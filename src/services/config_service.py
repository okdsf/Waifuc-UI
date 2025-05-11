"""
配置服务：包装 src/data/config_manager.py，提供配置读写功能。
包括输出目录、临时目录、日志级别等设置，供 Gradio 前端使用。
"""
from src.data.config_manager import config_manager
import os

class ConfigError(Exception):
    """配置相关错误"""
    pass

class ConfigService:
    @staticmethod
    def get_output_directory() -> str:
        """获取默认输出目录"""
        return config_manager.get("general.output_directory", "")

    @staticmethod
    def set_output_directory(directory: str) -> None:
        """设置默认输出目录"""
        if directory and not os.path.isdir(directory):
            raise ConfigError("无效的输出目录")
        config_manager.set("general.output_directory", directory)

    @staticmethod
    def get_temp_directory() -> str:
        """获取临时目录"""
        return config_manager.get("general.temp_directory", "")

    @staticmethod
    def set_temp_directory(directory: str) -> None:
        """设置临时目录"""
        if directory and not os.path.isdir(directory):
            raise ConfigError("无效的临时目录")
        config_manager.set("general.temp_directory", directory)

    @staticmethod
    def get_log_level() -> str:
        """获取日志级别"""
        return config_manager.get("general.log_level", "INFO")

    @staticmethod
    def set_log_level(level: str) -> None:
        """设置日志级别"""
        if level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ConfigError("无效的日志级别")
        config_manager.set("general.log_level", level)

    @staticmethod
    def get(key: str, default: any = None) -> any:
        """通用获取配置"""
        return config_manager.get(key, default)

    @staticmethod
    def set(key: str, value: any) -> None:
        """通用设置配置"""
        config_manager.set(key, value)