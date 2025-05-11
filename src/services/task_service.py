"""
任务服务：包装 src/data/workflow_engine.py，提供任务执行功能，
通过内存存储进度更新，返回任务 ID，供 Gradio 前端使用。
"""
from src.data import workflow_manager
from src.data.workflow_engine import workflow_engine
from typing import Dict, List, Tuple
import logging
import threading

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskError(Exception):
    pass

class TaskService:
    progress_data = {}
    _lock = threading.Lock()

    @classmethod
    def start_task(cls, workflow_id: str, source_data: Dict, output_dir: str) -> str:
        """
        启动任务，返回任务 ID，进度信息存储到 progress_data。
        
        Args:
            workflow_id: 工作流 ID
            source_data: 数据源配置
            output_dir: 输出目录
            
        Returns:
            任务 ID
        """
        try:
            workflow = workflow_manager.get_workflow(workflow_id)
            if not workflow:
                raise TaskError("工作流不存在")
            source_type = source_data.get("type")
            source_params = source_data.get("params", {})
            if not source_type:
                raise TaskError("数据源类型不能为空")
            
            task_id = None
            def progress_callback(status: str, progress: float, message: str):
                nonlocal task_id
                with cls._lock:
                    if task_id is None:
                        cls.progress_data[task_id] = []
                    cls.progress_data[task_id].append((status, progress, message))
                logger.info(f"Task {task_id} progress: {status}, {progress:.2f}, {message}")
            
            record = workflow_engine.execute_workflow(
                workflow, source_type, source_params, output_dir, progress_callback
            )
            task_id = record.id
            with cls._lock:
                if task_id not in cls.progress_data:
                    cls.progress_data[task_id] = [("未开始", 0.0, "任务已启动")]
            logger.info(f"Started task: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Start task failed: {str(e)}")
            raise TaskError(f"启动任务失败: {str(e)}")

    @classmethod
    def get_progress(cls, task_id: str) -> Tuple[str, float, str, bool]:
        """
        获取任务的最新进度。
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Tuple[str, float, str, bool]: 状态、进度、消息、是否完成
        """
        with cls._lock:
            if task_id not in cls.progress_data or not cls.progress_data[task_id]:
                return "未开始", 0.0, "等待任务启动", False
        
            status, progress, message = cls.progress_data[task_id][-1]
            is_finished = status in ["完成", "错误", "取消"]  # 新增“取消”
            return status, progress, message, is_finished

    @classmethod
    def clear_progress(cls, task_id: str) -> None:
        """
        清理指定任务的进度数据。
        
        Args:
            task_id: 任务 ID
        """
        with cls._lock:
            if task_id in cls.progress_data:
                del cls.progress_data[task_id]
                logger.info(f"Cleared progress data for task: {task_id}")

    @classmethod
    def stop_task(cls, task_id: str) -> str:
        """
        停止任务，记录取消提示。
        
        Args:
            task_id: 任务 ID
            
        Returns:
            停止结果消息
        """
        try:
            if not task_id:
                raise TaskError("没有运行中的任务")
            with cls._lock:
                if task_id in cls.progress_data:
                    cls.progress_data[task_id].append((
                        "等待取消",
                        0.0,
                        "终止信号已发送，需等待当前工作流步骤完成"
                    ))
            success = workflow_engine.cancel_task(task_id)
            if success:
                logger.info(f"Stopped task: {task_id}")
                return "终止信号已发送，任务将在当前步骤完成后停止"
            else:
                logger.warning(f"Failed to stop task: {task_id}")
                return "无法停止任务，可能已完成或不存在"
        except TaskError as e:
            logger.error(f"Stop task error: {str(e)}")
            return str(e)

    @classmethod
    def open_output_directory(cls, output_dir: str) -> None:
        """
        打开输出目录。
        
        Args:
            output_dir: 输出目录路径
        """
        import os
        import platform
        try:
            if not os.path.exists(output_dir):
                raise TaskError(f"输出目录不存在: {output_dir}")
            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":
                os.system(f"open {output_dir}")
            else:
                os.system(f"xdg-open {output_dir}")
        except Exception as e:
            raise TaskError(f"打开输出目录失败: {str(e)}")