"""
历史记录组件：显示任务记录，查看详情，删除记录，清理记录，打开输出目录。
对应 PyQt5 的 history_view.py。
"""
import gradio as gr
import json
from src.services.history_service import HistoryService, HistoryError

def render():
    """
    渲染历史记录界面，包含记录表格、详情查看、删除和清理功能。
    """
    with gr.Column():
        with gr.Row():
            refresh_btn = gr.Button("刷新")
            clear_dropdown = gr.Dropdown(
                choices=["所有记录", "一周前", "一个月前"], label="清理范围"
            )
            clear_btn = gr.Button("清理记录")
        history_table = gr.Dataframe(
            value=[],
            headers=["ID", "工作流", "开始时间", "状态", "图像数"],
            datatype=["str", "str", "str", "str", "number"],
            interactive=True
        )
        selected_record_index = gr.State(None)
        view_detail_btn = gr.Button("查看详情")
        open_dir_btn = gr.Button("打开输出目录")
        detail_output = gr.Textbox(label="记录详情", interactive=False, lines=10)

        # 刷新记录
        def refresh_records():
            try:
                records = HistoryService.get_all_records() or []
                return [[r["id"], r["workflow_name"], r["start_time"], r["status"], r["total_images"]]
                        for r in records]
            except HistoryError as e:
                return str(e)

        refresh_btn.click(fn=refresh_records, outputs=history_table)

        # 选择记录
        def select_record(history_table_value):
            if not history_table_value:
                return None, "请先刷新记录"
            return 0, "已选择第一个记录"  # 默认选择第一行

        view_detail_btn.click(
            fn=select_record,
            inputs=history_table,
            outputs=[selected_record_index, detail_output]
        )

        # 查看详情
        def view_detail(selected_index, history_table_value):
            try:
                if selected_index is None or not history_table_value:
                    return "请先选择记录"
                record_id = history_table_value[selected_index][0]
                record = HistoryService.get_record(record_id)
                return json.dumps(record, indent=2) if record else "记录不存在"
            except HistoryError as e:
                return str(e)

        view_detail_btn.click(
            fn=view_detail,
            inputs=[selected_record_index, history_table],
            outputs=detail_output
        )

        # 打开输出目录
        def open_output_directory(selected_index, history_table_value):
            try:
                if selected_index is None or not history_table_value:
                    raise HistoryError("请先选择记录")
                record_id = history_table_value[selected_index][0]
                record = HistoryService.get_record(record_id)
                if not record or not record.get("output_directory"):
                    raise HistoryError("记录无输出目录")
                HistoryService.open_output_directory(record["output_directory"])
                return "已打开输出目录"
            except HistoryError as e:
                return str(e)

        open_dir_btn.click(
            fn=open_output_directory,
            inputs=[selected_record_index, history_table],
            outputs=detail_output
        )

        # 清理记录
        def clear_records(clear_option):
            try:
                days = None
                if clear_option == "一周前":
                    days = 7
                elif clear_option == "一个月前":
                    days = 30
                count = HistoryService.clear_records(days)
                return f"已清理 {count} 条记录", [], None
            except HistoryError as e:
                return str(e), gr.update(), gr.update()

        clear_btn.click(
            fn=clear_records,
            inputs=clear_dropdown,
            outputs=[detail_output, history_table, selected_record_index]
        )