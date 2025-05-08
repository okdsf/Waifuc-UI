"""
基础Action接口模块 - 定义所有图像处理操作的基本接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional


class BaseAction(ABC):
    """
    所有图像处理操作的基础接口
    """
    @abstractmethod
    def process(self, item: Any) -> Any:
        """
        处理单个图像项
        
        Args:
            item: 待处理的图像项
            
        Returns:
            处理后的图像项
        """
        pass
    
    @abstractmethod
    def iter(self, item: Any) -> Iterator[Any]:
        """
        处理图像项并生成结果序列
        
        Args:
            item: 待处理的图像项
            
        Yields:
            处理后的图像项序列
        """
        yield item
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取操作的信息
        
        Returns:
            包含操作信息的字典
        """
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__ or "暂无描述。"
        }
    
    def __repr__(self) -> str:
        """
        操作的字符串表示
        """
        return f"{self.__class__.__name__}()"


class ActionWithParams(BaseAction):
    """
    带参数的基础操作类
    """
    def __init__(self, **kwargs):
        self.params = kwargs
        
    def get_info(self) -> Dict[str, Any]:
        """
        获取包含参数的操作信息
        
        Returns:
            包含操作信息的字典
        """
        info = super().get_info()
        info["params"] = self.params
        return info
    
    def __repr__(self) -> str:
        """
        带参数操作的字符串表示
        """
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in self.params.items())
        return f"{self.__class__.__name__}({params_str})"