"""
misc_actions.py - 其他杂项动作
"""
from typing import Optional, Mapping, Any, Union, Tuple
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    SafetyAction as WaifucSafetyAction,
    ArrivalAction as WaifucArrivalAction,
    FileExtAction as WaifucFileExtAction,
    FileOrderAction as WaifucFileOrderAction,
    HeadCutOutAction as WaifucHeadCutOutAction
)

class SafetyAction(WaifucActionWrapper):
    """
    检查图像安全性并移除对抗性噪声。
    
    参数:
        cfg_adversarial (Optional[Mapping[str, Any]]): 对抗性噪声移除配置，默认为 None。
        cfg_safe_check (Optional[Mapping[str, Any]]): 安全检查配置，默认为 None。
    """
    def __init__(self, cfg_adversarial: Optional[Mapping[str, Any]] = None,
                 cfg_safe_check: Optional[Mapping[str, Any]] = None):
        super().__init__(WaifucSafetyAction, cfg_adversarial=cfg_adversarial, cfg_safe_check=cfg_safe_check)

class ArrivalAction(WaifucActionWrapper):
    """
    用于调试的到达动作，跟踪处理进度。
    
    参数:
        name (str): 动作名称。
        total (Optional[int]): 总计图像数量，默认为 None。
    """
    def __init__(self, name: str, total: Optional[int] = None):
        super().__init__(WaifucArrivalAction, name=name, total=total)

class FileExtAction(WaifucActionWrapper):
    """
    修改图像文件扩展名。
    
    参数:
        ext (str): 目标扩展名。
        quality (Optional[int]): 保存质量，默认为 None。
    """
    def __init__(self, ext: str, quality: Optional[int] = None):
        super().__init__(WaifucFileExtAction, ext=ext, quality=quality)

class FileOrderAction(WaifucActionWrapper):
    """
    按顺序重命名图像文件。
    
    参数:
        ext (Optional[str]): 文件扩展名，默认为 '.png'。
    """
    def __init__(self, ext: Optional[str] = '.png'):
        super().__init__(WaifucFileOrderAction, ext=ext)

class HeadCutOutAction(WaifucActionWrapper):
    """
    裁剪图像以移除头部区域。
    
    参数:
        kp_threshold (float): 关键点阈值，默认为 0.3。
        level (str): 检测级别，默认为 's'。
        version (str): 检测模型版本，默认为 'v1.4'。
        max_infer_size (int): 最大推理尺寸，默认为 640。
        conf_threshold (float): 置信度阈值，默认为 0.25。
        iou_threshold (float): IOU 阈值，默认为 0.7。
    """
    def __init__(self, kp_threshold: float = 0.3, level: str = 's', version: str = 'v1.4', max_infer_size: int = 640,
                 conf_threshold: float = 0.25, iou_threshold: float = 0.7):
        super().__init__(WaifucHeadCutOutAction, kp_threshold=kp_threshold, level=level, version=version,
                        max_infer_size=max_infer_size, conf_threshold=conf_threshold, iou_threshold=iou_threshold)