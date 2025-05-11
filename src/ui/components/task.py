"""
任务执行组件：选择工作流、数据源、输出目录，启动/停止任务，显示实时进度和日志，打开输出目录。
对应 PyQt5 的 task_execution.py。
"""
import gradio as gr
from src.services.workflow_service import WorkflowService
from src.services.task_service import TaskService, TaskError
from src.services.config_service import ConfigService

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
            value=ConfigService.get_output_directory() or "",
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

        # 启动任务
        def start_task(workflow_id, source_data, output_dir):
            try:
                if not workflow_id or not source_data or not output_dir:
                    return "请先选择工作流、数据源和输出目录", 0.0, [], gr.update(visible=True), None
                task_id_value = TaskService.start_task(workflow_id, source_data, output_dir)
                return (
                    f"任务 {task_id_value} 已启动",
                    100.0,  # 模拟完成
                    [["示例步骤", "完成", "详情"]],  # 模拟结果
                    gr.update(visible=False),
                    task_id_value
                )
            except TaskError as e:
                return str(e), 0.0, [], gr.update(visible=True), None

        start_btn.click(
            fn=start_task,
            inputs=[workflow_dropdown, source_data, output_dir],
            outputs=[log_output, progress_bar, results_table, stop_btn, task_id]
        )

        # 停止任务
        def stop_task(task_id):
            try:
                if not task_id:
                    raise TaskError("没有运行中的任务")
                TaskService.stop_task(task_id)
                return "任务已停止", 0.0, [], gr.update(visible=False), None
            except TaskError as e:
                return str(e), 0.0, [], gr.update(visible=True), None

        stop_btn.click(
            fn=stop_task,
            inputs=task_id,
            outputs=[log_output, progress_bar, results_table, stop_btn, task_id]
        )

        # 打开输出目录
        def open_output_directory(output_dir):
            try:
                TaskService.open_output_directory(output_dir)
                return "已打开输出目录"
            except TaskError as e:
                return str(e)

        open_dir_btn.click(
            fn=open_output_directory,
            inputs=output_dir,
            outputs=log_output
        )