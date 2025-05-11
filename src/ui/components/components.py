"""
组件说明组件：显示可用操作类型及其参数说明，支持搜索和分类查看。
对应 PyQt5 的 component_explorer.py。
"""
import gradio as gr
import json
from src.tools.actions.action_registry import registry as action_registry

def render():
    """
    渲染组件说明界面，按类别显示操作及其参数，支持搜索。
    """
    with gr.Column():
        # 调试 action_registry 数据
        categories = action_registry.get_categories() or ["默认类别"]
        print("Action categories:", categories)
        default_category = categories[0]
        print("Actions in default category:", action_registry.get_actions_in_category(default_category))

        category_dropdown = gr.Dropdown(
            choices=categories,
            label="选择类别",
            value=default_category
        )
        search_input = gr.Textbox(label="搜索操作", placeholder="输入关键字")
        action_table = gr.Dataframe(
            value=[["无操作", "无参数"]],
            headers=["操作", "参数"],
            datatype=["str", "str"],
            interactive=False
        )

        # 更新操作表格
        def update_actions(category, search):
            try:
                if not category:
                    return [["无操作", "无参数"]]
                actions = action_registry.get_actions_in_category(category) or []
                print("Actions for category", category, ":", actions)
                if search:
                    actions = [a for a in actions if search.lower() in a.lower()]
                rows = []
                for action in actions:
                    params = action_registry.get_action_params(action) or {}
                    print("Params for action", action, ":", params)
                    # 使用 default=str 处理非序列化对象
                    rows.append([action, json.dumps(params, indent=2, default=str)])
                return rows or [["无操作", "无参数"]]
            except Exception as e:
                print("Error in update_actions:", str(e))
                return [["错误", str(e)]]

        category_dropdown.change(
            fn=update_actions,
            inputs=[category_dropdown, search_input],
            outputs=action_table
        )
        search_input.change(
            fn=update_actions,
            inputs=[category_dropdown, search_input],
            outputs=action_table
        )