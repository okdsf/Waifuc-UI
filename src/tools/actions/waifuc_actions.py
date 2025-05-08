"""
Waifuc库Actions封装模块 - 封装waifuc库中的各种图像处理操作
"""
from typing import Any, Iterator, Optional
import logging
from .base import ActionWithParams

class WaifucActionWrapper(ActionWithParams):
    """
    Waifuc库Actions的基础封装类。
    """
    def __init__(self, action_class, **kwargs):
        super().__init__(**kwargs)
        self.action_class = action_class
        if kwargs:
            try:
                self.action = action_class(**kwargs)
            except TypeError as e:
                if "takes no arguments" in str(e):
                    self.action = action_class()
                else:
                    raise ValueError(f"Failed to initialize {action_class.__name__}: {str(e)}")
        else:
            self.action = action_class()
    
    def process(self, item: Any) -> Any:
        """
        使用封装的waifuc action处理单个图像项
        
        Args:
            item: 待处理的图像项
            
        Returns:
            处理后的图像项
        """
        try:
            return self.action.process(item)
        except Exception as e:
            logging.error(f"Process error in {self.action_class.__name__}: {str(e)}")
            return None
    
    def iter(self, item: Any) -> Iterator[Any]:
        """
        使用封装的waifuc action处理图像项并生成结果序列
        
        Args:
            item: 待处理的图像项
            
        Yields:
            处理后的图像项序列
        """
        try:
            for result in self.action.iter(item):
                if result is not None:
                    yield result
        except Exception as e:
            logging.error(f"Iter error in {self.action_class.__name__}: {str(e)}")