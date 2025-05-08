"""
enhance_actions.py - 图像增强相关的动作
"""
from typing import Optional
import torch
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    ESRGANAction as WaifucESRGANAction,
    SmartCropAction as WaifucSmartCropAction
)

class ESRGANActionWrapper(WaifucActionWrapper):
    """
    使用 Real-ESRGAN 模型对图像进行超分辨率增强。
    
    参数:
        scale (float): 目标缩放因子，例如 1.2、2.0。
        model_path (Optional[str]): 模型文件路径，默认为 'C:\\Users\\Administrator\\Desktop\\AA\\Real-ESRGAN\\weights\\RealESRGAN_x4plus.pth'。
    """
    def __init__(self, scale: float, model_path: Optional[str] = None):
        super().__init__(WaifucESRGANAction, scale=scale, model_path=model_path)

class SmartCropActionWrapper(WaifucActionWrapper):
    """
    使用 IS-Net 模型进行图像分割，智能裁剪图像中的角色区域。
    
    参数:
        width (int): 裁剪后的宽度，默认为 1024。
        height (int): 裁剪后的高度，默认为 1351。
    """
    def __init__(self, width: int = 1024, height: int = 1351):
        super().__init__(WaifucSmartCropAction, width=width, height=height)