"""
filter_actions.py - 图像过滤相关的动作
"""
from typing import Optional, List
from .waifuc_actions import WaifucActionWrapper
from waifuc.action import (
    FilterSimilarAction as WaifucFilterSimilarAction,
    MinSizeFilterAction as WaifucMinSizeFilterAction,
    MinAreaFilterAction as WaifucMinAreaFilterAction,
    NoMonochromeAction as WaifucNoMonochromeAction,
    OnlyMonochromeAction as WaifucOnlyMonochromeAction,
    ClassFilterAction as WaifucClassFilterAction,
    RatingFilterAction as WaifucRatingFilterAction,
    FaceCountAction as WaifucFaceCountAction,
    HeadCountAction as WaifucHeadCountAction,
    PersonRatioAction as WaifucPersonRatioAction,
    CCIPAction as WaifucCCIPAction,
    FirstNSelectAction as WaifucFirstNSelectAction,
    SliceSelectAction as WaifucSliceSelectAction
)

class FilterSimilarAction(WaifucActionWrapper):
    """
    使用LPIPS过滤相似或重复图像。
    
    参数:
        mode (str): 过滤模式，'all' 或 'group'，默认 'all'。
        threshold (float): 相似性阈值，默认为 0.45。
        capacity (int): 特征缓存容量，默认为 500。
        rtol (float): 宽高比相对误差，默认为 5e-2。
        atol (float): 宽高比绝对误差，默认为 2e-2。
    """
    def __init__(self, mode: str = 'all', threshold: float = 0.45,
                 capacity: int = 500, rtol: float = 5e-2, atol: float = 2e-2):
        super().__init__(WaifucFilterSimilarAction, mode=mode, threshold=threshold,
                        capacity=capacity, rtol=rtol, atol=atol)

class MinSizeFilterAction(WaifucActionWrapper):
    """
    过滤最小边长小于指定值的图像。
    
    参数:
        min_size (int): 最小边长。
    """
    def __init__(self, min_size: int):
        super().__init__(WaifucMinSizeFilterAction, min_size=min_size)

class MinAreaFilterAction(WaifucActionWrapper):
    """
    过滤面积小于指定值的图像。
    
    参数:
        min_size (int): 最小面积（像素数）。
    """
    def __init__(self, min_size: int):
        super().__init__(WaifucMinAreaFilterAction, min_size=min_size)

class NoMonochromeAction(WaifucActionWrapper):
    """
    过滤单色图像。
    """
    def __init__(self):
        super().__init__(WaifucNoMonochromeAction)

class OnlyMonochromeAction(WaifucActionWrapper):
    """
    仅保留单色图像。
    """
    def __init__(self):
        super().__init__(WaifucOnlyMonochromeAction)

class ClassFilterAction(WaifucActionWrapper):
    """
    根据图像分类（illustration, bangumi, comic, 3d）过滤。
    
    参数:
        classes (List[str]): 允许的分类。
        threshold (Optional[float]): 分数阈值，默认为 None。
    """
    def __init__(self, classes: List[str], threshold: Optional[float] = None):
        super().__init__(WaifucClassFilterAction, classes=classes, threshold=threshold)

class RatingFilterAction(WaifucActionWrapper):
    """
    根据图像评级（safe, r15, r18）过滤。
    
    参数:
        ratings (List[str]): 允许的评级。
        threshold (Optional[float]): 分数阈值，默认为 None。
    """
    def __init__(self, ratings: List[str], threshold: Optional[float] = None):
        super().__init__(WaifucRatingFilterAction, ratings=ratings, threshold=threshold)

class FaceCountAction(WaifucActionWrapper):
    """
    根据人脸数量过滤图像。
    
    参数:
        min_count (Optional[int]): 最小人脸数量，默认为 None。
        max_count (Optional[int]): 最大人脸数量，默认为 None。
        level (str): 检测级别，默认为 's'。
        version (str): 检测模型版本，默认为 'v1.4'。
        conf_threshold (float): 置信度阈值，默认为 0.25。
        iou_threshold (float): IOU 阈值，默认为 0.7。
    """
    def __init__(self, min_count: Optional[int] = None, max_count: Optional[int] = None,
                 level: str = 's', version: str = 'v1.4', conf_threshold: float = 0.25, iou_threshold: float = 0.7):
        super().__init__(WaifucFaceCountAction, min_count=min_count, max_count=max_count,
                        level=level, version=version, conf_threshold=conf_threshold, iou_threshold=iou_threshold)

