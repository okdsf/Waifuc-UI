import os
import logging
import tempfile
import shutil
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

from .workflow import Workflow, WorkflowStep
from .execution_history import ExecutionRecord, history_manager
from src.tools.actions.action_registry import registry as action_registry
from src.tools.sources.source_registry import registry as source_registry
from src.tools.actions.waifuc_actions import WaifucActionWrapper
from waifuc.source import LocalSource

class WorkflowEngine:
    def __init__(self, max_workers: int = 1):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running_tasks = {}
        os.makedirs("logs", exist_ok=True)

    def execute_workflow(self, workflow: Workflow,
                       source_type: str, source_params: Dict[str, Any],
                       output_directory: str,
                       progress_callback: Callable[[str, float, str], None] = None) -> ExecutionRecord:
        record = history_manager.create_record(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            source_type=source_type,
            source_params=source_params,
            output_directory=output_directory
        )
        future = self.executor.submit(
            self._execute_workflow_internal,
            workflow, source_type, source_params, output_directory,
            record, progress_callback
        )
        self._running_tasks[record.id] = (future, record)
        return record

    def _execute_workflow_internal(self, workflow: Workflow,
                                  source_type: str, source_params: Dict[str, Any],
                                  output_directory: str, record: ExecutionRecord,
                                  progress_callback: Callable[[str, float, str], None] = None) -> None:
        def clean_metadata(directory):
            try:
                for filename in os.listdir(directory):
                    if filename.startswith('.') and filename.endswith('_meta.json'):
                        os.remove(os.path.join(directory, filename))
            except Exception as e:
                logger.warning(f"清理元数据失败: {str(e)}")

        try:
            os.makedirs(output_directory, exist_ok=True)
            temp_dir = tempfile.mkdtemp()
            temp_input_dir = os.path.join(temp_dir, 'input')
            os.makedirs(temp_input_dir, exist_ok=True)

            try:
                log_file = os.path.join("logs", f"{record.id}_log.txt")
                file_handler = logging.FileHandler(log_file, 'w', 'utf-8')
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                logger = logging.getLogger(f"workflow.{record.id}")
                logger.setLevel(logging.INFO)
                logger.addHandler(file_handler)

                if progress_callback:
                    progress_callback("获取图像", 0.0, "准备图像来源...")
                logger.info(f"开始执行工作流: {workflow.name}")
                logger.info(f"图像来源: {source_type}")
                logger.info(f"输出目录: {output_directory}")

                try:
                    source = source_registry.create_source(source_type, **source_params)
                    record.add_step_log("source", source_type, "started", "创建图像来源")
                    logger.info("从来源获取图像...")
                    if progress_callback:
                        progress_callback("获取图像", 0.1, "正在获取图像...")
                    if source_type == "LocalSource":
                        input_dir = source_params.get("directory", "")
                        if not os.path.exists(input_dir):
                            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
                        total_files = sum(1 for f in os.listdir(input_dir)
                                        if os.path.isfile(os.path.join(input_dir, f)) and
                                        f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')))
                        record.total_images = total_files
                        logger.info(f"发现 {total_files} 个图像文件")
                    else:
                        logger.info("开始下载图像...")
                        if progress_callback:
                            progress_callback("获取图像", 0.2, "下载图像...")
                        from waifuc.export import SaveExporter
                        source.source.export(SaveExporter(temp_input_dir))
                        total_files = sum(1 for f in os.listdir(temp_input_dir)
                                        if os.path.isfile(os.path.join(temp_input_dir, f)) and
                                        f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')))
                        record.total_images = total_files
                        logger.info(f"已下载 {total_files} 个图像文件")
                        input_dir = temp_input_dir
                    record.add_step_log("source", source_type, "completed",
                                        f"成功获取 {record.total_images} 个图像文件")
                except Exception as e:
                    error_msg = f"获取图像失败: {str(e)}"
                    logger.error(error_msg)
                    record.add_step_log("source", source_type, "failed", error_msg)
                    record.fail(error_msg)
                    if progress_callback:
                        progress_callback("错误", 0, error_msg)
                    return

                current_dir = input_dir
                success_count = 0
                failed_count = 0

                for i, step in enumerate(workflow.steps):
                    step_progress_base = 0.3 + (i / len(workflow.steps)) * 0.6
                    unique_id = uuid.uuid4().hex[:8]
                    step_output_dir = os.path.join(temp_dir, f"step_{i+1}_{unique_id}")
                    os.makedirs(step_output_dir, exist_ok=True)
                    logger.info(f"执行步骤 {i+1}/{len(workflow.steps)}: {step.action_name}")
                    logger.info(f"步骤 {i+1} 输入目录: {current_dir}")
                    logger.info(f"步骤 {i+1} 输出目录: {step_output_dir}")
                    record.add_step_log(step.id, step.action_name, "started",
                                       f"开始执行步骤 {i+1}/{len(workflow.steps)}")
                    if progress_callback:
                        progress_callback("处理图像", step_progress_base,
                                         f"执行步骤 {i+1}/{len(workflow.steps)}: {step.action_name}")
                    try:
                        action = action_registry.create_action(step.action_name, **step.params)
                        if isinstance(action, WaifucActionWrapper) and hasattr(action, 'action'):
                            action_instance = action.action
                        else:
                            action_instance = action

                        if step.action_name == "PreSortImagesAction":
                            for result in action_instance.iter(current_dir, step_output_dir):
                                if 'item' in result:
                                    item = result['item']
                                    ratio = item.meta.get('ratio', 'unknown')
                                    ratio_dir = os.path.join(step_output_dir, ratio.replace(':', '_'))
                                    os.makedirs(ratio_dir, exist_ok=True)
                                    unique_filename = f"{uuid.uuid4().hex[:8]}.png"
                                    output_path = os.path.join(ratio_dir, unique_filename)
                                    item.image.save(output_path, format='PNG')
                                elif 'counts' in result:
                                    logger.info(f"PreSortImagesAction 统计: {result['counts']}")

                        elif step.action_name == "EnhancedImageProcessAction":
                            for result in action_instance.iter(current_dir, step_output_dir):
                                if 'item' in result:
                                    item = result['item']
                                    ratio = item.meta.get('ratio', 'unknown')
                                    ratio_dir = os.path.join(step_output_dir, ratio.replace(':', '_'))
                                    os.makedirs(ratio_dir, exist_ok=True)
                                    unique_filename = f"{uuid.uuid4().hex[:8]}.png"
                                    output_path = os.path.join(ratio_dir, unique_filename)
                                    item.image.save(output_path, format='PNG')
                                elif 'results' in result:
                                    for ratio, info in result['results'].items():
                                        logger.info(f"{ratio} 图像: {info['count']} 张")

                        else:
                            source = LocalSource(current_dir)
                            processed = source.attach(action_instance)
                            from waifuc.export import SaveExporter
                            processed.export(SaveExporter(step_output_dir))
                            clean_metadata(step_output_dir)

                        output_files = [f for f in os.listdir(step_output_dir)
                                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'))]
                        if not output_files:
                            logger.warning(f"步骤 {step.action_name} 未生成任何图像")
                        record.add_step_log(step.id, step.action_name, "completed",
                                           f"步骤 {i+1}/{len(workflow.steps)} 成功完成，生成 {len(output_files)} 张图像")
                        if progress_callback:
                            progress_callback("处理图像", step_progress_base + 0.6/len(workflow.steps),
                                            f"步骤 {i+1}/{len(workflow.steps)} 完成")
                        current_dir = step_output_dir

                    except Exception as e:
                        error_msg = f"步骤 {i+1} ({step.action_name}) 执行失败: {str(e)}"
                        logger.error(error_msg)
                        record.add_step_log(step.id, step.action_name, "failed", error_msg)
                        failed_count += 1
                        if i == 0:
                            record.fail(error_msg)
                            if progress_callback:
                                progress_callback("错误", 0, error_msg)
                            return
                        current_dir = os.path.join(temp_dir, f"step_{i}")

                if workflow.steps:
                    output_files_count = 0
                    for root, dirs, files in os.walk(current_dir):
                        for filename in files:
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
                                base, ext = os.path.splitext(filename)
                                unique_filename = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
                                src_path = os.path.join(root, filename)
                                dst_path = os.path.join(output_directory, unique_filename)
                                try:
                                    shutil.copy2(src_path, dst_path)
                                    output_files_count += 1
                                except Exception as e:
                                    logger.error(f"复制最终文件失败: {src_path} -> {dst_path}, 错误: {str(e)}")
                    logger.info(f"已将 {output_files_count} 个文件复制到 {output_directory}")
                    clean_metadata(output_directory)

                success_count = record.total_images - failed_count
                record.complete(
                    total_images=record.total_images,
                    processed_images=record.total_images,
                    success_images=success_count,
                    failed_images=failed_count
                )
                history_manager.save_record(record)
                logger.info(f"工作流执行完成. 总图像: {record.total_images}, "
                          f"成功: {success_count}, 失败: {failed_count}")
                if progress_callback:
                    progress_callback("完成", 1.0,
                                    f"处理完成. 总图像: {record.total_images}, "
                                    f"成功: {success_count}, 失败: {failed_count}")

            finally:
                shutil.rmtree(temp_dir)
                file_handler.close()
                logger.removeHandler(file_handler)

        except Exception as e:
            error_msg = f"工作流执行出错: {str(e)}"
            logger.error(error_msg)
            record.fail(error_msg)
            history_manager.save_record(record)
            if progress_callback:
                progress_callback("错误", 0, error_msg)

        finally:
            if record.id in self._running_tasks:
                del self._running_tasks[record.id]

    def get_running_tasks(self) -> Dict[str, ExecutionRecord]:
        running_records = {}
        for task_id, (future, record) in list(self._running_tasks.items()):
            if future.done():
                del self._running_tasks[task_id]
            else:
                running_records[task_id] = record
        return running_records

    def cancel_task(self, task_id: str) -> bool:
        if task_id not in self._running_tasks:
            return False
        future, record = self._running_tasks[task_id]
        cancelled = future.cancel()
        if cancelled:
            record.fail("任务被取消")
            history_manager.save_record(record)
            del self._running_tasks[task_id]
        return cancelled

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

workflow_engine = WorkflowEngine()

def 简单执行工作流(工作流,
                输入目录=None,
                输出目录=None,
                源类型="LocalSource",
                进度回调=None,
                **其他参数):
    if 输入目录 is None:
        输入目录 = "./input"
    if 输出目录 is None:
        输出目录 = "./output"
    source_params = {}
    if 源类型 == "LocalSource":
        source_params["directory"] = 输入目录
    elif 源类型 == "PixivSource":
        if "tags" not in 其他参数:
            source_params["tags"] = []
        if "limit" not in 其他参数:
            source_params["limit"] = 100
    elif 源类型 == "WebSource":
        if "urls" not in 其他参数:
            source_params["urls"] = []
    source_params.update(其他参数)
    return workflow_engine.execute_workflow(
        workflow=工作流,
        source_type=源类型,
        source_params=source_params,
        output_directory=输出目录,
        progress_callback=进度回调
    )