"""
Action注册表模块 - 管理和注册所有可用的图像处理操作
"""
import inspect
from typing import Dict, List, Type, Any
from .base import BaseAction
from .waifuc_actions import WaifucActionWrapper
from .transform_actions import (
    ModeConvertAction, BackgroundRemovalAction, AlignMaxSizeAction,
    AlignMinSizeAction, AlignMaxAreaAction, PaddingAlignAction
)
from .augment_actions import (
    RandomChoiceAction, RandomFilenameAction, MirrorAction, CharacterEnhanceAction
)
from .split_actions import (
    PersonSplitAction, ThreeStageSplitAction, FrameSplitAction
)
from .filter_actions import (
    FilterSimilarAction, MinSizeFilterAction, MinAreaFilterAction,
    NoMonochromeAction, OnlyMonochromeAction, ClassFilterAction,
    RatingFilterAction, FaceCountAction, HeadCountAction, PersonRatioAction,
    CCIPAction, FirstNSelectAction, SliceSelectAction
)
from .tagging_actions import (
    TaggingAction, TagFilterAction, TagOverlapDropAction, TagDropAction,
    BlacklistedTagDropAction, TagRemoveUnderlineAction
)
from .misc_actions import (
    SafetyAction, ArrivalAction, FileExtAction, FileOrderAction,
    HeadCutOutAction
)
from .custom_actions import (
    PreSortImagesAction, EnhancedImageProcessAction, ProcessRatioGroupAction,
    HeadCoverAction
)
from .enhance_actions import (
    ESRGANActionWrapper, SmartCropActionWrapper
)


class ActionRegistry:
    """
    所有可用图像处理操作的注册表
    """
    def __init__(self):
        self._actions: Dict[str, Type[BaseAction]] = {}
        self._categories: Dict[str, List[str]] = {
            "转换": [],
            "过滤": [],
            "变换": [],
            "分割": [],
            "对齐": [],
            "标签": [],
            "自定义": [],
            "安全": [],
            "调试": [],
            "文件名": [],
            "头部处理": [],
            "增强": [],  # 新增“增强”类别
        }
        
        # 注册操作
        self.register("转换", ModeConvertAction)
        self.register("转换", BackgroundRemovalAction)
        
        self.register("变换", RandomChoiceAction)
        self.register("变换", RandomFilenameAction)
        self.register("变换", MirrorAction)
        self.register("变换", CharacterEnhanceAction)
        
        self.register("对齐", AlignMaxSizeAction)
        self.register("对齐", AlignMinSizeAction)
        self.register("对齐", AlignMaxAreaAction)
        self.register("对齐", PaddingAlignAction)
        
        self.register("分割", ThreeStageSplitAction)
        self.register("分割", PersonSplitAction)
        self.register("分割", FrameSplitAction)
        
        self.register("标签", TaggingAction)
        self.register("标签", TagFilterAction)
        self.register("标签", TagOverlapDropAction)
        self.register("标签", TagDropAction)
        self.register("标签", BlacklistedTagDropAction)
        self.register("标签", TagRemoveUnderlineAction)
        
        self.register("过滤", FilterSimilarAction)
        self.register("过滤", MinSizeFilterAction)
        self.register("过滤", MinAreaFilterAction)
        self.register("过滤", NoMonochromeAction)
        self.register("过滤", OnlyMonochromeAction)
        self.register("过滤", ClassFilterAction)
        self.register("过滤", RatingFilterAction)
        self.register("过滤", FaceCountAction)
        self.register("过滤", HeadCountAction)
        self.register("过滤", PersonRatioAction)
        self.register("过滤", CCIPAction)
        self.register("过滤", FirstNSelectAction)
        self.register("过滤", SliceSelectAction)
        
        self.register("安全", SafetyAction)
        self.register("调试", ArrivalAction)
        self.register("文件名", FileExtAction)
        self.register("文件名", FileOrderAction)
        self.register("头部处理", HeadCutOutAction)
        
        # 注册自定义操作
        self.register("自定义", PreSortImagesAction)
        self.register("自定义", EnhancedImageProcessAction)
        self.register("自定义", ProcessRatioGroupAction)
        self.register("自定义", HeadCoverAction)
        
        # 注册增强操作
        self.register("增强", ESRGANActionWrapper)
        self.register("增强", SmartCropActionWrapper)
    
    def register(self, category: str, action_class: Type[BaseAction]) -> None:
        """
        注册一个操作类
        
        Args:
            category: 操作类别
            action_class: 要注册的操作类
        """
        action_name = action_class.__name__
        self._actions[action_name] = action_class
        
        if category not in self._categories:
            self._categories[category] = []
        
        if action_name not in self._categories[category]:
            self._categories[category].append(action_name)
    
    def get_action_class(self, action_name: str) -> Type[BaseAction]:
        """
        获取操作类
        
        Args:
            action_name: 操作名称
            
        Returns:
            操作类
        """
        if action_name not in self._actions:
            raise ValueError(f"操作 '{action_name}' 未找到")
        
        return self._actions[action_name]
    
    def create_action(self, action_name: str, **kwargs) -> BaseAction:
        """
        创建操作实例
        
        Args:
            action_name: 操作名称
            **kwargs: 操作参数
            
        Returns:
            操作实例
        """
        action_class = self.get_action_class(action_name)
        instance = action_class(**kwargs)
        
        # 检查是否是 WaifucActionWrapper 子类
        if isinstance(instance, WaifucActionWrapper) and hasattr(instance, 'action'):
            return instance
        else:
            # 直接返回实例，适用于自定义动作
            return instance
    
    def get_action_params(self, action_name: str) -> Dict[str, Any]:
        """
        获取操作的参数信息
        
        Args:
            action_name: 操作名称
            
        Returns:
            参数信息字典，包含参数名和默认值（无默认值时为 None）
        """
        action_class = self.get_action_class(action_name)
        sig = inspect.signature(action_class.__init__)
        params = {}
        for name, param in sig.parameters.items():
            if name != 'self':
                if param.default != inspect.Parameter.empty:
                    params[name] = param.default
                else:
                    params[name] = None  # 表示该参数无默认值，UI 中需处理
        return params
    
    def get_categories(self) -> List[str]:
        """
        获取所有操作类别
        
        Returns:
            类别名称列表
        """
        return list(self._categories.keys())
    
    def get_actions_in_category(self, category: str) -> List[str]:
        """
        获取指定类别中的所有操作名称
        
        Args:
            category: 类别名称
            
        Returns:
            操作名称列表
        """
        if category not in self._categories:
            raise ValueError(f"类别 '{category}' 未找到")
        
        return self._categories[category]
    
    def get_all_actions(self) -> Dict[str, List[str]]:
        """
        获取所有注册的操作，按类别分组
        
        Returns:
            以类别为键、操作名称列表为值的字典
        """
        return self._categories.copy()


# 创建全局实例
registry = ActionRegistry()