"""
任务执行组件：选择工作流、数据源、输出目录，启动/停止任务，显示实时进度和日志，打开输出目录。
对应 PyQt5 的 task_execution.py。
"""
import gradio as gr
import asyncio
import logging
from src.services.workflow_service import WorkflowService
from src.services.task_service import TaskService, TaskError

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render(source_data):
    """
    渲染任务执行界面，包含工作流选择、任务控制、进度和日志显示。
    """
    task_id = gr.State(None)
    with gr.Column():
        workflow_dropdown = gr.Dropdown(
            choices=[(w["name"], w["id"]) for w in WorkflowService.get_all_workflows()] or [("无工作流", "")],
            label="选择工作流"
        )
        output_dir = gr.Textbox(
            label="输出目录",
            placeholder="请输入输出目录"
        )
        with gr.Row():
            start_btn = gr.Button("开始任务")
            stop_btn = gr.Button("停止任务")
            open_dir_btn = gr.Button("打开输出目录")
        gr.Markdown("### 任务进度")
        progress_bar = gr.Slider(minimum=0, maximum=100, label="进度", interactive=False)
        log_output = gr.Textbox(label="任务日志", interactive=False, lines=10)
        results_table = gr.Dataframe(
            value=[],
            headers=["步骤", "状态", "详情"],
            datatype=["str", "str", "str"],
            interactive=False
        )

        async def start_task(workflow_id, source_data, output_dir):
            """
            启动任务，异步轮询进度并更新界面。
            
            Args:
                workflow_id: 工作流 ID
                source_data: 数据源配置
                output_dir: 输出目录
                
            Yields:
                更新后的日志、进度条、结果表格、停止按钮可见性、任务 ID
            """
            try:
                if not workflow_id or not source_data or not output_dir:
                    yield "请先选择工作流、数据源和输出目录", 0.0, [], gr.update(visible=True), None
                    return
                
                task_id_value = TaskService.start_task(workflow_id, source_data, output_dir)
                logger.info(f"Task started: {task_id_value}")
                
                status, progress, message, is_finished = TaskService.get_progress(task_id_value)
                progress_percent = progress * 100
                results = [[f"步骤 {i+1}", status, message] for i in range(len(message.splitlines()) or 1)]
                yield (
                    message,
                    progress_percent,
                    results,
                    gr.update(visible=not is_finished),
                    task_id_value
                )
                
                while not is_finished:
                    status, progress, message, is_finished = TaskService.get_progress(task_id_value)
                    progress_percent = progress * 100
                    results = [[f"步骤 {i+1}", status, message] for i in range(len(message.splitlines()) or 1)]
                    
                    yield (
                        message,
                        progress_percent,
                        results,
                        gr.update(visible=not is_finished),
                        task_id_value
                    )
                    
                    if is_finished:
                        if status == "取消":
                            yield (
                                "任务已终止",
                                0.0,
                                results,
                                gr.update(visible=False),
                                None
                            )
                        TaskService.clear_progress(task_id_value)
                        logger.info(f"Task finished: {task_id_value}, status: {status}")
                        break
                    
                    await asyncio.sleep(0.1)
            
            except TaskError as e:
                logger.error(f"Start task error: {str(e)}")
                yield str(e), 0.0, [], gr.update(visible=True), None

        start_btn.click(
            fn=start_task,
            inputs=[workflow_dropdown, source_data, output_dir],
            outputs=[log_output, progress_bar, results_table, stop_btn, task_id]
        )

        def stop_task(task_id):
            """
            停止任务，返回取消提示。
            
            Args:
                task_id: 任务 ID
                
            Returns:
                日志、进度条、结果表格、停止按钮可见性、任务 ID
            """
            try:
                message = TaskService.stop_task(task_id)
                return message, 0.0, [], gr.update(visible=True), task_id  # 保持 task_id 等待取消完成
            except TaskError as e:
                logger.error(f"Stop task error: {str(e)}")
                return str(e), 0.0, [], gr.update(visible=True), None

        stop_btn.click(
            fn=stop_task,
            inputs=task_id,
            outputs=[log_output, progress_bar, results_table, stop_btn, task_id]
        )

        def open_output_directory(output_dir):
            """
            打开输出目录。
            
            Args:
                output_dir: 输出目录路径
                
            Returns:
                操作结果消息
            """
            try:
                TaskService.open_output_directory(output_dir)
                logger.info(f"Opened output directory: {output_dir}")
                return "已打开输出目录"
            except TaskError as e:
                logger.error(f"Open directory error: {str(e)}")
                return str(e)

        open_dir_btn.click(
            fn=open_output_directory,
            inputs=output_dir,
            outputs=log_output
        )

    return task_id