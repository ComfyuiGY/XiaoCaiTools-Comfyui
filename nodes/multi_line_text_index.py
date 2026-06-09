# -*- coding: utf-8 -*-
"""
多行文本索引节点
显示多行文本的行数统计，并输出选中的文本
"""

import re
import random
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


class MultiLineTextIndex:
    """
    多行文本索引节点
    显示多行文本的行数统计，并输出选中的文本
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "多行文本": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "输入多行文本，每行作为一个条目"
                }),
                "选择索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "tooltip": "选择要输出的行索引（从0开始）"
                }),
                "启用动态提示词": ("BOOLEAN", {
                    "default": False,
                    "label_on": "🎲 动态模式",
                    "label_off": "📝 普通模式",
                    "tooltip": "开启：处理 Spintax 和 Wildcards 语法\n关闭：直接输出原文本"
                }),
                "清理空行": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 清理空行",
                    "label_off": "📝 保留原样",
                    "tooltip": "自动删除文本中的空行"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "STRING")
    RETURN_NAMES = ("选中文本", "行数", "全部文本")
    FUNCTION = "process"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def __init__(self):
        self.wildcards_paths = []
    
    @classmethod
    def IS_CHANGED(cls, 多行文本, 选择索引, 启用动态提示词, 清理空行):
        if 启用动态提示词:
            return float("nan")
        return (多行文本, 选择索引, 清理空行)
    
    def clean_empty_lines(self, text):
        """清理空行，保留非空行"""
        if not text:
            return text
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        return '\n'.join(non_empty_lines)
    
    def parse_weighted_options(self, text):
        """解析带权重的选项"""
        if not text:
            return [], 0
        
        parts = text.split('|')
        weighted = []
        total_weight = 0
        
        for part in parts:
            if '::' in part:
                weight_str, value = part.split('::', 1)
                try:
                    weight = float(weight_str.strip())
                except:
                    weight = 1.0
                value = value.strip()
            else:
                weight = 1.0
                value = part.strip()
            
            if weight > 0 and value:
                weighted.append((value, weight))
                total_weight += weight
        
        return weighted, total_weight
    
    def select_weighted_option(self, weighted, total_weight):
        """根据权重随机选择"""
        if not weighted:
            return ""
        
        r = random.random() * total_weight
        acc = 0
        for value, weight in weighted:
            acc += weight
            if r <= acc:
                return value
        return weighted[-1][0]
    
    def load_wildcard(self, filename):
        """加载 wildcard 文件，默认使用 input/wildcards"""
        paths = []
        paths.extend(self.wildcards_paths)
        
        base_path = getattr(folder_paths, 'base_path', '.')
        paths.extend([
            Path(base_path) / "input" / "wildcards",
            Path(base_path) / "wildcards",
            Path(base_path) / "ComfyUI" / "wildcards",
            Path(base_path) / "models" / "wildcards",
        ])
        
        for path in paths:
            file_path = path / f"{filename}.txt"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f.readlines() 
                                if line.strip() and not line.startswith('#')]
                        if lines:
                            return random.choice(lines)
                except:
                    pass
        
        return filename
    
    def process_dynamic(self, text):
        """处理动态提示词"""
        if not text:
            return text
        
        pattern_wildcard = re.compile(r"__([^_]+(?:_[^_]+)*)__")
        
        def replace_wildcard(match):
            name = match.group(1)
            return self.load_wildcard(name)
        
        prev = None
        max_iterations = 50
        iteration = 0
        while prev != text and pattern_wildcard.search(text) and iteration < max_iterations:
            prev = text
            text = pattern_wildcard.sub(replace_wildcard, text)
            iteration += 1
        
        pattern_spintax = re.compile(r"\{([^{}]+)\}")
        
        def replace_spintax(match):
            content = match.group(1)
            
            if '::' in content:
                weighted, total = self.parse_weighted_options(content)
                if weighted:
                    return self.select_weighted_option(weighted, total)
            
            options = [p.strip() for p in content.split("|") if p.strip()]
            if options:
                return random.choice(options)
            return match.group(0)
        
        prev = None
        iteration = 0
        while prev != text and pattern_spintax.search(text) and iteration < max_iterations:
            prev = text
            text = pattern_spintax.sub(replace_spintax, text)
            iteration += 1
        
        return text
    
    def process(self, 多行文本, 选择索引, 启用动态提示词, 清理空行):
        if 清理空行:
            processed_text = self.clean_empty_lines(多行文本)
        else:
            processed_text = 多行文本
        
        lines = [line.strip() for line in processed_text.split('\n') if line.strip()]
        line_count = len(lines)
        
        if 启用动态提示词:
            processed_lines = []
            for line in lines:
                processed_line = self.process_dynamic(line)
                processed_lines.append(processed_line)
            lines = processed_lines
        
        if line_count > 0:
            valid_index = max(0, min(选择索引, line_count - 1))
            selected_text = lines[valid_index]
        else:
            selected_text = ""
        
        return (selected_text, line_count, processed_text)