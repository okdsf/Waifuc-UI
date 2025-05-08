"""
Actions包初始化文件 - 导出所有公共组件并注册动作
"""
from .enhance_actions import ESRGANActionWrapper, SmartCropActionWrapper
from .action_registry import registry
from .base import BaseAction, ActionWithParams
from .waifuc_actions import WaifucActionWrapper
from .transform_actions import (
    ModeConvertAction,
    BackgroundRemovalAction,
    AlignMaxSizeAction,
    AlignMinSizeAction,
    AlignMaxAreaAction,
    PaddingAlignAction
)
from .augment_actions import (
    RandomChoiceAction,
    RandomFilenameAction,
    MirrorAction,
    CharacterEnhanceAction
)
from .split_actions import (
    PersonSplitAction,
    ThreeStageSplitAction,
    FrameSplitAction
)
from .filter_actions import (
    FilterSimilarAction,
    MinSizeFilterAction,
    MinAreaFilterAction,
    NoMonochromeAction,
    OnlyMonochromeAction,
    ClassFilterAction,
    RatingFilterAction,
    FaceCountAction,
    HeadCountAction,
    PersonRatioAction,
    CCIPAction,
    FirstNSelectAction,
    SliceSelectAction
)
from .tagging_actions import (
    TaggingAction,
    TagFilterAction,
    TagOverlapDropAction,
    TagDropAction,
    BlacklistedTagDropAction,
    TagRemoveUnderlineAction
)
from .misc_actions import (
    SafetyAction,
    ArrivalAction,
    FileExtAction,
    FileOrderAction,
    HeadCutOutAction
)
from .custom_actions import (
    PreSortImagesAction,
    EnhancedImageProcessAction,
    ProcessRatioGroupAction,
    HeadCoverAction
)

# 注册动作
registry.register("转换", ModeConvertAction)
registry.register("转换", BackgroundRemovalAction)
registry.register("对齐", AlignMaxSizeAction)
registry.register("对齐", AlignMinSizeAction)
registry.register("对齐", AlignMaxAreaAction)
registry.register("对齐", PaddingAlignAction)
registry.register("变换", RandomChoiceAction)
registry.register("变换", RandomFilenameAction)
registry.register("变换", MirrorAction)
registry.register("变换", CharacterEnhanceAction)
registry.register("分割", PersonSplitAction)
registry.register("分割", ThreeStageSplitAction)
registry.register("分割", FrameSplitAction)
registry.register("过滤", FilterSimilarAction)
registry.register("过滤", MinSizeFilterAction)
registry.register("过滤", MinAreaFilterAction)
registry.register("过滤", NoMonochromeAction)
registry.register("过滤", OnlyMonochromeAction)
registry.register("过滤", ClassFilterAction)
registry.register("过滤", RatingFilterAction)
registry.register("过滤", FaceCountAction)
registry.register("过滤", HeadCountAction)
registry.register("过滤", PersonRatioAction)
registry.register("过滤", CCIPAction)
registry.register("过滤", FirstNSelectAction)
registry.register("过滤", SliceSelectAction)
registry.register("标签", TaggingAction)
registry.register("标签", TagFilterAction)
registry.register("标签", TagOverlapDropAction)
registry.register("标签", TagDropAction)
registry.register("标签", BlacklistedTagDropAction)
registry.register("标签", TagRemoveUnderlineAction)
registry.register("安全", SafetyAction)
registry.register("调试", ArrivalAction)
registry.register("文件名", FileExtAction)
registry.register("文件名", FileOrderAction)
registry.register("头部处理", HeadCutOutAction)
registry.register("自定义", PreSortImagesAction)
registry.register("自定义", EnhancedImageProcessAction)
registry.register("自定义", ProcessRatioGroupAction)
registry.register("自定义", HeadCoverAction)
registry.register("增强", ESRGANActionWrapper)
registry.register("增强", SmartCropActionWrapper)
