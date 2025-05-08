"""
split_actions.py - 图像分割相关的动作
"""
from typing import Optional, Dict
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    PersonSplitAction as WaifucPersonSplitAction,
    ThreeStageSplitAction as WaifucThreeStageSplitAction,
    FrameSplitAction as WaifucFrameSplitAction
)

class PersonSplitAction(WaifucActionWrapper):
    """
    检测并裁剪图像中的每个人物，生成单独的图像。
    
    参数:
        keep_original (bool): 是否保留原始图像，默认为 False。
        level (str): 检测级别，默认为 'm'。
        version (str): 检测模型版本，默认为 'v1.1'。
        conf_threshold (float): 置信度阈值，默认为 0.3。
        iou_threshold (float): IOU 阈值，默认为 0.5。
        keep_origin_tags (bool): 是否保留原始标签，默认为 False。
    """
    def __init__(self, keep_original: bool = False, level: str = 'm', version: str = 'v1.1',
                 conf_threshold: float = 0.3, iou_threshold: float = 0.5, keep_origin_tags: bool = False):
        super().__init__(WaifucPersonSplitAction, keep_original=keep_original, level=level, version=version,
                        conf_threshold=conf_threshold, iou_threshold=iou_threshold, keep_origin_tags=keep_origin_tags)

class ThreeStageSplitAction(WaifucActionWrapper):
    """
    进行全身、半身、头部的三阶段分割。
    
    参数:
        person_conf (Optional[dict]): 人物检测配置，默认为 None。
        halfbody_conf (Optional[dict]): 半身检测配置，默认为 None。
        head_conf (Optional[dict]): 头部检测配置，默认为 None。
        head_scale (float): 头部裁剪比例，默认为 1.5。
        split_eyes (bool): 是否分割眼部，默认为 False。
        eye_conf (Optional[dict]): 眼部检测配置，默认为 None。
        eye_scale (float): 眼部裁剪比例，默认为 2.4。
        split_person (bool): 是否分割人物，默认为 True。
        keep_origin_tags (bool): 是否保留原始标签，默认为 False。
        return_person (bool): 是否返回人物分割结果，默认为 True。
        return_halfbody (bool): 是否返回半身分割结果，默认为 True。
        return_head (bool): 是否返回头部分割结果，默认为 True。
        return_eyes (bool): 是否返回眼部分割结果，默认为 False。
    """
    def __init__(self, person_conf: Optional[Dict] = None, halfbody_conf: Optional[Dict] = None,
                 head_conf: Optional[Dict] = None, head_scale: float = 1.5,
                 split_eyes: bool = False, eye_conf: Optional[Dict] = None, eye_scale: float = 2.4,
                 split_person: bool = True, keep_origin_tags: bool = False,
                 return_person: bool = True, return_halfbody: bool = True,
                 return_head: bool = True, return_eyes: bool = False):
        super().__init__(WaifucThreeStageSplitAction, person_conf=person_conf, halfbody_conf=halfbody_conf,
                        head_conf=head_conf, head_scale=head_scale, split_eyes=split_eyes,
                        eye_conf=eye_conf, eye_scale=eye_scale, split_person=split_person,
                        keep_origin_tags=keep_origin_tags, return_person=return_person,
                        return_halfbody=return_halfbody, return_head=return_head, return_eyes=return_eyes)
        
class FrameSplitAction(WaifucActionWrapper):
    """
    将多帧图像（如GIF）分割成单帧。
    """
    def __init__(self):
        super().__init__(WaifucFrameSplitAction)