# -*- coding: utf-8 -*-
"""
清粥小菜工具箱 - ComfyUI 实用工具合集
"""

import os
import sys
import importlib
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))

# 设置 Web 目录
WEB_DIRECTORY = "./web"

print(f"[XiaoCaiTools] 初始化，加载路径: {current_dir}")

# 导入所有节点
nodes_dir = os.path.join(current_dir, "nodes")

# 添加 nodes 目录到路径
if nodes_dir not in sys.path:
    sys.path.insert(0, nodes_dir)

# 手动加载每个节点模块
def load_node_module(module_name, file_name):
    try:
        file_path = os.path.join(nodes_dir, file_name)
        if not os.path.exists(file_path):
            print(f"[XiaoCaiTools] 文件不存在: {file_path}")
            return None
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 获取模块中的所有类
        classes = {}
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type):
                classes[name] = obj
        
        print(f"[XiaoCaiTools] 加载模块 {file_name}: {list(classes.keys())}")
        return classes
    except Exception as e:
        print(f"[XiaoCaiTools] 加载模块 {file_name} 失败: {e}")
        traceback.print_exc()
        return None

# 收集所有节点类
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 定义模块文件与显示名称的映射
modules_config = [
    # (文件名, 模块名, 节点显示名称映射)
    ("image_saver.py", "image_saver", {
        "ImageSaver": "📸 图像保存(高级)",
        "ImageSaverSimple": "📸 图像保存(简单)",
    }),
    ("text_with_index.py", "text_with_index", {
        "TextWithIndex": "📊 带索引文本",
    }),
    ("simple_dynamic_text_v1.py", "simple_dynamic_text_v1", {
        "SimpleDynamicTextV1": "🎲 简单动态文本 V1",
    }),
    ("simple_dynamic_text.py", "simple_dynamic_text", {
        "SimpleDynamicText": "🎲 简单动态文本",
    }),
    ("simple_dynamic_text_concat.py", "simple_dynamic_text_concat", {
        "SimpleDynamicTextConcat": "🔗 简单动态文本连结",
    }),
    ("multi_line_text_index.py", "multi_line_text_index", {
        "MultiLineTextIndex": "📝 多行文本索引",
    }),
    ("text_list_selector.py", "text_list_selector", {
        "TextListSelector": "📋 文本列表选择器",
    }),
    ("folder_image_counter.py", "folder_image_counter", {
        "FolderImageCounterAdvanced": "📷 文件夹图像统计(高级)",
        "FolderImageCounter": "📷 图像数量统计",
        "FolderSubdirectoryListAdvanced": "📁 子目录列表(高级)",
        "FolderSubdirectoryList": "📁 子目录列表",
        "FolderSubdirectoryWithCount": "📊 子目录文件数量统计(高级)",
        "FolderSubdirectoryWithCountSimple": "📊 子目录文件数量统计",
    }),
    ("ultra_switch.py", "ultra_switch", {
        "UltraSwitch": "🔄 万能判断切换(自动)",
        "UltraSwitchSelect": "🎛️ 万能判断切换(手动)",
    }),
    ("text_file_reader.py", "text_file_reader", {
        "TextFileReader": "📄 文本文件读取器",
        "TextBatchReader": "📚 批量文本读取器",
        "TextFolderScanner": "🔍 文件夹文本扫描器",
    }),
    ("resolution_selector.py", "resolution_selector", {
        "AdvancedResolutionSelector": "🎯 高级分辨率选择器",
        "AdvancedResolutionSelectorLatent": "🎯 高级分辨率选择器(Latent)",
    }),
]

for file_name, module_name, display_names in modules_config:
    classes = load_node_module(module_name, file_name)
    if classes:
        for class_name, class_obj in classes.items():
            if class_name in display_names:
                NODE_CLASS_MAPPINGS[class_name] = class_obj
                NODE_DISPLAY_NAME_MAPPINGS[class_name] = display_names[class_name]

print(f"[XiaoCaiTools] 成功加载 {len(NODE_CLASS_MAPPINGS)} 个节点")
print(f"[XiaoCaiTools] 节点列表: {list(NODE_CLASS_MAPPINGS.keys())}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]