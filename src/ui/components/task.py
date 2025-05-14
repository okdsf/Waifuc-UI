import gradio as gr
import asyncio
import logging
import re
import pandas as pd # 如果完全删除了 step_states 和 results，并且没有其他地方用 pd，可以考虑删除此导入
from src.services.workflow_service import WorkflowService
from src.services.task_service import TaskService, TaskError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render(source_data):
    task_id = gr.State(None)
    with gr.Column():
        workflow_dropdown = gr.Dropdown(
            choices=[(w["name"], w["id"]) for w in WorkflowService.get_all_workflows()] or [("无工作流", "")],
            label="选择工作流"
        )
        output_dir = gr.Textbox(label="输出目录", placeholder="请输入输出目录")
        with gr.Row():
            start_btn = gr.Button("开始任务")
            stop_btn = gr.Button("停止任务")
            open_dir_btn = gr.Button("打开输出目录")
        gr.Markdown("### 任务进度")
        progress_bar = gr.Slider(minimum=0, maximum=100, label="进度", interactive=False)
        log_output = gr.Textbox(label="任务日志", interactive=False, lines=10)
        # results_table = gr.Dataframe(value=[], headers=["步骤", "状态", "详情"], datatype=["str", "str", "str"], interactive=False) # <-- 已删除

        async def start_task(workflow_id, source_data, output_dir):
            try:
                if not workflow_id or not source_data or not output_dir:
                    # yield "请先选择工作流、数据源和输出目录", 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), None # <-- 修改前
                    yield "请先选择工作流、数据源和输出目录", 0.0, gr.update(visible=True), None # <-- 修改后
                    return
                
                task_id_value = TaskService.start_task(workflow_id, source_data, output_dir)
                logger.info(f"Task started: {task_id_value}")
                
                last_log = "" # 跟踪最新的日志内容

                while True:
                    status, progress, message, is_finished = TaskService.get_progress(task_id_value)
                    progress_percent = progress * 100
                    current_log = message.strip()

                    # 日志解析逻辑可以保留，因为它可能影响 current_log 的内容，
                    # 或者你将来可能想基于此做其他事情。
                    # 但 step_states 和 results 的生成及更新被移除。
                    if current_log and current_log != last_log:
                        last_log = current_log
                        # (可选) 如果日志解析只为了 step_states，这部分也可以简化或移除
                        match_step = re.match(r"执行步骤 (\d+)/(\d+): (.+)", current_log)
                        if match_step:
                            pass # 原本这里更新 step_states
                        match_complete = re.match(r"处理完成\. 总图像: (\d+), 成功: (\d+), 失败: (\d+)", current_log)
                        if match_complete:
                            pass # 原本这里更新 step_states
                        if current_log == "终止信号已发送，需等待当前工作流步骤完成":
                            pass # 原本这里更新 step_states
                        if current_log == "任务已终止":
                            pass # 原本这里更新 step_states

                    # results = pd.DataFrame(...) # <-- 已删除

                    # yield ( # <-- 修改前
                    #     current_log,
                    #     progress_percent,
                    #     results,
                    #     gr.update(visible=not is_finished),
                    #     task_id_value
                    # )
                    yield ( # <-- 修改后
                        current_log,
                        progress_percent,
                        gr.update(visible=not is_finished),
                        task_id_value
                    )
                    
                    if is_finished:
                        if status == "取消":
                            # yield ("任务已终止", 0.0, results, gr.update(visible=False), None) # <-- 修改前
                            yield ("任务已终止", 0.0, gr.update(visible=False), None) # <-- 修改后
                        TaskService.clear_progress(task_id_value)
                        logger.info(f"Task finished: {task_id_value}, status: {status}")
                        break
                    
                    await asyncio.sleep(0.1)
            
            except TaskError as e:
                logger.error(f"Start task error: {str(e)}")
                # yield str(e), 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), None # <-- 修改前
                yield str(e), 0.0, gr.update(visible=True), None # <-- 修改后

        # start_btn.click(fn=start_task, inputs=[workflow_dropdown, source_data, output_dir], outputs=[log_output, progress_bar, results_table, stop_btn, task_id]) # <-- 修改前
        start_btn.click(fn=start_task, inputs=[workflow_dropdown, source_data, output_dir], outputs=[log_output, progress_bar, stop_btn, task_id]) # <-- 修改后

        def stop_task(task_id_val): # Renamed task_id to task_id_val to avoid conflict with gr.State
            try:
                message = TaskService.stop_task(task_id_val)
                # return message, 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), task_id_val # <-- 修改前
                return message, 0.0, gr.update(visible=True), task_id_val # <-- 修改后
            except TaskError as e:
                logger.error(f"Stop task error: {str(e)}")
                # return str(e), 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), None # <-- 修改前
                return str(e), 0.0, gr.update(visible=True), None # <-- 修改后

        # stop_btn.click(fn=stop_task, inputs=task_id, outputs=[log_output, progress_bar, results_table, stop_btn, task_id]) # <-- 修改前
        stop_btn.click(fn=stop_task, inputs=task_id, outputs=[log_output, progress_bar, stop_btn, task_id]) # <-- 修改后

        def open_output_directory(output_dir_val): # Renamed output_dir to avoid conflict
            try:
                TaskService.open_output_directory(output_dir_val)
                logger.info(f"Opened output directory: {output_dir_val}")
                return "已打开输出目录"
            except TaskError as e:
                logger.error(f"Open directory error: {str(e)}")
                return str(e)

        open_dir_btn.click(fn=open_output_directory, inputs=output_dir, outputs=log_output)

    return task_id