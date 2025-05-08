"""
custom_actions.py - 自定义图像处理操作
"""
import logging
from typing import Iterator, Any, Dict, Union, Tuple
import random
from PIL import Image, ImageDraw
from waifuc.model import ImageItem
from waifuc.action import ProcessAction
from waifuc.source import LocalSource
from imgutils.detect.head import detect_heads

class PreSortImagesAction(ProcessAction):
    """
    按宽高比预先对图像进行分类
    """
    def __init__(self, ratios=None):
        super().__init__()
        if ratios is None:
            ratios = {
                '1:1': 1/1,
                '2:3': 2/3,
                '3:2': 3/2,
            }
        self.ratios = ratios

    def process(self, item: ImageItem) -> ImageItem:
        """为图像添加分类元数据"""
        try:
            width, height = item.image.size
            img_ratio = width / height
            closest = self._closest_ratio(img_ratio)
            item.meta['ratio'] = closest
            return item
        except Exception as e:
            logging.error(f"PreSortImagesAction process failed: {str(e)}")
            return None

    def iter(self, current_dir: str, output_dir: str) -> Iterator[Dict[str, Any]]:
        """从 current_dir 加载图像，处理并返回"""
        source = LocalSource(current_dir)
        for item in source:
            processed_item = self.process(item)
            if processed_item:
                yield {'item': processed_item}

    def _closest_ratio(self, ratio: float) -> str:
        """找到最接近的预定义比例"""
        return min(self.ratios.keys(), key=lambda k: abs(ratio - self.ratios[k]))

class EnhancedImageProcessAction(ProcessAction):
    """
    增强图像处理操作 - 实现综合功能
    """
    def __init__(self, prefix="output", sizes=None):
        super().__init__()
        if sizes is None:
            sizes = {
                '1:1': 1024,
                '2:3': 960,
                '3:2': 960
            }
        self.prefix = prefix
        self.sizes = sizes

    def process(self, item: ImageItem) -> ImageItem:
        """执行图像处理逻辑"""
        try:
            ratio = item.meta.get('ratio', '1:1')
            min_size = self.sizes.get(ratio, 1024)
            image = item.image
            width, height = image.size
            if min(width, height) < min_size:
                scale = min_size / min(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            return ImageItem(image, item.meta)
        except Exception as e:
            logging.error(f"EnhancedImageProcessAction process failed: {str(e)}")
            return None

    def iter(self, current_dir: str, output_dir: str) -> Iterator[Dict[str, Any]]:
        """从 current_dir 加载图像，处理并返回"""
        source = LocalSource(current_dir)
        for item in source:
            processed_item = self.process(item)
            if processed_item:
                yield {'item': processed_item}

class ProcessRatioGroupAction(ProcessAction):
    """
    处理特定宽高比的图像组
    """
    def __init__(self, min_size: int):
        super().__init__()
        self.min_size = min_size

    def process(self, item: ImageItem) -> ImageItem:
        """调整图像大小"""
        try:
            image = item.image
            width, height = image.size
            if min(width, height) < self.min_size:
                scale = self.min_size / min(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            return ImageItem(image, item.meta)
        except Exception as e:
            logging.error(f"ProcessRatioGroupAction process failed: {str(e)}")
            return None

    def iter(self, current_dir: str, output_dir: str) -> Iterator[Dict[str, Any]]:
        """从 current_dir 加载图像，处理并返回"""
        source = LocalSource(current_dir)
        for item in source:
            processed_item = self.process(item)
            if processed_item:
                yield {'item': processed_item}

class HeadCoverAction(ProcessAction):
    """
    检测并覆盖图像中的头部区域。
    
    参数:
        color (str): 覆盖颜色，默认为 'random'（随机颜色）。
        scale (Union[float, Tuple[float, float]]): 覆盖区域缩放比例，默认为 0.8。
        model (str): 头部检测模型名，默认为 'head_detect_v1.6_s'。
        conf_threshold (float): 置信度阈值，默认为 0.3。
        iou_threshold (float): IOU 阈值，默认为 0.7。
    """
    def __init__(self, color: str = 'random', scale: Union[float, Tuple[float, float]] = 0.8,
                 model: str = 'head_detect_v1.6_s', conf_threshold: float = 0.3, iou_threshold: float = 0.7):
        self.color = color
        self.scale = scale
        self.model = model
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.params = {
            'color': color,
            'scale': scale,
            'model': model,
            'conf_threshold': conf_threshold,
            'iou_threshold': iou_threshold
        }

    def process(self, item: ImageItem) -> ImageItem:
        """处理图像，覆盖头部区域"""
        try:
            logging.debug(f"处理图片: {item.meta.get('filename', 'unknown')}, 参数: "
                         f"color={self.color}, scale={self.scale}, model={self.model}, "
                         f"conf_threshold={self.conf_threshold}, iou_threshold={self.iou_threshold}")

            # 检测头部区域
            head_areas = []
            for (x0, y0, x1, y1), _, _ in detect_heads(
                item.image,
                model_name=self.model,
                conf_threshold=self.conf_threshold,
                iou_threshold=self.iou_threshold
            ):
                width, height = x1 - x0, y1 - y0
                xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
                if isinstance(self.scale, tuple):
                    min_scale, max_scale = self.scale
                    scale = min_scale + random.random() * (max_scale - min_scale)
                else:
                    scale = self.scale
                width, height = width * scale, height * scale
                x0, x1 = xc - width / 2, xc + width / 2
                y0, y1 = yc - height / 2, yc + height / 2
                # 确保坐标合法
                x0, y0 = max(0, x0), max(0, y0)
                x1, y1 = min(item.image.width, x1), min(item.image.height, y1)
                head_areas.append((x0, y0, x1, y1))

            # 确定覆盖颜色
            if self.color == 'random':
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            else:
                color = self.color

            # 复制图片并覆盖头部区域
            image = item.image.copy()
            draw = ImageDraw.Draw(image)
            for x0, y0, x1, y1 in head_areas:
                draw.rectangle((x0, y0, x1, y1), fill=color)

            # 返回处理后的图片
            return ImageItem(image, item.meta)

        except Exception as e:
            logging.error(f"HeadCoverAction 处理失败: {str(e)}", exc_info=True)
            return None

    def iter(self, item: ImageItem) -> Iterator[ImageItem]:
        """迭代处理图像"""
        result = self.process(item)
        if result is not None:
            yield result

    def get_info(self) -> Dict[str, Any]:
        """
        获取操作的信息
        """
        return {
            "name": self.__class__.__name__,
            "description": "检测并覆盖图像中的头部区域",
            "params": self.params
        }