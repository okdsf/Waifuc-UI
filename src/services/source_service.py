"""
数据源服务：包装 src/tools/sources/source_registry.py，提供数据源类型获取和参数验证，
返回字典数据，供 Gradio 前端使用。
"""
from src.tools.sources.source_registry import registry as source_registry
import os
from typing import List, Dict

class SourceError(Exception):
    pass

class SourceService:
    # 内存中的数据源存储（临时方案）
    _saved_sources: List[Dict] = []

    @staticmethod
    def get_source_types() -> List[str]:
        """获取所有可用数据源类型"""
        categories = source_registry.get_categories()
        sources = []
        for category in categories:
            sources.extend(source_registry.get_sources_in_category(category))
        return sources

    @staticmethod
    def validate_source(source_type: str, params: Dict) -> None:
        """验证数据源参数，失败时抛出异常"""
        if source_type == "LocalSource":
            directory = params.get("directory", "").strip()
            if not directory:
                raise SourceError("请选择图像目录")
            if not os.path.exists(directory):
                raise SourceError(f"目录不存在: {directory}")
        elif "tags" in params and not params["tags"]:
            raise SourceError("请至少输入一个标签")

    @staticmethod
    def save_source(source_data: Dict) -> None:
        """
        保存数据源到内存

        Args:
            source_data: 数据源字典，格式为 {"type": str, "params": dict}
        """
        if not isinstance(source_data, dict) or "type" not in source_data or "params" not in source_data:
            raise SourceError("无效的数据源格式")
        if source_data["type"] not in SourceService.get_source_types():
            raise SourceError(f"未知的数据源类型: {source_data['type']}")
        SourceService._saved_sources.append(source_data)

    @staticmethod
    def get_saved_sources() -> List[Dict]:
        """
        获取所有保存的数据源

        Returns:
            数据源列表，每个元素为 {"type": str, "params": dict}
        """
        return SourceService._saved_sources