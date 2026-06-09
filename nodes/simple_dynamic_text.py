# -*- coding: utf-8 -*-
"""
简单动态文本处理器
只使用默认 Wildcards 路径
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


class SimpleDynamicText:
    """
    简单动态文本处理器
    无自定义路径，只使用默认路径
    支持 Spintax 和 Wildcards 语法
    支持权重语法：{权重::选项|权重::选项}
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "文本": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "输入文本，支持 Spintax 语法\n"
                              "- 普通随机：{选项1|选项2|选项3}\n"
                              "- 权重随机：{权重::选项1|权重::选项2}\n"
                              "  例如：{8::2026|1::2023|1::2025} (80%概率2026)\n"
                              "- Wildcards：__filename__"
                }),
                "启用动态提示词": ("BOOLEAN", {
                    "default": True,
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
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("文本",)
    FUNCTION = "process"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    @classmethod
    def IS_CHANGED(cls, 文本, 启用动态提示词, 清理空行):
        if 启用动态提示词:
            return float("nan")
        return (文本, 启用动态提示词, 清理空行)
    
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
        """加载 wildcard 文件（使用默认路径，优先 input/wildcards）"""
        base_path = getattr(folder_paths, 'base_path', '.')
        paths = [
            Path(base_path) / "input" / "wildcards",
            Path(base_path) / "wildcards",
            Path(base_path) / "ComfyUI" / "wildcards",
            Path(base_path) / "models" / "wildcards",
        ]
        
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
    
    def process(self, 文本, 启用动态提示词, 清理空行):
        if not 文本:
            return ("",)
        
        if not 启用动态提示词:
            result = 文本
        else:
            result = self.process_dynamic(文本)
        
        if 清理空行:
            result = self.clean_empty_lines(result)
        
        return (result,)