class HeadCountAction(WaifucActionWrapper):
    """
    根据头部数量过滤图像。
    
    参数:
        min_count (Optional[int]): 最小头部数量，默认为 None。
        max_count (Optional[int]): 最大头部数量，默认为 None。
        level (str): 检测级别，默认为 's'。
        conf_threshold (float): 置信度阈值，默认为 0.3。
        iou_threshold (float): IOU 阈值，默认为 0.7。
    """
    def __init__(self, min_count: Optional[int] = None, max_count: Optional[int] = None,
                 level: str = 's', conf_threshold: float = 0.3, iou_threshold: float = 0.7):
        super().__init__(WaifucHeadCountAction, min_count=min_count, max_count=max_count,
                        level=level, conf_threshold=conf_threshold, iou_threshold=iou_threshold)

class PersonRatioAction(WaifucActionWrapper):
    """
    根据人物区域占图像的比例过滤。
    
    参数:
        ratio (float): 最小比例，默认为 0.4。
        level (str): 检测级别，默认为 'm'。
        version (str): 检测模型版本，默认为 'v1.1'。
        conf_threshold (float): 置信度阈值，默认为 0.3。
        iou_threshold (float): IOU 阈值，默认为 0.5。
    """
    def __init__(self, ratio: float = 0.4, level: str = 'm', version: str = 'v1.1',
                 conf_threshold: float = 0.3, iou_threshold: float = 0.5):
        super().__init__(WaifucPersonRatioAction, ratio=ratio, level=level, version=version,
                        conf_threshold=conf_threshold, iou_threshold=iou_threshold)

class CCIPAction(WaifucActionWrapper):
    """
    使用CCIP特征聚类过滤相似图像。
    
    参数:
        init_source (Optional): 初始图像源，默认为 None。
        min_val_count (int): 最小有效计数，默认为 15。
        step (int): 聚类步长，默认为 5。
        ratio_threshold (float): 比例阈值，默认为 0.6。
        min_clu_dump_ratio (float): 最小聚类丢弃比例，默认为 0.3。
        cmp_threshold (float): 比较阈值，默认为 0.5。
        eps (Optional[float]): OPTICS聚类参数，默认为 None。
        min_samples (Optional[int]): OPTICS聚类参数，默认为 None。
        model (str): 模型名称，默认为 'ccip-caformer-24-randaug-pruned'。
        threshold (Optional[float]): 相似性阈值，默认为 None。
    """
    def __init__(self, init_source=None, min_val_count: int = 15, step: int = 5,
                 ratio_threshold: float = 0.6, min_clu_dump_ratio: float = 0.3, cmp_threshold: float = 0.5,
                 eps: Optional[float] = None, min_samples: Optional[int] = None,
                 model: str = 'ccip-caformer-24-randaug-pruned', threshold: Optional[float] = None):
        super().__init__(WaifucCCIPAction, init_source=init_source, min_val_count=min_val_count, step=step,
                        ratio_threshold=ratio_threshold, min_clu_dump_ratio=min_clu_dump_ratio,
                        cmp_threshold=cmp_threshold, eps=eps, min_samples=min_samples,
                        model=model, threshold=threshold)

class FirstNSelectAction(WaifucActionWrapper):
    """
    选择前N张图像。
    
    参数:
        n (int): 选择的数量。
    """
    def __init__(self, n: int):
        super().__init__(WaifucFirstNSelectAction, n=n)

class SliceSelectAction(WaifucActionWrapper):
    """
    按切片方式选择图像（start, stop, step）。
    
    参数:
        start (Optional[int]): 起始索引，默认为 None。
        stop (Optional[int]): 结束索引，默认为 None。
        step (Optional[int]): 步长，默认为 None。
    """
    def __init__(self, start: Optional[int] = None, stop: Optional[int] = None, step: Optional[int] = None):
        super().__init__(WaifucSliceSelectAction, start=start, stop=stop, step=step)