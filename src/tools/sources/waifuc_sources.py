"""
Waifuc库Sources封装模块 - 封装waifuc库中的各种图像来源
"""
from typing import Any, Dict, Iterator, List, Optional
from .base import SourceWithParams

# 导入waifuc.source模块
import waifuc.source


class WaifucSourceWrapper(SourceWithParams):
    """
    Waifuc库Sources的基础封装类
    """
    def __init__(self, source_class, **kwargs):
        super().__init__(**kwargs)
        self.source_class = source_class
        self.source = source_class(**kwargs)
    
    def fetch(self, *args, **kwargs) -> Iterator[Any]:
        """
        从封装的waifuc source获取图像
        
        Yields:
            图像项序列
        """
        yield from self.source


# 本地图像来源
class LocalSource(WaifucSourceWrapper):
    """
    本地图像文件来源
    """
    def __init__(self, directory: str):
        super().__init__(
            waifuc.source.LocalSource,
            directory=directory
        )


# Danbooru来源
class DanbooruSource(WaifucSourceWrapper):
    """
    从Danbooru获取图像
    """
    def __init__(self, tags: List[str], limit: int = 100):
        super().__init__(
            waifuc.source.DanbooruSource,
            tags=tags,
            limit=limit
        )


# Sankaku来源
class SankakuSource(WaifucSourceWrapper):
    """
    从Sankaku Complex获取图像
    """
    def __init__(self, tags: List[str], username: str = None, password: str = None, limit: int = 100):
        super().__init__(
            waifuc.source.SankakuSource,
            tags=tags,
            username=username,
            password=password,
            limit=limit
        )


# Zerochan来源
class ZerochanSource(WaifucSourceWrapper):
    """
    从Zerochan获取图像
    """
    def __init__(self, tags: List[str], limit: int = 100):
        super().__init__(
            waifuc.source.ZerochanSource,
            tags=tags,
            limit=limit
        )


# Pixiv来源
class PixivSource(WaifucSourceWrapper):
    """
    从Pixiv获取图像
    """
    def __init__(self, tags: List[str], username: str = None, password: str = None, limit: int = 100):
        super().__init__(
            waifuc.source.PixivSource,
            tags=tags,
            username=username,
            password=password,
            limit=limit
        )


# Yandere来源
class YandereSource(WaifucSourceWrapper):
    """
    从Yande.re获取图像
    """
    def __init__(self, tags: List[str], limit: int = 100):
        super().__init__(
            waifuc.source.YandereSource,
            tags=tags,
            limit=limit
        )