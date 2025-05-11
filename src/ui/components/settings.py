"""
设置组件：配置通用设置、处理设置、数据源设置。
对应 PyQt5 的 settings_dialog.py。
"""
import gradio as gr
from src.services.config_service import ConfigService, ConfigError

def render():
    """
    渲染设置界面，包含通用、处理、数据源设置。
    """
    with gr.Tabs():
        with gr.Tab("通用设置"):
            output_dir = gr.Textbox(label="默认输出目录", value=ConfigService.get_output_directory())
            temp_dir = gr.Textbox(label="临时目录", placeholder="留空使用系统默认")
            log_level = gr.Dropdown(
                choices=["DEBUG", "INFO", "WARNING", "ERROR"], label="日志级别",
                value=ConfigService.get_log_level()
            )
            theme = gr.Dropdown(choices=["light", "dark"], label="主题", value="light")
            language = gr.Dropdown(choices=["zh_CN", "en_US"], label="语言", value="zh_CN")
            tooltips = gr.Checkbox(label="显示工具提示", value=True)

        with gr.Tab("处理设置"):
            prefix = gr.Textbox(label="默认输出前缀", value="output")
            size_1_1 = gr.Number(label="正方形 (1:1) 最小尺寸", value=1024)
            size_2_3 = gr.Number(label="纵向 (2:3) 最小尺寸", value=960)
            size_3_2 = gr.Number(label="横向 (3:2) 最小尺寸", value=960)

        with gr.Tab("数据源设置"):
            danbooru_limit = gr.Number(label="Danbooru 默认下载数量", value=100)
            sankaku_username = gr.Textbox(label="Sankaku 用户名")
            sankaku_password = gr.Textbox(label="Sankaku 密码", type="password")
            sankaku_limit = gr.Number(label="Sankaku 默认下载数量", value=100)
            pixiv_username = gr.Textbox(label="Pixiv 用户名")
            pixiv_password = gr.Textbox(label="Pixiv 密码", type="password")
            pixiv_limit = gr.Number(label="Pixiv 默认下载数量", value=100)

        save_btn = gr.Button("保存设置")
        settings_output = gr.Textbox(label="设置结果")

        # 保存设置
        def save_settings(
            output_dir, temp_dir, log_level, theme, language, tooltips,
            prefix, size_1_1, size_2_3, size_3_2,
            danbooru_limit, sankaku_username, sankaku_password, sankaku_limit,
            pixiv_username, pixiv_password, pixiv_limit
        ):
            try:
                ConfigService.set_output_directory(output_dir)
                ConfigService.set_temp_directory(temp_dir)
                ConfigService.set_log_level(log_level)
                ConfigService.set("ui.theme", theme)
                ConfigService.set("ui.language", language)
                ConfigService.set("ui.show_tooltips", tooltips)
                ConfigService.set("processing.default_prefix", prefix)
                ConfigService.set("processing.default_sizes", {
                    "1:1": size_1_1,
                    "2:3": size_2_3,
                    "3:2": size_3_2
                })
                ConfigService.set("sources.danbooru.default_limit", danbooru_limit)
                ConfigService.set("sources.sankaku.username", sankaku_username)
                ConfigService.set("sources.sankaku.password", sankaku_password)
                ConfigService.set("sources.sankaku.default_limit", sankaku_limit)
                ConfigService.set("sources.pixiv.username", pixiv_username)
                ConfigService.set("sources.pixiv.password", pixiv_password)
                ConfigService.set("sources.pixiv.default_limit", pixiv_limit)
                # 主题动态应用（Gradio 需重载）
                return "设置已保存，请重启应用以应用主题和语言"
            except ConfigError as e:
                return str(e)

        save_btn.click(
            fn=save_settings,
            inputs=[
                output_dir, temp_dir, log_level, theme, language, tooltips,
                prefix, size_1_1, size_2_3, size_3_2,
                danbooru_limit, sankaku_username, sankaku_password, sankaku_limit,
                pixiv_username, pixiv_password, pixiv_limit
            ],
            outputs=settings_output
        )