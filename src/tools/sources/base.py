"""
基础Source接口模块 - 定义所有图像来源的基本接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional


class BaseSource(ABC):
    """
    所有图像来源的基础接口
    """
    @abstractmethod
    def fetch(self, *args, **kwargs) -> Iterator[Any]:
        """
        从来源获取图像
        
        Yields:
            图像项序列
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取来源的信息
        
        Returns:
            包含来源信息的字典
        """
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__ or "暂无描述。"
        }
    
    def __repr__(self) -> str:
        """
        来源的字符串表示
        """
        return f"{self.__class__.__name__}()"


class SourceWithParams(BaseSource):
    """
    带参数的基础来源类
    """
    def __init__(self, **kwargs):
        self.params = kwargs
        
    def get_info(self) -> Dict[str, Any]:
        """
        获取包含参数的来源信息
        
        Returns:
            包含来源信息的字典
        """
        info = super().get_info()
        info["params"] = self.params
        return info
    
    def __repr__(self) -> str:
        """
        带参数来源的字符串表示
        """
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in self.params.items())
        return f"{self.__class__.__name__}({params_str})"
