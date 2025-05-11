"""
程序入口：启动 Gradio 应用，配置服务器地址和端口以适配 VPN 环境。
"""
from src.ui.app import app

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",  # 监听所有接口，绕过 localhost 限制
        server_port=7860,       # 固定端口
        show_error=True         # 显示详细错误
    )