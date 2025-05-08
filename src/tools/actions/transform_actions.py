"""
transform_actions.py - 图像变换相关的动作
"""
from typing import Optional, Tuple
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    ModeConvertAction as WaifucModeConvertAction,
    BackgroundRemovalAction as WaifucBackgroundRemovalAction,
    AlignMaxSizeAction as WaifucAlignMaxSizeAction,
    AlignMinSizeAction as WaifucAlignMinSizeAction,
    AlignMaxAreaAction as WaifucAlignMaxAreaAction,
    PaddingAlignAction as WaifucPaddingAlignAction
)

class ModeConvertAction(WaifucActionWrapper):
    """
    将图像转换为指定模式，并强制设置背景颜色。
    
    参数:
        mode (str): 目标图像模式，默认为 'RGB'。
        force_background (Optional[str]): 强制背景颜色，默认为 'white'。
    """
    def __init__(self, mode: str = 'RGB', force_background: Optional[str] = 'white'):
        super().__init__(WaifucModeConvertAction, mode=mode, force_background=force_background)

class BackgroundRemovalAction(WaifucActionWrapper):
    """
    使用isnetis模型移除图像背景，保留前景。
    """
    def __init__(self):
        super().__init__(WaifucBackgroundRemovalAction)

class AlignMaxSizeAction(WaifucActionWrapper):
    """
    调整图像，确保最大边不超过指定尺寸。
    
    参数:
        max_size (int): 最大边长。
    """
    def __init__(self, max_size: int):
        super().__init__(WaifucAlignMaxSizeAction, max_size=max_size)

class AlignMinSizeAction(WaifucActionWrapper):
    """
    调整图像，确保最小边不小于指定尺寸。
    
    参数:
        min_size (int): 最小边长。
    """
    def __init__(self, min_size: int):
        super().__init__(WaifucAlignMinSizeAction, min_size=min_size)

class AlignMaxAreaAction(WaifucActionWrapper):
    """
    调整图像尺寸，使其面积不超过指定值。
    
    参数:
        size (int): 最大面积（像素数）。
    """
    def __init__(self, size: int):
        super().__init__(WaifucAlignMaxAreaAction, size=size)

class PaddingAlignAction(WaifucActionWrapper):
    """
    通过填充将图像对齐到指定尺寸。
    
    参数:
        size (Tuple[int, int]): 目标尺寸 (width, height)。
        color (str): 填充颜色，默认为 'white'。
    """
    def __init__(self, size: Tuple[int, int], color: str = 'white'):
        super().__init__(WaifucPaddingAlignAction, size=size, color=color)