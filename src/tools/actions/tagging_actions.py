"""
tagging_actions.py - 图像标签管理相关的动作
"""
from typing import Union, List, Mapping
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    TaggingAction as WaifucTaggingAction,
    TagFilterAction as WaifucTagFilterAction,
    TagOverlapDropAction as WaifucTagOverlapDropAction,
    TagDropAction as WaifucTagDropAction,
    BlacklistedTagDropAction as WaifucBlacklistedTagDropAction,
    TagRemoveUnderlineAction as WaifucTagRemoveUnderlineAction
)

class TaggingAction(WaifucActionWrapper):
    """
    使用指定模型为图像生成标签。
    
    参数:
        method (str): 标签模型，默认为 'wd14_v3_swinv2'。
        force (bool): 是否强制重新生成标签，默认为 False。
        general_threshold (float): 通用标签阈值，默认为 0.35。
        character_threshold (float): 角色标签阈值，默认为 0.85。
    """
    def __init__(self, method: str = 'wd14_v3_swinv2', force: bool = False,
                 general_threshold: float = 0.35, character_threshold: float = 0.85):
        super().__init__(WaifucTaggingAction, method=method, force=force,
                        general_threshold=general_threshold, character_threshold=character_threshold)

class TagFilterAction(WaifucActionWrapper):
    """
    根据指定标签和分数过滤图像。
    
    参数:
        tags (Union[List[str], Mapping[str, float]]): 标签或标签分数字典。
        method (str): 标签模型，默认为 'wd14_convnextv2'。
        reversed (bool): 是否反向过滤，默认为 False。
        general_threshold (float): 通用标签阈值，默认为 0.35。
        character_threshold (float): 角色标签阈值，默认为 0.85。
    """
    def __init__(self, tags: Union[List[str], Mapping[str, float]], method: str = 'wd14_convnextv2',
                 reversed: bool = False, general_threshold: float = 0.35, character_threshold: float = 0.85):
        super().__init__(WaifucTagFilterAction, tags=tags, method=method, reversed=reversed,
                        general_threshold=general_threshold, character_threshold=character_threshold)

class TagOverlapDropAction(WaifucActionWrapper):
    """
    删除重叠标签。
    """
    def __init__(self):
        super().__init__(WaifucTagOverlapDropAction)

class TagDropAction(WaifucActionWrapper):
    """
    删除指定标签。
    
    参数:
        tags_to_drop (List[str]): 要删除的标签列表。
    """
    def __init__(self, tags_to_drop: List[str]):
        super().__init__(WaifucTagDropAction, tags_to_drop=tags_to_drop)

class BlacklistedTagDropAction(WaifucActionWrapper):
    """
    删除黑名单标签。
    """
    def __init__(self):
        super().__init__(WaifucBlacklistedTagDropAction)

class TagRemoveUnderlineAction(WaifucActionWrapper):
    """
    移除标签中的下划线。
    """
    def __init__(self):
        super().__init__(WaifucTagRemoveUnderlineAction)