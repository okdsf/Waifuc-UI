"""
Source注册表模块 - 管理和注册所有可用的图像来源
"""
from typing import Dict, List, Type, Any
from .base import BaseSource
from .waifuc_sources import (
    LocalSource, DanbooruSource, SankakuSource, ZerochanSource,
    PixivSource, YandereSource
)


class SourceRegistry:
    """
    所有可用图像来源的注册表
    """
    def __init__(self):
        self._sources: Dict[str, Type[BaseSource]] = {}
        self._categories: Dict[str, List[str]] = {
            "本地": [],
            "网络": [],
        }
        
        # 注册来源
        self.register("本地", LocalSource)
        self.register("网络", DanbooruSource)
        self.register("网络", SankakuSource)
        self.register("网络", ZerochanSource)
        self.register("网络", PixivSource)
        self.register("网络", YandereSource)
    
    def register(self, category: str, source_class: Type[BaseSource]) -> None:
        """
        注册一个来源类
        
        Args:
            category: 来源类别
            source_class: 要注册的来源类
        """
        source_name = source_class.__name__
        self._sources[source_name] = source_class
        
        if category not in self._categories:
            self._categories[category] = []
        
        if source_name not in self._categories[category]:
            self._categories[category].append(source_name)
    
    def get_source_class(self, source_name: str) -> Type[BaseSource]:
        """
        获取来源类
        
        Args:
            source_name: 来源名称
            
        Returns:
            来源类
        """
        if source_name not in self._sources:
            raise ValueError(f"来源 '{source_name}' 未找到")
        
        return self._sources[source_name]
    
    def create_source(self, source_name: str, **kwargs) -> BaseSource:
        """
        创建来源实例
        
        Args:
            source_name: 来源名称
            **kwargs: 来源参数
            
        Returns:
            来源实例
        """
        source_class = self.get_source_class(source_name)
        return source_class(**kwargs)
    
    def get_source_params(self, source_name: str) -> Dict[str, Any]:
        """
        获取来源的参数信息
        
        Args:
            source_name: 来源名称
            
        Returns:
            参数信息字典
        """
        source_class = self.get_source_class(source_name)
        # 创建一个临时实例以获取默认参数
        instance = source_class.__new__(source_class)
        if hasattr(instance, 'params'):
            return instance.params
        return {}
    
    def get_categories(self) -> List[str]:
        """
        获取所有来源类别
        
        Returns:
            类别名称列表
        """
        return list(self._categories.keys())
    
    def get_sources_in_category(self, category: str) -> List[str]:
        """
        获取指定类别中的所有来源名称
        
        Args:
            category: 类别名称
            
        Returns:
            来源名称列表
        """
        if category not in self._categories:
            raise ValueError(f"类别 '{category}' 未找到")
        
        return self._categories[category]
    
    def get_all_sources(self) -> Dict[str, List[str]]:
        """
        获取所有注册的来源，按类别分组
        
        Returns:
            以类别为键、来源名称列表为值的字典
        """
        return self._categories.copy()


# 创建全局实例
registry = SourceRegistry()
