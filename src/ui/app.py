"""
Gradio 主应用：整合工作流设计、数据源选择、任务执行、历史记录、设置、组件说明。
包含插图、自定义 CSS 和状态栏。
"""
import gradio as gr
from src.ui.components import workflow, source, task, history, settings, components

# 自定义 CSS
custom_css = """
.gradio-container { background-color: #f0f4f8; }
button { border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); }
input, textarea { border-radius: 5px; }
.output-text { font-family: 'Arial', sans-serif; }
.status-bar { background-color: #e6f0ff; padding: 10px; border-radius: 5px; }
"""

# 主界面
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css=custom_css) as app:
    # 插图
    gr.HTML("""
        <img src='./ui/components/assets/logo.png' style='width: 150px; display: block; margin: 20px auto; 
               border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); 
               transition: transform 0.3s;'>
        <style>
            img:hover { transform: scale(1.1); }
        </style>
    """)
    
    # 标题
    gr.Markdown("# 图像处理工具")

    # 菜单
    with gr.Row():
        menu = gr.Dropdown(
            choices=["文件 - 新建工作流", "文件 - 打开工作流", "文件 - 保存工作流",
                     "文件 - 导入工作流", "文件 - 导出工作流", "文件 - 退出",
                     "工具 - 运行任务", "工具 - 停止任务", "工具 - 设置",
                     "帮助 - 关于", "帮助 - 文档"],
            label="菜单"
        )
        menu_output = gr.Textbox(label="菜单操作结果", interactive=False)

    # 选项卡
    with gr.Tabs():
        with gr.Tab("工作流设计"):
            workflow.render()
        with gr.Tab("数据源选择"):
            source_data = source.render()  # 渲染数据源选择界面
        with gr.Tab("任务执行"):
            task.render(source_data)
        with gr.Tab("历史记录"):
            history.render()
        with gr.Tab("设置"):
            settings.render()
        with gr.Tab("组件说明"):
            components.render()


    # 状态栏
    status_bar = gr.Textbox(label="状态", value="就绪", interactive=False, elem_classes="status-bar")

    # 菜单操作
    def handle_menu(menu_option):
        if menu_option == "文件 - 退出":
            return "退出程序（Gradio 需手动关闭）", "退出"
        elif menu_option == "帮助 - 关于":
            return "图像处理工具 v1.0\n© 2025 版权所有", "关于"
        elif menu_option == "帮助 - 文档":
            return "帮助文档尚未实现，敬请期待", "帮助"
        else:
            return f"执行: {menu_option}", menu_option.split(" - ")[1]

    menu.change(
        fn=handle_menu,
        inputs=menu,
        outputs=[menu_output, status_bar]
    )

# 启动
if __name__ == "__main__":
    app.launch(debug=True)  # 启用调试模式