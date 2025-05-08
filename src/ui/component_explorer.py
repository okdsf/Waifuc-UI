from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QTextBrowser, QPushButton
from PyQt5.QtCore import Qt

# 完整组件信息列表
components = [
    {
        "category": "图像模式转换",
        "name": "ModeConvertAction",
        "description": "将图像转换为指定的模式（如 'RGB'、'RGBA'），并可选地设置背景颜色，用于统一图像格式或处理透明背景。",
        "parameters": [
            {
                "name": "mode",
                "type": "字符串",
                "default": "'RGB'",
                "description": "目标图像模式，决定输出图像的颜色通道。支持 'RGB'（三通道彩色）、'RGBA'（带透明通道）、'L'（灰度图）。"
            },
            {
                "name": "force_background",
                "type": "字符串",
                "default": "'white'",
                "description": "透明区域填充颜色，用于处理透明图像转换到非透明模式时的背景填充。支持 'white'、'black'、'gray' 或 None（不填充）。"
            }
        ],
        "call_example": "action = ModeConvertAction(mode='RGB', force_background='white')\nprocessed_item = action.process(item)",
        "notes": "输入图像必须是 ImageItem 类型。透明图像在转换为 'RGB' 时会填充背景颜色。建议检查输入图像格式以避免错误。",
        "implementation": """
依赖库：PIL (Pillow) 的 Image 模块。
实现步骤：
1. 调用 waifuc.data.load_image，传入输入图像、目标模式 mode 和 force_background 参数。
2. 如果 force_background 非 None，则用指定颜色填充透明区域。
3. 返回转换后的 ImageItem，保留原 meta 数据。
伪代码：
```python
image = load_image(item.image, mode=mode, force_background=force_background)
return ImageItem(image, item.meta)
```
"""
    },
    {
        "category": "背景移除",
        "name": "BackgroundRemovalAction",
        "description": "使用 isnetis 模型移除图像背景，保留前景（如角色），生成带透明背景的 RGBA 图像，适合动漫角色提取。",
        "parameters": [],
        "call_example": "action = BackgroundRemovalAction()\nprocessed_item = action.process(item)",
        "notes": "依赖 imgutils.segment.segment_rgba_with_isnetis，需确保模型已安装。处理复杂背景可能需要调整模型参数。",
        "implementation": """
依赖库：imgutils.segment 的 segment_rgba_with_isnetis。
实现步骤：
1. 输入图像转换为 RGB 格式。
2. 调用 IS-Net 模型（深度学习分割模型）生成前景掩码。
3. 根据掩码将背景区域设为透明，生成 RGBA 图像。
4. 返回新的 ImageItem，保留原 meta 数据。
伪代码：
```python
_, image = segment_rgba_with_isnetis(item.image)
return ImageItem(image, item.meta)
```
IS-Net 模型：基于 U-Net 架构，预训练于动漫图像数据集，擅长分割复杂背景。
"""
    },
    {
        "category": "数据增强",
        "name": "RandomChoiceAction",
        "description": "以指定概率随机选择图像，用于数据采样或减少数据集规模。",
        "parameters": [
            {
                "name": "p",
                "type": "浮点数",
                "default": "0.5",
                "description": "选择概率，决定图像被保留的概率。取值范围 0 到 1，p=0.5 表示 50% 概率保留。"
            },
            {
                "name": "seed",
                "type": "整数",
                "default": "None",
                "description": "随机种子，用于初始化随机数生成器，保证结果可复现。若为 None 则使用系统随机种子。"
            }
        ],
        "call_example": "action = RandomChoiceAction(p=0.5, seed=42)\nfor selected_item in action.iter(item): ...",
        "notes": "适合用于数据集清洗或随机抽样。seed 参数可确保重复运行结果一致。",
        "implementation": """
依赖库：Python 的 random 模块。
实现步骤：
1. 初始化 Random 对象，若 seed 非 None 则设置随机种子。
2. 对每张图像，生成随机数（random.random()），若小于 p 则 yield 输出。
伪代码：
```python
random.seed(seed)
if random.random() <= p:
    yield item
```
"""
    },
    {
        "category": "数据增强",
        "name": "RandomFilenameAction",
        "description": "随机重命名图像文件名，生成唯一文件名以避免冲突。",
        "parameters": [
            {
                "name": "ext",
                "type": "字符串",
                "default": "'.png'",
                "description": "目标文件扩展名，如 '.png' 或 '.jpg'，决定输出文件格式。"
            },
            {
                "name": "seed",
                "type": "整数",
                "default": "None",
                "description": "随机种子，用于初始化随机数生成器，保证文件名生成可复现。"
            }
        ],
        "call_example": "action = RandomFilenameAction(ext='.jpg', seed=42)\nfor renamed_item in action.iter(item): ...",
        "notes": "若元数据中无 filename 且未指定 ext，会抛出错误。建议明确指定 ext 以避免异常。",
        "implementation": """
依赖库：waifuc.random 的 random_sha1 函数。
实现步骤：
1. 初始化 Random 对象，若 seed 非 None 则设置种子。
2. 检查 meta['filename']，若存在则提取原扩展名，否则使用指定 ext。
3. 调用 random_sha1 生成唯一文件名，附加 ext。
4. 更新 meta['filename']，返回新的 ImageItem。
伪代码：
```python
ext = ext or os.path.splitext(item.meta['filename'])[1]
filename = random_sha1(rnd=random) + ext
yield ImageItem(item.image, {**item.meta, 'filename': filename})
```
"""
    },
    {
        "category": "数据增强",
        "name": "MirrorAction",
        "description": "生成原始图像及其水平镜像图像，增加数据集多样性。",
        "parameters": [
            {
                "name": "names",
                "type": "元组",
                "default": "('origin', 'mirror')",
                "description": "原始和镜像图像的文件名后缀，用于区分两张图像，如 ('orig', 'mirr')。"
            }
        ],
        "call_example": "action = MirrorAction(names=('orig', 'mirr'))\nfor mirrored_item in action.iter(item): ...",
        "notes": "常用于数据增强，尤其在图像分类任务中提高模型鲁棒性。",
        "implementation": """
依赖库：PIL 的 ImageOps 模块。
实现步骤：
1. 检查 meta['filename']，若存在则提取文件名主体和扩展名。
2. 对原始图像，附加 origin 后缀，生成 ImageItem。
3. 调用 ImageOps.mirror 翻转图像，附加 mirror 后缀，生成另一个 ImageItem。
4. yield 输出两张图像。
伪代码：
```python
if 'filename' in item.meta:
    filebody, ext = os.path.splitext(item.meta['filename'])
    yield ImageItem(item.image, {**item.meta, 'filename': f'{filebody}_{names[0]}{ext}'})
    yield ImageItem(ImageOps.mirror(item.image), {**item.meta, 'filename': f'{filebody}_{names[1]}{ext}'})
else:
    yield ImageItem(item.image, item.meta)
    yield ImageItem(ImageOps.mirror(item.image), item.meta)
```
"""
    },
    {
        "category": "数据增强",
        "name": "CharacterEnhanceAction",
        "description": "通过旋转、裁剪和背景替换生成角色图像的变体，增强数据集多样性。",
        "parameters": [
            {
                "name": "repeats",
                "type": "整数",
                "default": "10",
                "description": "生成变体图像的数量，取值范围大于 0。"
            },
            {
                "name": "modes",
                "type": "列表",
                "default": "['halfbody', 'head']",
                "description": "增强模式，决定裁剪区域。支持 'person'（全身）、'halfbody'（半身）、'head'（头部）。"
            },
            {
                "name": "head_ratio",
                "type": "浮点数",
                "default": "1.2",
                "description": "头部裁剪比例，决定头部区域放大倍数，取值大于 0。"
            },
            {
                "name": "body_ratio",
                "type": "浮点数",
                "default": "1.05",
                "description": "全身裁剪比例，决定全身区域放大倍数，取值大于 0。"
            },
            {
                "name": "halfbody_ratio",
                "type": "浮点数",
                "default": "1.1",
                "description": "半身裁剪比例，决定半身区域放大倍数，取值大于 0。"
            },
            {
                "name": "degree_range",
                "type": "元组",
                "default": "(-30, 30)",
                "description": "旋转角度范围（单位：度），决定随机旋转的上下限。"
            }
        ],
        "call_example": "action = CharacterEnhanceAction(repeats=5, modes=['person'], degree_range=(-15, 15))\nfor enhanced_item in action.iter(item): ...",
        "notes": "依赖 waifuc.detect 的检测函数和 BackgroundImageSet，可能因检测失败抛出异常。建议调整 ratio 参数以优化裁剪效果。",
        "implementation": """
依赖库：waifuc.detect（检测函数）、waifuc.resource.BackgroundImageSet、PIL 的 Image 模块。
实现步骤：
1. 初始化随机数生成器，确定旋转角度（在 degree_range 内）。
2. 转换图像为 RGBA 格式，调用检测函数（detect_heads、detect_person 等）识别目标区域。
3. 根据 modes 选择裁剪区域（头部、全身或半身），按对应 ratio 放大。
4. 从 BackgroundImageSet 随机选取背景图像，调整大小后粘贴裁剪区域。
5. 重复 repeats 次，生成多个变体图像。
伪代码：
```python
for _ in range(repeats):
    image = item.image.rotate(random_degree, expand=True)
    detection = detect_mode(image, mode)  # mode in ['head', 'person', 'halfbody']
    cropped = image.crop(detection)
    bg_image = BackgroundImageSet().random_image()
    new_image = paste_cropped_on_background(cropped, bg_image)
    yield ImageItem(new_image, updated_meta)
```
"""
    },
    {
        "category": "基础操作",
        "name": "ProgressBarAction",
        "description": "在图像处理流水线中显示进度条，提供处理进度反馈。",
        "parameters": [
            {
                "name": "total",
                "type": "整数或None",
                "default": "None",
                "description": "图像总数，用于设置进度条总步数。若为 None 则动态计算。"
            }
        ],
        "call_example": "action = ProgressBarAction(total=100)\nfor item in action.iter_from(items): ...",
        "notes": "通常用于包装其他 Action 的迭代器，适合长时间处理任务。",
        "implementation": """
依赖库：tqdm 模块。
实现步骤：
1. 初始化 tqdm 进度条，设置 total 参数。
2. 遍历输入迭代器，yield 输出每张图像，同时更新进度条。
伪代码：
```python
for item in tqdm(iter_, total=total):
    yield item
```
"""
    },
    {
        "category": "图像对齐",
        "name": "AlignMaxSizeAction",
        "description": "调整图像，使其最大边不超过指定尺寸，保持宽高比。",
        "parameters": [
            {
                "name": "max_size",
                "type": "整数",
                "default": "无",
                "description": "最大边长（像素），必填参数，决定输出图像的最大尺寸。"
            }
        ],
        "call_example": "action = AlignMaxSizeAction(max_size=1024)\nprocessed_item = action.process(item)",
        "notes": "按比例缩放图像，适合统一图像尺寸。建议设置合理的 max_size 以平衡质量和性能。",
        "implementation": """
依赖库：PIL 的 Image 模块。
实现步骤：
1. 获取图像宽高，计算最大边（max(width, height)）。
2. 若最大边大于 max_size，计算缩放比例（max_size / max_edge）。
3. 调用 image.resize 调整尺寸，保持宽高比。
4. 返回新的 ImageItem。
伪代码：
```python
ms = max(image.width, image.height)
if ms > max_size:
    r = ms / max_size
    image = image.resize((int(image.width / r), int(image.height / r)))
return ImageItem(image, item.meta)
```
"""
    },
    {
        "category": "图像对齐",
        "name": "AlignMinSizeAction",
        "description": "调整图像，使其最小边不小于指定尺寸，保持宽高比。",
        "parameters": [
            {
                "name": "min_size",
                "type": "整数",
                "default": "无",
                "description": "最小边长（像素），必填参数，决定输出图像的最小尺寸。"
            }
        ],
        "call_example": "action = AlignMinSizeAction(min_size=512)\nprocessed_item = action.process(item)",
        "notes": "按比例缩放图像，适合确保图像达到最低分辨率要求。",
        "implementation": """
依赖库：PIL 的 Image 模块。
实现步骤：
1. 获取图像宽高，计算最小边（min(width, height)）。
2. 若最小边小于 min_size，计算缩放比例（min_size / min_edge）。
3. 调用 image.resize 调整尺寸，保持宽高比。
4. 返回新的 ImageItem。
Pseudo code:
```python
ms = min(image.width, image.height)
if ms < min_size:
    r = min_size / ms
    image = image.resize((int(image.width * r), int(image.height * r)))
return ImageItem(image, item.meta)
```
"""
    },
    {
        "category": "图像对齐",
        "name": "AlignMaxAreaAction",
        "description": "调整图像，使其面积不超过指定值，保持宽高比。",
        "parameters": [
            {
                "name": "size",
                "type": "整数",
                "default": "无",
                "description": "面积的平方根（像素），必填参数，决定输出图像的最大面积。"
            }
        ],
        "call_example": "action = AlignMaxAreaAction(size=1000)\nprocessed_item = action.process(item)",
        "notes": "按面积比例缩放图像，适合限制图像文件大小。",
        "implementation": """
依赖库：PIL 的 Image 模块、math 模块。
实现步骤：
1. 计算当前图像面积（width * height）。
2. 若面积大于 size**2，计算缩放比例（size / sqrt(area)）。
3. 调用 image.resize 调整尺寸，保持宽高比。
4. 返回新的 ImageItem。
Pseudo code:
```python
if size**2 < image.width * image.height:
    r = ((image.width * image.height) / (size**2))**0.5
    image = image.resize((int(image.width / r), int(image.height / r)))
return ImageItem(image, item.meta)
```
"""
    },
    {
        "category": "图像对齐",
        "name": "PaddingAlignAction",
        "description": "通过填充将图像对齐到指定尺寸，保持宽高比。",
        "parameters": [
            {
                "name": "size",
                "type": "元组",
                "default": "无",
                "description": "目标尺寸 (width, height)，必填参数，决定输出图像的固定尺寸。"
            },
            {
                "name": "color",
                "type": "字符串",
                "default": "'white'",
                "description": "填充颜色，用于填充空白区域。支持 'white'、'black' 等颜色名。"
            }
        ],
        "call_example": "action = PaddingAlignAction(size=(512, 512), color='black')\nprocessed_item = action.process(item)",
        "notes": "先缩放图像（保持宽高比），再填充到目标尺寸。适合生成统一尺寸的图像。",
        "implementation": """
依赖库：PIL 的 Image 模块、waifuc.data.load_image。
实现步骤：
1. 加载图像为 RGBA 格式，确保透明度支持。
2. 计算缩放比例（min(target_width/width, target_height/height)），缩放图像。
3. 创建目标尺寸的新画布，填充指定 color。
4. 将缩放后的图像居中粘贴到画布上。
5. 返回新的 ImageItem。
Pseudo code:
```python
image = load_image(item.image, mode='RGBA')
r = min(target_width/image.width, target_height/image.height)
resized = image.resize((int(image.width * r), int(image.height * r)))
new_image = Image.new('RGBA', size, color)
new_image.paste(resized, center_position)
return ImageItem(new_image.convert(item.image.mode), item.meta)
```
"""
    },
    {
        "category": "角色一致性过滤",
        "name": "CCIPAction",
        "description": "使用 CCIP 模型过滤角色图像，确保数据集中的角色一致性，适合清理杂乱数据集。",
        "parameters": [
            {
                "name": "init_source",
                "type": "迭代器",
                "default": "None",
                "description": "初始图像源，用于提供参考图像。若为 None 则动态聚类。"
            },
            {
                "name": "min_val_count",
                "type": "整数",
                "default": "15",
                "description": "触发聚类的最小图像数量，决定何时开始一致性检查。"
            },
            {
                "name": "step",
                "type": "整数",
                "default": "5",
                "description": "每隔多少张图像进行一次聚类，控制聚类频率。"
            },
            {
                "name": "ratio_threshold",
                "type": "浮点数",
                "default": "0.6",
                "description": "聚类中主类的比例阈值，决定主类的最小占比，取值 0 到 1。"
            },
            {
                "name": "min_clu_dump_ratio",
                "type": "浮点数",
                "default": "0.3",
                "description": "聚类转储的最小比例阈值，决定是否接受聚类结果，取值 0 到 1。"
            },
            {
                "name": "cmp_threshold",
                "type": "浮点数",
                "default": "0.5",
                "description": "特征比较的匹配阈值，决定图像相似度标准，取值 0 到 1。"
            },
            {
                "name": "eps",
                "type": "浮点数或None",
                "default": "None",
                "description": "聚类参数，控制 OPTICS 聚类的邻域距离。若为 None 则使用默认值。"
            },
            {
                "name": "min_samples",
                "type": "整数或None",
                "default": "None",
                "description": "聚类参数，控制 OPTICS 聚类的最小样本数。若为 None 则使用默认值。"
            },
            {
                "name": "model",
                "type": "字符串",
                "default": "'ccip-caformer-24-randaug-pruned'",
                "description": "CCIP 模型名称，决定使用的特征提取模型。"
            },
            {
                "name": "threshold",
                "type": "浮点数或None",
                "default": "None",
                "description": "相似度阈值，若为 None 则使用模型默认值。"
            }
        ],
        "call_example": "action = CCIPAction(min_val_count=10, step=5)\nfor filtered_item in action.iter(item): ...",
        "notes": "适用于大数据集，依赖 imgutils.metrics.ccip_* 函数。处理大型数据集时可能需要调整 step 和 threshold 参数以优化性能。",
        "implementation": """
依赖库：waifuc.metrics 的 ccip_extract_feature、ccip_clustering、ccip_batch_differences，numpy。
实现步骤：
1. 初始化状态机（CCIPStatus），存储图像特征和聚类状态。
2. 若提供 init_source，加载参考图像特征，进入 INFER 状态。
3. 对每张输入图像，调用 ccip_extract_feature 提取特征。
4. 每 step 张图像，调用 ccip_clustering（OPTICS 算法）进行聚类。
5. 检查主类比例是否大于 ratio_threshold，若满足则保留主类图像。
6. 使用 ccip_batch_differences 计算特征差异，过滤不一致图像。
Pseudo code:
```python
if not init_source:
    items.append(item)
    feats.append(ccip_extract_feature(item.image))
    if len(items) >= min_val_count:
        clu_ids = ccip_clustering(feats, method='optics')
        if main_cluster_ratio > ratio_threshold:
            yield main_cluster_items
else:
    for item in init_source:
        feats.append(ccip_extract_feature(item.image))
    for item in input:
        if ccip_batch_differences(feat, feats) <= threshold:
            yield item
```
"""
    },
    {
        "category": "动画帧拆分",
        "name": "FrameSplitAction",
        "description": "将动画图像（如 GIF）拆分为单帧图像，生成独立的图像文件。",
        "parameters": [],
        "call_example": "action = FrameSplitAction()\nfor frame_item in action.iter(item): ...",
        "notes": "为每帧生成带帧编号的文件名（如 'filename_frame_0.png'）。若图像不是动画则直接返回原图。",
        "implementation": """
依赖库：PIL 的 Image 模块。
实现步骤：
1. 检查图像是否为动画（hasattr(image, 'n_frames')）。
2. 若不是动画，直接 yield 原 ImageItem。
3. 遍历每帧（image.seek(i)），复制帧图像。
4. 更新 meta['filename']，附加帧编号，生成新的 ImageItem。
Pseudo code:
```python
if not hasattr(image, 'n_frames') or image.n_frames == 1:
    yield item
else:
    for i in range(image.n_frames):
        image.seek(i)
        frame_image = image.copy()
        meta = {**item.meta, 'filename': f'{filename}_frame_{i}{ext}'}
        yield ImageItem(frame_image, meta)
```
"""
    },
    {
        "category": "头部处理",
        "name": "HeadCutOutAction",
        "description": "裁剪出不包含头部（人脸）的图像区域，用于去除面部信息。",
        "parameters": [
            {
                "name": "kp_threshold",
                "type": "浮点数",
                "default": "0.3",
                "description": "关键点置信度阈值，决定姿态估计的关键点有效性，取值 0 到 1。"
            },
            {
                "name": "level",
                "type": "字符串",
                "default": "'s'",
                "description": "人脸检测模型级别，决定检测精度和速度。支持 's'（小）、'm'（中）、'l'（大）。"
            },
            {
                "name": "version",
                "type": "字符串",
                "default": "'v1.4'",
                "description": "人脸检测模型版本，决定使用的模型迭代。"
            },
            {
                "name": "max_infer_size",
                "type": "整数",
                "default": "640",
                "description": "推理图像最大尺寸（像素），决定检测时的输入分辨率。"
            },
            {
                "name": "conf_threshold",
                "type": "浮点数",
                "default": "0.25",
                "description": "置信度阈值，决定检测结果的最小可信度，取值 0 到 1。"
            },
            {
                "name": "iou_threshold",
                "type": "浮点数",
                "default": "0.7",
                "description": "IOU 阈值，决定重叠区域的过滤标准，取值 0 到 1。"
            }
        ],
        "call_example": "action = HeadCutOutAction(kp_threshold=0.3, level='s')\nfor cutout_item in action.iter(item): ...",
        "notes": "依赖姿态估计（dwpose_estimate）和人脸检测（detect_faces），可能因检测失败无输出。建议调整 kp_threshold 和 conf_threshold 以优化效果。",
        "implementation": """
依赖库：waifuc.detect（detect_faces）、waifuc.pose（dwpose_estimate）。
实现步骤：
1. 调用 dwpose_estimate 获取姿态关键点，提取身体关键点。
2. 调用 detect_faces 检测人脸区域，获取边界框。
3. 根据人脸位置，定义四个裁剪区域（左、右、上、下）。
4. 计算每个区域内的有效关键点数量，选择关键点最多的区域。
5. 裁剪选定区域，生成新的 ImageItem。
Pseudo code:
```python
poses = dwpose_estimate(image)
faces = detect_faces(image, level, version, max_infer_size, conf_threshold, iou_threshold)
if faces:
    crop_areas = [left_area, top_area, right_area, bottom_area]
    max_area = select_area_with_max_keypoints(crop_areas, poses.body, kp_threshold)
    yield ImageItem(image.crop(max_area), item.meta)
```
"""
    },
    {
        "category": "头部处理",
        "name": "HeadCoverAction",
        "description": "覆盖图像中的头部区域，用于隐私保护或数据脱敏。",
        "parameters": [
            {
                "name": "color",
                "type": "字符串",
                "default": "'random'",
                "description": "覆盖颜色，决定头部区域的填充颜色。支持 'random'（随机颜色）或具体颜色（如 'blue'）。"
            },
            {
                "name": "scale",
                "type": "浮点数或元组",
                "default": "0.8",
                "description": "覆盖区域缩放比例，决定覆盖区域相对于检测区域的大小。取值大于 0，或元组 (min, max) 表示随机范围。"
            },
            {
                "name": "level",
                "type": "字符串",
                "default": "'s'",
                "description": "头部检测模型级别，决定检测精度和速度。支持 's'、'm'、'l'。"
            },
            {
                "name": "max_infer_size",
                "type": "整数",
                "default": "640",
                "description": "推理图像最大尺寸（像素），决定检测时的输入分辨率。"
            },
            {
                "name": "conf_threshold",
                "type": "浮点数",
                "default": "0.3",
                "description": "置信度阈值，决定检测结果的最小可信度，取值 0 到 1。"
            },
            {
                "name": "iou_threshold",
                "type": "浮点数",
                "default": "0.7",
                "description": "IOU 阈值，决定重叠区域的过滤标准，取值 0 到 1。"
            }
        ],
        "call_example": "action = HeadCoverAction(color='blue', scale=0.8)\ncovered_item = action.process(item)",
        "notes": "使用随机颜色或指定颜色覆盖头部，适合隐私保护场景。建议调整 scale 参数以控制覆盖范围。",
        "implementation": """
依赖库：waifuc.detect（detect_heads）、waifuc.operate（censor_areas）、random。
实现步骤：
1. 调用 detect_heads 检测头部区域，获取边界框。
2. 对每个边界框，计算中心点和缩放后的尺寸（根据 scale 参数）。
3. 若 color 为 'random'，生成随机颜色；否则使用指定颜色。
4. 调用 censor_areas 使用指定颜色覆盖头部区域。
5. 返回新的 ImageItem。
Pseudo code:
```python
head_areas = []
for (x0, y0, x1, y1) in detect_heads(image, level, max_infer_size, conf_threshold, iou_threshold):
    width, height = (x1 - x0) * scale, (y1 - y0) * scale
    head_areas.append(calculate_scaled_area(x0, y0, x1, y1, width, height))
color = random_color() if color == 'random' else color
image = censor_areas(image, 'color', head_areas, color)
return ImageItem(image, item.meta)
```
"""
    },
    {
        "category": "图像安全处理",
        "name": "SafetyAction",
        "description": "检查图像是否包含不适宜内容，若不安全则移除对抗噪声，保护数据安全。",
        "parameters": [
            {
                "name": "cfg_adversarial",
                "type": "字典",
                "default": "None",
                "description": "对抗噪声移除配置，包含噪声处理参数（如强度、迭代次数）。若为 None 则使用默认配置。"
            },
            {
                "name": "cfg_safe_check",
                "type": "字典",
                "default": "None",
                "description": "安全检查配置，包含内容检测参数（如置信度阈值）。若为 None 则使用默认配置。"
            }
        ],
        "call_example": "action = SafetyAction(cfg_adversarial={'strength': 0.5}, cfg_safe_check={'threshold': 0.7})\nsafe_item = action.process(item)",
        "notes": "依赖 waifuc.validate.safe_check 和 waifuc.restore.remove_adversarial_noise，可能需要预训练模型。建议根据数据集调整配置参数。",
        "implementation": """
依赖库：waifuc.validate（safe_check）、waifuc.restore（remove_adversarial_noise）。
实现步骤：
1. 调用 safe_check 检查图像安全性，返回安全标签（如 'safe'、'unsafe'）。
2. 若标签为 'unsafe'，调用 remove_adversarial_noise 处理图像，移除潜在对抗噪声。
3. 返回处理后的 ImageItem，保留原 meta 数据。
Pseudo code:
```python
safe_tag, _ = safe_check(image, **cfg_safe_check)
if safe_tag != 'safe':
    image = remove_adversarial_noise(image, **cfg_adversarial)
return ImageItem(image, item.meta)
```
"""
    },
    {
        "category": "相似图像过滤",
        "name": "FilterSimilarAction",
        "description": "使用 LPIPS 模型过滤相似或重复图像，减少数据集冗余。",
        "parameters": [
            {
                "name": "mode",
                "type": "字符串",
                "default": "'all'",
                "description": "过滤模式，决定相似性检查范围。支持 'all'（全局检查）或 'group'（按 group_id 分组检查）。"
            },
            {
                "name": "threshold",
                "type": "浮点数",
                "default": "0.45",
                "description": "LPIPS 相似度阈值，决定图像被认为是相似的标准。取值 0 到 1，值越小过滤越严格。"
            },
            {
                "name": "capacity",
                "type": "整数",
                "default": "500",
                "description": "特征缓存容量，决定存储的特征数量。取值大于 0，影响内存使用。"
            },
            {
                "name": "rtol",
                "type": "浮点数",
                "default": "5.e-2",
                "description": "相对容差，用于宽高比比较，取值大于 0。"
            },
            {
                "name": "atol",
                "type": "浮点数",
                "default": "2.e-2",
                "description": "绝对容差，用于宽高比比较，取值大于 0。"
            }
        ],
        "call_example": "action = FilterSimilarAction(mode='all', threshold=0.45)\nfor unique_item in action.iter(item): ...",
        "notes": "使用 FeatureBucket 管理特征缓存，适合大数据集去重。建议根据数据集规模调整 capacity 和 threshold。",
        "implementation": """
依赖库：waifuc.metrics（lpips_extract_feature、lpips_difference）、numpy。
实现步骤：
1. 初始化 FeatureBucket，设置 threshold 和 capacity。
2. 对每张图像，调用 lpips_extract_feature 提取特征。
3. 计算图像宽高比（height/width）。
4. 检查 FeatureBucket 中是否存在相似特征（lpips_difference <= threshold 且宽高比接近）。
5. 若无相似特征，将当前特征加入 FeatureBucket，yield 输出图像。
Pseudo code:
```python
bucket = FeatureBucket(threshold, capacity, rtol, atol)
feat = lpips_extract_feature(image)
ratio = image.height / image.width
if not bucket.check_duplicate(feat, ratio):
    bucket.add(feat, ratio)
    yield item
```
"""
    },
    {
        "category": "文件名处理",
        "name": "FileExtAction",
        "description": "更改图像文件扩展名，并可选设置保存质量，规范化文件格式。",
        "parameters": [
            {
                "name": "ext",
                "type": "字符串",
                "default": "无",
                "description": "目标扩展名，如 '.jpg' 或 '.png'，必填参数，决定输出文件格式。"
            },
            {
                "name": "quality",
                "type": "整数或None",
                "default": "None",
                "description": "保存质量，取值 0 到 100，仅对支持质量参数的格式（如 JPEG）有效。若为 None 则使用默认质量。"
            }
        ],
        "call_example": "action = FileExtAction(ext='.jpg', quality=90)\nfor renamed_item in action.iter(item): ...",
        "notes": "若输入无文件名，会生成 'untitled_<编号>.ext' 格式名称。建议明确指定 quality 以控制输出质量。",
        "implementation": """
依赖库：Python 的 os、copy 模块。
实现步骤：
1. 检查 meta['filename']，若存在则提取文件名主体，否则生成 'untitled_<编号>'。
2. 替换扩展名为指定 ext，更新 meta['filename']。
3. 若 quality 非 None，设置 meta['save_cfg']['quality']。
4. 返回新的 ImageItem。
Pseudo code:
```python
if 'filename' in item.meta:
    filebody, _ = os.path.splitext(item.meta['filename'])
    filename = f'{filebody}{ext}'
else:
    untitled += 1
    filename = f'untitled_{untitled}{ext}'
meta = copy.deepcopy(item.meta)
meta['filename'] = filename
if quality is not None:
    meta['save_cfg'] = meta.get('save_cfg', {})
    meta['save_cfg']['quality'] = quality
yield ImageItem(item.image, meta)
```
"""
    },
    {
        "category": "文件名处理",
        "name": "FileOrderAction",
        "description": "按顺序重命名图像文件，生成递增编号的文件名。",
        "parameters": [
            {
                "name": "ext",
                "type": "字符串",
                "default": "'.png'",
                "description": "文件扩展名，如 '.png' 或 '.jpg'，决定输出文件格式。"
            }
        ],
        "call_example": "action = FileOrderAction(ext='.png')\nfor ordered_item in action.iter(item): ...",
        "notes": "若输入无文件名且未指定 ext，会抛出错误。建议明确指定 ext 以避免异常。",
        "implementation": """
依赖库：无。
实现步骤：
1. 维护内部计数器 _current，初始化为 0。
2. 检查 meta['filename']，若存在则提取原扩展名，否则使用指定 ext。
3. 生成新文件名（_current + ext），_current 自增。
4. 更新 meta['filename']，返回新的 ImageItem。
Pseudo code:
```python
_current += 1
if 'filename' in item.meta:
    _, ext = os.path.splitext(item.meta['filename'])
    new_filename = f'{_current}{ext or specified_ext}'
else:
    new_filename = f'{_current}{specified_ext}'
yield ImageItem(item.image, {**item.meta, 'filename': new_filename})
```
"""
    },
    {
        "category": "图像选择",
        "name": "FirstNSelectAction",
        "description": "选择前 N 张图像，限制输出数量。",
        "parameters": [
            {
                "name": "n",
                "type": "整数",
                "default": "无",
                "description": "选择数量，必填参数，取值大于 0，决定输出的最大图像数。"
            }
        ],
        "call_example": "action = FirstNSelectAction(n=10)\nfor selected_item in action.iter(item): ...",
        "notes": "继承 ProgressBarAction，支持进度条显示。适合快速抽取部分数据。",
        "implementation": """
依赖库：waifuc（ProgressBarAction、ActionStop）。
实现步骤：
1. 维护计数器 _passed，初始化为 0。
2. 对每张图像，若 _passed < n，则 yield 输出，_passed 自增。
3. 若 _passed >= n，抛出 ActionStop 异常终止迭代。
Pseudo code:
```python
if _passed < n:
    yield item
    _passed += 1
else:
    raise ActionStop
```
"""
    },
    {
        "category": "图像选择",
        "name": "SliceSelectAction",
        "description": "按切片方式选择图像，类似 Python 切片语法。",
        "parameters": [
            {
                "name": "*args",
                "type": "变长参数",
                "default": "无",
                "description": "切片参数（start, stop, step），类似 Python 切片语法。start/stop 为图像索引，step 为步长。"
            }
        ],
        "call_example": "action = SliceSelectAction(5, 10, 2)\nfor sliced_item in action.iter(item): ...",
        "notes": "支持灵活的切片选择，如 5:10:2 表示第 6 到 10 张图像，每隔 2 张选一张。",
        "implementation": """
依赖库：math 模块、waifuc（ProgressBarAction、ActionStop）。
实现步骤：
1. 解析切片参数，设置 start、stop、step（默认 start=0, step=1）。
2. 维护计数器 _current，初始化为 0。
3. 对每张图像，若 _current 在切片范围内（start <= _current < stop 且 (_current - start) % step == 0），yield 输出。
4. 若超出 stop，抛出 ActionStop 终止迭代。
Pseudo code:
```python
if _current < stop and _current >= start and (_current - start) % step == 0:
    yield item
_current += 1
if _current > max:
    raise ActionStop
```
"""
    },
    {
        "category": "调试",
        "name": "ArrivalAction",
        "description": "显示图像处理进度条，用于调试工作流。",
        "parameters": [
            {
                "name": "name",
                "type": "字符串",
                "default": "无",
                "description": "进度条名称，用于区分不同调试点，必填参数。"
            },
            {
                "name": "total",
                "type": "整数或None",
                "default": "None",
                "description": "图像总数，决定进度条总步数。若为 None 则动态计算。"
            }
        ],
        "call_example": "action = ArrivalAction(name='debug', total=100)\nfor debug_item in action.iter(item): ...",
        "notes": "继承 ProgressBarAction，仅用于调试，不会修改图像数据。",
        "implementation": """
依赖库：waifuc（ProgressBarAction）、tqdm。
实现步骤：
1. 初始化 ProgressBarAction，设置 total 参数。
2. 对每张图像，直接 yield 输出，同时更新进度条。
Pseudo code:
```python
yield item  # 原样输出，同时通过 ProgressBarAction 更新进度条
```
"""
    },
    {
        "category": "过滤器",
        "name": "NoMonochromeAction",
        "description": "过滤掉单色或灰度图像，保留彩色图像。",
        "parameters": [],
        "call_example": "action = NoMonochromeAction()\nif action.check(item): yield item",
        "notes": "依赖 waifuc.validate.is_monochrome，可能因图像特性误判。适合清理单色数据集。",
        "implementation": """
依赖库：waifuc.validate（is_monochrome）。
实现步骤：
1. 调用 is_monochrome 检查图像是否为单色或灰度。
2. 若返回 False（非单色），则通过检查，yield 输出图像。
Pseudo code:
```python
if not is_monochrome(item.image):
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "OnlyMonochromeAction",
        "description": "仅保留单色或灰度图像，过滤彩色图像。",
        "parameters": [],
        "call_example": "action = OnlyMonochromeAction()\nif action.check(item): yield item",
        "notes": "与 NoMonochromeAction 相反，用于提取单色图像。可能因图像特性误判。",
        "implementation": """
依赖库：waifuc.validate（is_monochrome）。
实现步骤：
1. 调用 is_monochrome 检查图像是否为单色或灰度。
2. 若返回 True（单色），则通过检查，yield 输出图像。
Pseudo code:
```python
if is_monochrome(item.image):
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "ClassFilterAction",
        "description": "根据图像类别（如插画、动画）过滤图像，保留指定类别。",
        "parameters": [
            {
                "name": "classes",
                "type": "列表",
                "default": "无",
                "description": "保留的类别，如 ['illustration', 'anime']，必填参数。支持 'illustration'、'bangumi'、'comic'、'3d'。"
            },
            {
                "name": "threshold",
                "type": "浮点数或None",
                "default": "None",
                "description": "分类置信度阈值，决定类别判断的最小可信度，取值 0 到 1。若为 None 则不检查置信度。"
            }
        ],
        "call_example": "action = ClassFilterAction(classes=['illustration'], threshold=0.5)\nif action.check(item): yield item",
        "notes": "依赖 waifuc.validate.anime_classify，需要预训练模型。建议设置 threshold 以提高准确性。",
        "implementation": """
依赖库：waifuc.validate（anime_classify）。
实现步骤：
1. 调用 anime_classify 获取图像类别和置信度。
2. 检查类别是否在 classes 列表中，且置信度是否高于 threshold（若指定）。
3. 若通过检查，yield 输出图像。
Pseudo code:
```python
cls, score = anime_classify(item.image)
if cls in classes and (threshold is None or score >= threshold):
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "RatingFilterAction",
        "description": "根据图像评级（如 'safe'、'r15'）过滤图像，保留指定评级。",
        "parameters": [
            {
                "name": "ratings",
                "type": "列表",
                "default": "无",
                "description": "保留的评级，如 ['safe', 'r15']，必填参数。支持 'safe'、'r15'、'r18'。"
            },
            {
                "name": "threshold",
                "type": "浮点数或None",
                "default": "None",
                "description": "评级置信度阈值，决定评级判断的最小可信度，取值 0 到 1。若为 None 则不检查置信度。"
            }
        ],
        "call_example": "action = RatingFilterAction(ratings=['safe'], threshold=0.5)\nif action.check(item): yield item",
        "notes": "依赖 waifuc.validate.anime_rating，需要预训练模型。建议设置 threshold 以提高准确性。",
        "implementation": """
依赖库：waifuc.validate（anime_rating）。
实现步骤：
1. 调用 anime_rating 获取图像评级和置信度。
2. 检查评级是否在 ratings 列表中，且置信度是否高于 threshold（若指定）。
3. 若通过检查，yield 输出图像。
Pseudo code:
```python
rating, score = anime_rating(item.image)
if rating in ratings and (threshold is None or score >= threshold):
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "FaceCountAction",
        "description": "根据人脸数量过滤图像，保留符合指定数量范围的图像。",
        "parameters": [
            {
                "name": "min_count",
                "type": "整数或None",
                "default": "None",
                "description": "最小人脸数，决定人脸数量下限。若为 None 则无下限。"
            },
            {
                "name": "max_count",
                "type": "整数或None",
                "default": "None",
                "description": "最大人脸数，决定人脸数量上限。若为 None 则无上限。"
            },
            {
                "name": "level",
                "type": "字符串",
                "default": "'s'",
                "description": "人脸检测模型级别，决定检测精度和速度。支持 's'、'm'、'l'。"
            },
            {
                "name": "version",
                "type": "字符串",
                "default": "'v1.4'",
                "description": "人脸检测模型版本，决定使用的模型迭代。"
            },
            {
                "name": "conf_threshold",
                "type": "浮点数",
                "default": "0.25",
                "description": "置信度阈值，决定检测结果的最小可信度，取值 0 到 1。"
            },
            {
                "name": "iou_threshold",
                "type": "浮点数",
                "default": "0.7",
                "description": "IOU 阈值，决定重叠区域的过滤标准，取值 0 到 1。"
            }
        ],
        "call_example": "action = FaceCountAction(min_count=1, max_count=3, level='s')\nif action.check(item): yield item",
        "notes": "依赖 waifuc.detect.detect_faces，可能受检测精度影响。建议调整 conf_threshold 和 iou_threshold 以优化效果。",
        "implementation": """
依赖库：waifuc.detect（detect_faces）。
实现步骤：
1. 调用 detect_faces 获取人脸检测结果，返回边界框列表。
2. 统计人脸数量（len(detection)）。
3. 检查数量是否在 min_count 和 max_count 范围内（若指定）。
4. 若通过检查，yield 输出图像。
Pseudo code:
```python
detection = detect_faces(image, level, version, conf_threshold, iou_threshold)
count = len(detection)
if (min_count is None or count >= min_count) and (max_count is None or count <= max_count):
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "HeadCountAction",
        "description": "根据头部数量过滤图像，保留符合指定数量范围的图像。",
        "parameters": [
            {
                "name": "min_count",
                "type": "整数或None",
                "default": "None",
                "description": "最小头部数，决定头部数量下限。若为 None 则无下限。"
            },
            {
                "name": "max_count",
                "type": "整数或None",
                "default": "None",
                "description": "最大头部数，决定头部数量上限。若为 None 则无上限。"
            },
            {
                "name": "level",
                "type": "字符串",
                "default": "'s'",
                "description": "头部检测模型级别，决定检测精度和速度。支持 's'、'm'、'l'。"
            },
            {
                "name": "conf_threshold",
                "type": "浮点数",
                "default": "0.3",
                "description": "置信度阈值，决定检测结果的最小可信度，取值 0 到 1。"
            },
            {
                "name": "iou_threshold",
                "type": "浮点数",
                "default": "0.7",
                "description": "IOU 阈值，决定重叠区域的过滤标准，取值 0 到 1。"
            }
        ],
        "call_example": "action = HeadCountAction(min_count=1, max_count=2, level='s')\nif action.check(item): yield item",
        "notes": "依赖 waifuc.detect.detect_heads，可能受检测精度影响。建议调整 conf_threshold 以优化效果。",
        "implementation": """
依赖库：waifuc.detect（detect_heads）。
实现步骤：
1. 调用 detect_heads 获取头部检测结果，返回边界框列表。
2. 统计头部数量（len(detection)）。
3. 检查数量是否在 min_count 和 max_count 范围内（若指定）。
4. 若通过检查，yield 输出图像。
Pseudo code:
```python
detection = detect_heads(image, level, conf_threshold, iou_threshold)
count = len(detection)
if (min_count is None or count >= min_count) and (max_count is None or count <= max_count):
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "PersonRatioAction",
        "description": "根据人物在图像中的面积占比过滤图像，保留符合占比要求的图像。",
        "parameters": [
            {
                "name": "ratio",
                "type": "浮点数",
                "default": "0.4",
                "description": "人物面积占比阈值，决定人物区域占图像总面积的最小比例，取值 0 到 1。"
            },
            {
                "name": "level",
                "type": "字符串",
                "default": "'m'",
                "description": "人物检测模型级别，决定检测精度和速度。支持 's'、'm'、'l'。"
            },
            {
                "name": "version",
                "type": "字符串",
                "default": "'v1.1'",
                "description": "人物检测模型版本，决定使用的模型迭代。"
            },
            {
                "name": "conf_threshold",
                "type": "浮点数",
                "default": "0.3",
                "description": "置信度阈值，决定检测结果的最小可信度，取值 0 到 1。"
            },
            {
                "name": "iou_threshold",
                "type": "浮点数",
                "default": "0.5",
                "description": "IOU 阈值，决定重叠区域的过滤标准，取值 0 到 1。"
            }
        ],
        "call_example": "action = PersonRatioAction(ratio=0.5, level='m')\nif action.check(item): yield item",
        "notes": "仅当检测到一个人物时有效，依赖 waifuc.detect.detect_person。建议调整 ratio 和 conf_threshold 以优化效果。",
        "implementation": """
依赖库：waifuc.detect（detect_person）。
实现步骤：
1. 调用 detect_person 获取人物检测结果，返回边界框列表。
2. 若检测到一个人物，计算人物区域面积（(x1-x0)*(y1-y0)）。
3. 计算面积占比（人物面积 / 图像总面积）。
4. 若占比大于等于 ratio，则通过检查，yield 输出图像。
Pseudo code:
```python
detections = detect_person(image, level, version, conf_threshold, iou_threshold)
if len(detections) == 1:
    (x0, y0, x1, y1), _, _ = detections[0]
    if (x1 - x0) * (y1 - y0) >= ratio * image.width * image.height:
        yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "MinSizeFilterAction",
        "description": "过滤掉最小边长小于指定值的图像，确保输出图像达到最低分辨率。",
        "parameters": [
            {
                "name": "min_size",
                "type": "整数",
                "default": "无",
                "description": "最小边长（像素），必填参数，决定输出图像的最小尺寸。"
            }
        ],
        "call_example": "action = MinSizeFilterAction(min_size=512)\nif action.check(item): yield item",
        "notes": "检查图像的最小边长，常用于去除低分辨率图像。建议根据任务需求设置 min_size。",
        "implementation": """
依赖库：无。
实现步骤：
1. 获取图像宽高，计算最小边（min(width, height)）。
2. 若最小边大于等于 min_size，则通过检查，yield 输出图像。
Pseudo code:
```python
if min(image.width, image.height) >= min_size:
    yield item
```
"""
    },
    {
        "category": "过滤器",
        "name": "MinAreaFilterAction",
        "description": "过滤掉面积（宽*高）小于指定值的图像，确保输出图像达到最低面积要求。",
        "parameters": [
            {
                "name": "min_size",
                "type": "整数",
                "default": "无",
                "description": "面积的平方根（像素），必填参数，决定输出图像的最小面积。"
            }
        ],
        "call_example": "action = MinAreaFilterAction(min_size=1000)\nif action.check(item): yield item",
        "notes": "检查图像面积的平方根，常用于去除小尺寸图像。建议根据任务需求设置 min_size。",
        "implementation": """
依赖库：无。
实现步骤：
1. 计算图像面积（width * height）。
2. 计算面积平方根（sqrt(area)）。
3. 若平方根大于等于 min_size，则通过检查，yield 输出图像。
Pseudo code:
```python
if (image.width * image.height)**0.5 >= min_size:
    yield item
```
"""
    },
    {
        "category": "图像分割",
        "name": "PersonSplitAction",
        "description": "将图像中的每个人物分割成单独的图像，生成独立的人物图像。",
        "parameters": [
            {
                "name": "keep_original",
                "type": "布尔值",
                "default": "False",
                "description": "是否保留原始图像。若为 True，则同时输出原图和分割图像。"
            },
            {
                "name": "level",
                "type": "字符串",
                "default": "'m'",
                "description": "人物检测模型级别，决定检测精度和速度。支持 's'、'm'、'l'。"
            },
            {
                "name": "version",
                "type": "字符串",
                "default": "'v1.1'",
                "description": "人物检测模型版本，决定使用的模型迭代。"
            },
            {
                "name": "conf_threshold",
                "type": "浮点数",
                "default": "0.3",
                "description": "置信度阈值，决定检测结果的最小可信度，取值 0 到 1。"
            },
            {
                "name": "iou_threshold",
                "type": "浮点数",
                "default": "0.5",
                "description": "IOU 阈值，决定重叠区域的过滤标准，取值 0 到 1。"
            },
            {
                "name": "keep_origin_tags",
                "type": "布尔值",
                "default": "False",
                "description": "是否保留原始图像的标签。若为 False，则分割图像不继承原标签。"
            }
        ],
        "call_example": "action = PersonSplitAction(keep_original=True, level='m')\nfor split_item in action.iter(item): ...",
        "notes": "依赖 waifuc.detect.detect_person，可能因检测失败无输出。建议调整 conf_threshold 和 iou_threshold 以优化效果。",
        "implementation": """
依赖库：waifuc.detect（detect_person）。
实现步骤：
1. 调用 detect_person 获取人物检测结果，返回边界框列表。
2. 若 keep_original 为 True，yield 输出原始 ImageItem。
3. 对每个检测到的人物，裁剪边界框区域，生成新的 ImageItem。
4. 更新 meta['filename']（附加人物编号），若 keep_origin_tags 为 False 则移除原标签。
Pseudo code:
```python
detection = detect_person(image, level, version, conf_threshold, iou_threshold)
if keep_original:
    yield item
for i, (area, type_, score) in enumerate(detection):
    new_meta = {**item.meta, 'crop': {'type': type_, 'score': score}}
    if not keep_origin_tags:
        new_meta.pop('tags', None)
    new_meta['filename'] = f'{filebody}_person{i}{ext}'
    yield ImageItem(image.crop(area), new_meta)
```
"""
    },
    {
        "category": "图像分割",
        "name": "ThreeStageSplitAction",
        "description": "进行全身、半身、头部（可选眼睛）的三阶段分割，生成多层次的图像裁剪。",
        "parameters": [
            {
                "name": "person_conf",
                "type": "字典",
                "default": "{}",
                "description": "全身检测配置，包含检测参数（如置信度阈值）。若为空则使用默认配置。"
            },
            {
                "name": "halfbody_conf",
                "type": "字典",
                "default": "{}",
                "description": "半身检测配置，包含检测参数。若为空则使用默认配置。"
            },
            {
                "name": "head_conf",
                "type": "字典",
                "default": "{}",
                "description": "头部检测配置，包含检测参数。若为空则使用默认配置。"
            },
            {
                "name": "eye_conf",
                "type": "字典",
                "default": "{}",
                "description": "眼睛检测配置，包含检测参数。若为空则使用默认配置。"
            },
            {
                "name": "head_scale",
                "type": "浮点数",
                "default": "1.5",
                "description": "头部裁剪缩放比例，决定头部区域放大倍数，取值大于 0。"
            },
            {
                "name": "eye_scale",
                "type": "浮点数",
                "default": "2.4",
                "description": "眼睛裁剪缩放比例，决定眼睛区域放大倍数，取值大于 0。"
            },
            {
                "name": "split_eyes",
                "type": "布尔值",
                "default": "False",
                "description": "是否分割眼睛区域。若为 True，则额外生成眼睛裁剪图像。"
            },
            {
                "name": "split_person",
                "type": "布尔值",
                "default": "True",
                "description": "是否分割全身区域。若为 False，则直接使用原图进行后续分割。"
            },
            {
                "name": "keep_origin_tags",
                "type": "布尔值",
                "default": "False",
                "description": "是否保留原始图像的标签。若为 False，则分割图像不继承原标签。"
            }
        ],
        "call_example": "action = ThreeStageSplitAction(split_eyes=True, head_scale=1.5)\nfor split_item in action.iter(item): ...",
        "notes": "依赖 waifuc.detect 的多级检测函数（detect_person、detect_halfbody、detect_heads、detect_eyes），可能因检测失败无输出。建议调整 scale 参数以优化裁剪效果。",
        "implementation": """
依赖库：waifuc.detect（detect_person、detect_halfbody、detect_heads、detect_eyes）。
实现步骤：
1. 若 split_person 为 True，调用 detect_person 分割全身区域，否则使用原图。
2. 对每个全身图像，调用 detect_halfbody 获取半身区域，裁剪并生成 ImageItem。
3. 对每个全身图像，调用 detect_heads 获取头部区域，按 head_scale 缩放后裁剪。
4. 若 split_eyes 为 True，对每个头部图像调用 detect_eyes，按 eye_scale 缩放后裁剪。
5. 更新 meta['filename'] 和 meta['crop']，若 keep_origin_tags 为 False 则移除原标签。
Pseudo code:
```python
for person_item in (detect_person(image, **person_conf) if split_person else [item]):
    yield person_item
    halfbody = detect_halfbody(person_item.image, **halfbody_conf)
    if halfbody:
        yield ImageItem(person_item.image.crop(halfbody[0]), updated_meta)
    heads = detect_heads(person_item.image, **head_conf)
    if heads:
        head_image = person_item.image.crop(scale_area(heads[0], head_scale))
        yield ImageItem(head_image, updated_meta)
        if split_eyes:
            eyes = detect_eyes(head_image, **eye_conf)
            for eye in eyes:
                yield ImageItem(head_image.crop(scale_area(eye, eye_scale)), updated_meta)
```
"""
    },
    {
        "category": "标签处理",
        "name": "TaggingAction",
        "description": "使用指定模型为图像生成标签，添加语义信息。",
        "parameters": [
            {
                "name": "method",
                "type": "字符串",
                "default": "'wd14_v3_swinv2'",
                "description": "标签模型名称，决定使用的标签生成模型。支持 'deepdanbooru'、'wd14_vit'、'wd14_convnextv2' 等。"
            },
            {
                "name": "force",
                "type": "布尔值",
                "default": "False",
                "description": "是否强制重新生成标签。若为 False 且已有标签，则跳过处理。"
            },
            {
                "name": "general_threshold",
                "type": "浮点数",
                "default": "0.35",
                "description": "通用标签置信度阈值，决定保留标签的最小可信度，取值 0 到 1。（仅部分模型支持）"
            },
            {
                "name": "character_threshold",
                "type": "浮点数",
                "default": "0.85",
                "description": "角色标签置信度阈值，决定保留角色标签的最小可信度，取值 0 到 1。（仅部分模型支持）"
            }
        ],
        "call_example": "action = TaggingAction(method='deepdanbooru', force=True, general_threshold=0.5)\ntagged_item = action.process(item)",
        "notes": "支持多种标签模型（如 DeepDanbooru、WD14），需要预训练模型。建议根据任务调整 threshold 参数。",
        "implementation": """
依赖库：waifuc.tagging（get_deepdanbooru_tags、get_wd14_tags、get_mldanbooru_tags）。
实现步骤：
1. 检查 meta['tags']，若存在且 force=False，则直接返回原 ImageItem。
2. 根据 method 选择标签模型，调用对应函数生成标签。
3. 将生成的标签存入 meta['tags']，返回新的 ImageItem。
Pseudo code:
```python
if 'tags' in item.meta and not force:
    return item
tags = _TAGGING_METHODS[method](image, **kwargs)
return ImageItem(item.image, {**item.meta, 'tags': tags})
```
"""
    },
    {
        "category": "标签处理",
        "name": "TagFilterAction",
        "description": "根据标签过滤图像，保留或丢弃包含特定标签的图像。",
        "parameters": [
            {
                "name": "tags",
                "type": "列表或字典",
                "default": "无",
                "description": "要过滤的标签，列表表示保留的标签，字典表示标签及其最小置信度。必填参数。"
            },
            {
                "name": "method",
                "type": "字符串",
                "default": "'wd14_convnextv2'",
                "description": "标签模型名称，用于生成标签。支持 'wd14_convnextv2'、'deepdanbooru' 等。"
            },
            {
                "name": "reversed",
                "type": "布尔值",
                "default": "False",
                "description": "是否反转过滤逻辑。若为 True，则丢弃包含指定标签的图像。"
            }
        ],
        "call_example": "action = TagFilterAction(tags=['cat'], method='wd14_vit')\nfor filtered_item in action.iter(item): ...",
        "notes": "内部使用 TaggingAction 生成标签，需预训练模型。建议明确指定 tags 以避免误过滤。",
        "implementation": """
依赖库：waifuc.tagging、TaggingAction。
实现步骤：
1. 使用 TaggingAction 生成图像标签，存入 meta['tags']。
2. 检查 meta['tags'] 是否满足 tags 参数的要求（标签存在且置信度高于阈值）。
3. 根据 reversed 参数，决定是否 yield 输出图像。
Pseudo code:
```python
item = tagger(item)
tags = item.meta['tags']
valid = all(tags.get(tag, 0.0) >= min_score for tag, min_score in tags.items())
if valid != reversed:
    yield item
```
"""
    },
    {
        "category": "标签处理",
        "name": "TagOverlapDropAction",
        "description": "移除重叠或相似的标签，清理冗余标签。",
        "parameters": [],
        "call_example": "action = TagOverlapDropAction()\nprocessed_item = action.process(item)",
        "notes": "依赖 waifuc.tagging.drop_overlap_tags，适合规范化标签集。可能因语义判断移除部分有效标签。",
        "implementation": """
依赖库：waifuc.tagging（drop_overlap_tags）。
实现步骤：
1. 获取 meta['tags']（若无则为空字典）。
2. 调用 drop_overlap_tags 处理标签，去除语义重叠的标签。
3. 更新 meta['tags']，返回新的 ImageItem。
Pseudo code:
```python
tags = drop_overlap_tags(dict(item.meta.get('tags', {})))
return ImageItem(item.image, {**item.meta, 'tags': tags})
```
"""
    },
    {
        "category": "标签处理",
        "name": "TagDropAction",
        "description": "移除指定的标签，清理不需要的标签。",
        "parameters": [
            {
                "name": "tags_to_drop",
                "type": "列表",
                "default": "无",
                "description": "要移除的标签列表，如 ['tag1', 'tag2']，必填参数。"
            }
        ],
        "call_example": "action = TagDropAction(tags_to_drop=['tag1', 'tag2'])\nprocessed_item = action.process(item)",
        "notes": "直接从 meta['tags'] 中删除指定标签，适合精确清理。",
        "implementation": """
依赖库：无。
实现步骤：
1. 获取 meta['tags']（若无则为空字典）。
2. 过滤 tags，移除 tags_to_drop 中的标签。
3. 更新 meta['tags']，返回新的 ImageItem。
Pseudo code:
```python
tags = {tag: score for tag, score in item.meta.get('tags', {}).items() if tag not in tags_to_drop}
return ImageItem(item.image, {**item.meta, 'tags': tags})
```
"""
    },
    {
        "category": "标签处理",
        "name": "BlacklistedTagDropAction",
        "description": "移除黑名单中的标签，清理不符合要求的标签。",
        "parameters": [],
        "call_example": "action = BlacklistedTagDropAction()\nprocessed_item = action.process(item)",
        "notes": "依赖 waifuc.tagging.is_blacklisted，需预定义黑名单。适合内容过滤场景。",
        "implementation": """
依赖库：waifuc.tagging（is_blacklisted）。
实现步骤：
1. 获取 meta['tags']（若无则为空字典）。
2. 过滤 tags，移除 is_blacklisted 返回 True 的标签。
3. 更新 meta['tags']，返回新的 ImageItem。
Pseudo code:
```python
tags = {tag: score for tag, score in item.meta.get('tags', {}).items() if not is_blacklisted(tag)}
return ImageItem(item.image, {**item.meta, 'tags': tags})
```
"""
    },
    {
        "category": "标签处理",
        "name": "TagRemoveUnderlineAction",
        "description": "移除标签中的下划线，规范化标签格式。",
        "parameters": [],
        "call_example": "action = TagRemoveUnderlineAction()\nprocessed_item = action.process(item)",
        "notes": "将标签中的 '_' 替换为空格，适合清理格式不一致的标签。",
        "implementation": """
依赖库：waifuc.tagging（remove_underline）。
实现步骤：
1. 获取 meta['tags']（若无则为空字典）。
2. 对每个标签调用 remove_underline，替换下划线为空格。
3. 更新 meta['tags']，返回新的 ImageItem。
Pseudo code:
```python
tags = {remove_underline(tag): score for tag, score in item.meta.get('tags', {}).items()}
return ImageItem(item.image, {**item.meta, 'tags': tags})
```
"""
    }
]

class ComponentDetailDialog(QDialog):
    def __init__(self, component, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{component['name']} 详情")
        self.resize(700, 500)
        layout = QVBoxLayout()

        # 使用 QTextBrowser 显示 HTML 格式内容
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(self.format_component_html(component))
        layout.addWidget(text_browser)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def format_component_html(self, component):
        html = f"<h2>{component['name']}</h2>"
        html += f"<p><strong>类别</strong>: {component['category']}</p>"
        html += f"<p><strong>功能描述</strong>: {component['description']}</p>"

        # 参数表格
        if component['parameters']:
            html += "<h3>参数</h3>"
            html += "<table style='width:100%; border-collapse: collapse;'>"
            html += "<tr>"
            html += "<th style='border:1px solid #ddd; padding:8px; text-align:left;'>名称</th>"
            html += "<th style='border:1px solid #ddd; padding:8px; text-align:left;'>类型</th>"
            html += "<th style='border:1px solid #ddd; padding:8px; text-align:left;'>默认值</th>"
            html += "<th style='border:1px solid #ddd; padding:8px; text-align:left;'>描述</th>"
            html += "</tr>"
            for param in component['parameters']:
                html += "<tr>"
                html += f"<td style='border:1px solid #ddd; padding:8px;'>{param['name']}</td>"
                html += f"<td style='border:1px solid #ddd; padding:8px;'>{param['type']}</td>"
                html += f"<td style='border:1px solid #ddd; padding:8px;'>{param['default']}</td>"
                html += f"<td style='border:1px solid #ddd; padding:8px;'>{param['description']}</td>"
                html += "</tr>"
            html += "</table>"

        # 其他信息
        html += f"<h3>调用方法</h3><pre style='background:#f4f4f4; padding:10px;'>{component['call_example']}</pre>"
        html += f"<h3>注意事项</h3><p>{component['notes']}</p>"
        html += f"<h3>底层实现原理</h3><pre style='background:#f4f4f4; padding:10px;'>{component['implementation']}</pre>"

        return html

class ComponentListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("组件说明")
        self.resize(800, 600)
        layout = QVBoxLayout()

        # 组件列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["类别", "组件名称"])
        self.table.setRowCount(len(components))
        for i, comp in enumerate(components):
            self.table.setItem(i, 0, QTableWidgetItem(comp['category']))
            self.table.setItem(i, 1, QTableWidgetItem(comp['name']))
        self.table.cellClicked.connect(self.show_detail)
        layout.addWidget(self.table)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def show_detail(self, row, column):
        component = components[row]
        detail_dialog = ComponentDetailDialog(component, self)
        detail_dialog.exec_()