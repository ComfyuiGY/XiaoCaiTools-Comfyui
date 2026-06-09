# -*- coding: utf-8 -*-
"""
文本列表选择器节点
从 wildcards 文件夹读取指定文件，将内容作为下拉列表选项
"""

import os
from pathlib import Path

try:
    import folder_paths
except ImportError:
    class MockFolderPaths:
        base_path = "."
        models_dir = "models"
        user_directory = "user"
        input_dir = "input"
    folder_paths = MockFolderPaths()


def get_comfyui_base_path():
    """获取 ComfyUI 基础路径"""
    base_path = getattr(folder_paths, 'base_path', '.')
    return base_path


def get_wildcard_files():
    """获取 wildcards 目录下的所有 .txt 文件"""
    files = set()
    
    base_path = get_comfyui_base_path()
    
    # 只使用 input/wildcards 路径
    search_path = Path(base_path) / "input" / "wildcards"
    
    if search_path.exists():
        for file_path in search_path.glob("*.txt"):
            files.add(file_path.stem)
    
    result = sorted(list(files)) if files else ["无可用文件"]
    return result


def get_options_from_file(filename):
    """从文件读取选项列表"""
    if not filename or filename == "无可用文件":
        return ["无可用选项"]
    
    base_path = get_comfyui_base_path()
    
    # 只使用 input/wildcards 路径
    search_path = Path(base_path) / "input" / "wildcards"
    file_path = search_path / f"{filename}.txt"
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for line in f.readlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        lines.append(line)
                return lines if lines else ["无内容"]
        except Exception as e:
            print(f"[TextListSelector] 读取文件失败 {file_path}: {e}")
            return ["读取失败"]
    
    return ["未找到文件"]


class TextListSelector:
    """
    文本列表选择器节点
    从 wildcards 文件夹读取指定文件，将内容作为下拉列表选项
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取文件列表
        files = get_wildcard_files()
        default_file = files[0] if files else "无可用文件"
        
        # 获取该文件的选项列表
        options = get_options_from_file(default_file)
        options_tuple = tuple(options) if options else ("无可用选项",)
        
        return {
            "required": {
                "文件列表": (files, {
                    "default": default_file,
                    "tooltip": "选择要读取的 wildcards 文件"
                }),
                "选项列表": (options_tuple, {
                    "default": options_tuple[0] if options_tuple else "无",
                    "tooltip": "从文件内容中选择一个选项"
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "LIST", "INT")
    RETURN_NAMES = ("选中文本", "文件名", "全部选项", "选项数量")
    FUNCTION = "process"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    @classmethod
    def IS_CHANGED(cls, 文件列表, 选项列表=None, unique_id=None):
        return (文件列表,)
    
    def process(self, 文件列表, 选项列表, unique_id=None):
        """处理文本列表选择"""
        # 获取选项列表
        options = get_options_from_file(文件列表)
        option_count = len(options)
        
        # 确保选择选项有效
        if options:
            if 选项列表 not in options:
                选项列表 = options[0]
        else:
            选项列表 = ""
        
        return (选项列表, 文件列表, options, option_count)


NODE_CLASS_MAPPINGS = {
    "TextListSelector": TextListSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextListSelector": "📋 文本列表选择器",
}