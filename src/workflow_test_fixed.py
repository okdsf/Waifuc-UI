import gradio as gr
import json
import logging
import sys
import os

# 确保 action_registry 可导入
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from tools.actions.action_registry import registry as action_registry
except ImportError as e:
    print(f"Error importing action_registry: {e}")
    sys.exit(1)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render():
    with gr.Blocks() as app:
        gr.Markdown("### 动态参数输入测试")
        
        # 动作选择
        action_dropdown = gr.Dropdown(
            choices=[f"{cat} - {act}" for cat, acts in action_registry.get_all_actions().items() for act in acts],
            label="选择操作",
            value=None
        )
        
        # 使用 gr.State 存储 action_dropdown 的值
        action_state = gr.State(value=None)
        
        # 绑定 .change 事件，更新 action_state（移除 _js 参数）
        action_dropdown.change(
            fn=lambda x: x,
            inputs=action_dropdown,
            outputs=action_state
        )
        
        # 参数输入区域
        output = gr.Textbox(label="保存的参数", interactive=False)

        @gr.render(inputs=action_state)
        def render_params(action_str):
            logger.info(f"render_params called with action_str: {action_str}")
            if not action_str:
                gr.Markdown("请选择一个操作")
                return
            action_name = action_str.split(" - ")[-1]
            params = action_registry.get_action_params(action_name)
            logger.info(f"Generating inputs for action: {action_name}, params: {params}")
            
            with gr.Column():
                components = []
                param_names = []
                for param_name, default_value in params.items():
                    param_names.append(param_name)
                    if isinstance(default_value, bool):
                        component = gr.Checkbox(
                            label=param_name,
                            value=default_value if default_value is not None else False
                        )
                    elif isinstance(default_value, (int, float)):
                        component = gr.Number(
                            label=param_name,
                            value=default_value if default_value is not None else 0,
                            precision=0 if isinstance(default_value, int) else None
                        )
                    else:
                        placeholder = f"必填：{param_name}" if default_value is None else ""
                        component = gr.Textbox(
                            label=param_name,
                            value=str(default_value) if default_value is not None else "",
                            placeholder=placeholder
                        )
                    components.append(component)
                
                add_btn = gr.Button("添加")
                
                def add_params(*param_values):
                    if not action_str:
                        return "请选择操作"
                    param_dict = {}
                    try:
                        if len(param_values) != len(param_names):
                            raise ValueError(f"参数数量不匹配：预期 {len(param_names)}，实际 {len(param_values)}")
                        for i, param_name in enumerate(param_names):
                            value = param_values[i]
                            default_value = params[param_name]
                            if default_value is None and (value is None or value == ""):
                                raise ValueError(f"请输入必填参数：{param_name}")
                            param_dict[param_name] = value
                        logger.info(f"Saved params for action: {action_name}, params: {param_dict}")
                        return json.dumps(param_dict, indent=2)
                    except ValueError as e:
                        logger.error(f"Add params error: {str(e)}")
                        return str(e)
                
                add_btn.click(
                    fn=add_params,
                    inputs=components,
                    outputs=output
                )

    return app

if __name__ == "__main__":
    render().launch(share=False)