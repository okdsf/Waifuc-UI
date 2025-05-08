"""
augment_actions.py - 图像增强相关的动作
"""
from typing import Optional, Tuple, List
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    RandomChoiceAction as WaifucRandomChoiceAction,
    RandomFilenameAction as WaifucRandomFilenameAction,
    MirrorAction as WaifucMirrorAction,
    CharacterEnhanceAction as WaifucCharacterEnhanceAction
)

class RandomChoiceAction(WaifucActionWrapper):
    """
    以指定概率随机选择图像。
    
    参数:
        p (float): 选择概率，默认为 0.5。
        seed (Optional[int]): 随机种子，默认为 None。
    """
    def __init__(self, p: float = 0.5, seed: Optional[int] = None):
        super().__init__(WaifucRandomChoiceAction, p=p, seed=seed)

class RandomFilenameAction(WaifucActionWrapper):
    """
    为图像文件生成随机文件名。
    
    参数:
        ext (str): 文件扩展名，默认为 '.png'。
        seed (Optional[int]): 随机种子，默认为 None。
    """
    def __init__(self, ext: str = '.png', seed: Optional[int] = None):
        super().__init__(WaifucRandomFilenameAction, ext=ext, seed=seed)

class MirrorAction(WaifucActionWrapper):
    """
    生成图像的镜像版本。
    
    参数:
        names (Tuple[str, str]): 原始和镜像文件的命名后缀，默认为 ('origin', 'mirror')。
    """
    def __init__(self, names: Tuple[str, str] = ('origin', 'mirror')):
        super().__init__(WaifucMirrorAction, names=names)

class CharacterEnhanceAction(WaifucActionWrapper):
    """
    通过旋转、裁剪和背景替换增强人物图像。
    
    参数:
        repeats (int): 增强次数，默认为 10。
        modes (Optional[List[str]]): 增强模式（person, halfbody, head），默认为 ['halfbody', 'head']。
        head_ratio (float): 头部裁剪比例，默认为 1.2。
        body_ratio (float): 全身裁剪比例，默认为 1.05。
        halfbody_ratio (float): 半身裁剪比例，默认为 1.1。
        degree_range (Tuple[float, float]): 旋转角度范围，默认为 (-30, 30)。
    """
    def __init__(self, repeats: int = 10, modes: Optional[List[str]] = None,
                 head_ratio: float = 1.2, body_ratio: float = 1.05, halfbody_ratio: float = 1.1,
                 degree_range: Tuple[float, float] = (-30, 30)):
        super().__init__(WaifucCharacterEnhanceAction, repeats=repeats, modes=modes,
                        head_ratio=head_ratio, body_ratio=body_ratio, halfbody_ratio=halfbody_ratio,
                        degree_range=degree_range)