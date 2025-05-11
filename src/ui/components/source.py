"""
数据源选择组件：选择数据源类型，配置参数，验证并保存，加载历史数据源。
对应 PyQt5 的 source_selector.py。
"""
import gradio as gr
import json
from src.services.source_service import SourceService, SourceError
from typing import Dict

def render():
    """
    渲染数据源选择界面，使用 gr.Accordion 布局
    """
    source_data = gr.State(None)
    with gr.Column():
        # 初始数据框数据
        saved_sources_data = SourceService.get_saved_sources() or []
        saved_sources_rows = [[s["type"], json.dumps(s["params"])] for s in saved_sources_data]

        # 定义 saved_sources 数据框
        saved_sources = gr.Dataframe(
            value=saved_sources_rows,
            headers=["类型", "参数"],
            datatype=["str", "str"],
            interactive=True
        )

        with gr.Accordion("新建数据源", open=True):
            source_type = gr.Dropdown(
                choices=SourceService.get_source_types(),
                label="源类型"
            )
            directory = gr.Textbox(label="本地目录", visible=False)
            tags = gr.Textbox(label="标签", placeholder="输入标签，用空格分隔", visible=False)
            limit = gr.Number(label="下载数量", value=100, visible=False)
            select_btn = gr.Button("选择数据源")
            source_output = gr.Textbox(label="选择结果")

            def update_params(source_type):
                is_local = source_type == "LocalSource"
                return (
                    gr.update(visible=is_local),
                    gr.update(visible=not is_local),
                    gr.update(visible=not is_local)
                )

            source_type.change(
                fn=update_params,
                inputs=source_type,
                outputs=[directory, tags, limit]
            )

            def select_source(source_type, directory, tags, limit):
                try:
                    if not source_type:
                        raise SourceError("请选择数据源类型")
                    params = {}
                    if source_type == "LocalSource":
                        params["directory"] = directory
                    else:
                        params["tags"] = tags.split() if tags else []
                        params["limit"] = int(limit)
                    SourceService.validate_source(source_type, params)
                    source_data_value = {"type": source_type, "params": params}
                    SourceService.save_source(source_data_value)
                    saved = SourceService.get_saved_sources() or []
                    saved_rows = [[s["type"], json.dumps(s["params"])] for s in saved]
                    return source_data_value, f"已选择数据源: {source_type}", saved_rows
                except SourceError as e:
                    return None, str(e), gr.update()

            select_btn.click(
                fn=select_source,
                inputs=[source_type, directory, tags, limit],
                outputs=[source_data, source_output, saved_sources]
            )

        with gr.Accordion("保存的数据源", open=False):
            # 使用相同的 saved_sources 数据框
            saved_sources_display = gr.Dataframe(
                value=saved_sources_rows,
                headers=["类型", "参数"],
                datatype=["str", "str"],
                interactive=True
            )
            load_saved_btn = gr.Button("加载选中数据源")
            load_output = gr.Textbox(label="加载结果")

            def load_saved_source(selected_row):
                try:
                    if not selected_row:
                        raise SourceError("请先选择数据源")
                    source_type, params_json = selected_row[0]
                    params = json.loads(params_json)
                    source_data_value = {"type": source_type, "params": params}
                    return source_data_value, f"已加载数据源: {source_type}"
                except SourceError as e:
                    return None, str(e)

            load_saved_btn.click(
                fn=load_saved_source,
                inputs=saved_sources_display,
                outputs=[source_data, load_output]
            )

    return source_data