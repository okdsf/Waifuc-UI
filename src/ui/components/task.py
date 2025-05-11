import gradio as gr
import asyncio
import logging
import re
import pandas as pd
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
        results_table = gr.Dataframe(value=[], headers=["步骤", "状态", "详情"], datatype=["str", "str", "str"], interactive=False)

        async def start_task(workflow_id, source_data, output_dir):
            try:
                if not workflow_id or not source_data or not output_dir:
                    yield "请先选择工作流、数据源和输出目录", 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), None
                    return
                
                task_id_value = TaskService.start_task(workflow_id, source_data, output_dir)
                logger.info(f"Task started: {task_id_value}")
                
                # 初始化状态
                step_states = {}
                total_steps = 1  # 默认值，稍后从日志动态更新
                last_log = ""  # 跟踪最新的日志内容

                while True:
                    status, progress, message, is_finished = TaskService.get_progress(task_id_value)
                    progress_percent = progress * 100

                    # 使用 message 作为 log_output 的内容（假设 message 直接输出到 log_output）
                    current_log = message.strip()

                    # 只在日志有更新时解析
                    if current_log and current_log != last_log:
                        last_log = current_log

                        # 解析日志：执行步骤
                        match_step = re.match(r"执行步骤 (\d+)/(\d+): (.+)", current_log)
                        if match_step:
                            current_step, total, action_name = match_step.groups()
                            total_steps = int(total)
                            current_step = int(current_step)

                            # 初始化所有步骤（仅在第一次匹配时）
                            if not step_states:
                                step_states = {
                                    f"步骤 {i+1}/{total_steps}": {"status": "未开始", "message": "等待执行"}
                                    for i in range(total_steps)
                                }

                            # 更新状态：前 N-1 步完成，当前步骤处理中，后续步骤未开始
                            for step_id in step_states:
                                step_num = int(step_id.split('/')[0].split()[1])
                                if step_num < current_step:
                                    step_states[step_id] = {"status": "完成", "message": "步骤执行完成"}
                                elif step_num == current_step:
                                    step_states[step_id] = {"status": "处理中", "message": f"{action_name} 执行中"}
                                else:
                                    step_states[step_id] = {"status": "未开始", "message": "等待执行"}

                        # 解析日志：任务完成
                        match_complete = re.match(r"处理完成\. 总图像: (\d+), 成功: (\d+), 失败: (\d+)", current_log)
                        if match_complete:
                            for step_id in step_states:
                                step_states[step_id] = {"status": "完成", "message": "步骤执行完成"}

                        # 解析日志：终止信号
                        if current_log == "终止信号已发送，需等待当前工作流步骤完成":
                            for step_id in step_states:
                                if step_states[step_id]["status"] == "处理中":
                                    step_states[step_id] = {"status": "取消中", "message": "等待当前步骤终止"}
                                elif step_states[step_id]["status"] == "未开始":
                                    step_states[step_id] = {"status": "未执行", "message": "任务被终止"}

                        # 解析日志：任务已终止
                        if current_log == "任务已终止":
                            for step_id in step_states:
                                if step_states[step_id]["status"] in ["处理中", "取消中"]:
                                    step_states[step_id] = {"status": "失败", "message": "任务被取消"}
                                elif step_states[step_id]["status"] == "未开始":
                                    step_states[step_id] = {"status": "未执行", "message": "任务被取消"}

                    # 生成 results_table 数据
                    results = pd.DataFrame([
                        [step_id, step_states[step_id]["status"], step_states[step_id]["message"]]
                        for step_id in step_states
                    ], columns=["步骤", "状态", "详情"]) if step_states else pd.DataFrame(columns=["步骤", "状态", "详情"])

                    yield (
                        current_log,
                        progress_percent,
                        results,
                        gr.update(visible=not is_finished),
                        task_id_value
                    )
                    
                    if is_finished:
                        if status == "取消":
                            yield ("任务已终止", 0.0, results, gr.update(visible=False), None)
                        TaskService.clear_progress(task_id_value)
                        logger.info(f"Task finished: {task_id_value}, status: {status}")
                        break
                    
                    await asyncio.sleep(0.1)
            
            except TaskError as e:
                logger.error(f"Start task error: {str(e)}")
                yield str(e), 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), None

        start_btn.click(fn=start_task, inputs=[workflow_dropdown, source_data, output_dir], outputs=[log_output, progress_bar, results_table, stop_btn, task_id])

        def stop_task(task_id):
            try:
                message = TaskService.stop_task(task_id)
                return message, 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), task_id
            except TaskError as e:
                logger.error(f"Stop task error: {str(e)}")
                return str(e), 0.0, pd.DataFrame(columns=["步骤", "状态", "详情"]), gr.update(visible=True), None

        stop_btn.click(fn=stop_task, inputs=task_id, outputs=[log_output, progress_bar, results_table, stop_btn, task_id])

        def open_output_directory(output_dir):
            try:
                TaskService.open_output_directory(output_dir)
                logger.info(f"Opened output directory: {output_dir}")
                return "已打开输出目录"
            except TaskError as e:
                logger.error(f"Open directory error: {str(e)}")
                return str(e)

        open_dir_btn.click(fn=open_output_directory, inputs=output_dir, outputs=log_output)

    return task_id