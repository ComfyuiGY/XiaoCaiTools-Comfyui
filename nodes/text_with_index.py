# -*- coding: utf-8 -*-
"""
带索引文本处理器节点
支持索引/顺序/随机模式
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


class TextWithIndex:
    """带索引文本处理器"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "文本列表": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "多行文本，每行作为一个条目"
                }),
                "模式": (["索引", "顺序", "随机"], {
                    "default": "索引",
                    "tooltip": "选择模式\n- 索引：根据指定索引读取\n- 顺序：循环读取\n- 随机：随机读取"
                }),
                "索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                    "tooltip": "索引模式：指定读取第几个文本（从0开始）"
                }),
            },
            "optional": {
                "随机种子": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                    "tooltip": "随机模式：随机种子（-1=自动）"
                }),
                "启用动态提示词": ("BOOLEAN", {
                    "default": True,
                    "label_on": "启用",
                    "label_off": "禁用",
                    "tooltip": "是否处理 Spintax {选项1|选项2} 和 Wildcards __filename__ 语法"
                }),
                "清理空行": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 清理空行",
                    "label_off": "📝 保留原样",
                    "tooltip": "自动删除文本中的空行"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("文本", "下一索引")
    FUNCTION = "process"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def __init__(self):
        self.current_index = 0
        self.wildcards_paths = []
    
    @classmethod
    def IS_CHANGED(cls, 文本列表, 模式, 索引, 随机种子=-1, 启用动态提示词=True, 清理空行=True):
        if 模式 == "随机" or 启用动态提示词:
            return float("nan")
        return (文本列表, 模式, 索引)
    
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
        """加载 wildcard 文件"""
        paths = []
        paths.extend(self.wildcards_paths)
        paths.extend([
            Path(folder_paths.base_path) / "input" / "wildcards",
            Path(folder_paths.base_path) / "wildcards",
            Path(folder_paths.base_path) / "ComfyUI" / "wildcards",
            Path(folder_paths.models_dir) / "wildcards",
        ])
        
        for path in paths:
            file_path = path / f"{filename}.txt"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = [l.strip() for l in f.readlines() 
                                if l.strip() and not l.startswith('#')]
                        if lines:
                            return random.choice(lines)
                except:
                    pass
        return filename
    
    def process_dynamic(self, text, seed):
        """处理动态提示词"""
        if not text:
            return text
        
        if seed is not None:
            random.seed(seed)
        
        # 1. 处理 Wildcard 语法 __wildcard__
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
        
        # 2. 处理 Spintax 语法 {选项|选项}，支持权重
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
    
    def process(self, 文本列表, 模式, 索引, 随机种子=-1, 启用动态提示词=True, 清理空行=True):
        lines = [line.strip() for line in 文本列表.split("\n") if line.strip()]
        
        if not lines:
            return ("", 0)
        
        if 模式 == "索引":
            current_idx = min(索引, len(lines) - 1)
            next_idx = current_idx
        elif 模式 == "顺序":
            current_idx = self.current_index % len(lines)
            next_idx = self.current_index + 1
            self.current_index = next_idx
        else:
            if 随机种子 != -1:
                random.seed(随机种子)
            current_idx = random.randint(0, len(lines) - 1)
            next_idx = current_idx
        
        text = lines[current_idx]
        
        if 启用动态提示词:
            seed_val = 随机种子 if 随机种子 != -1 else random.randint(0, 0xffffffffffffffff)
            text = self.process_dynamic(text, seed_val)
        
        if 清理空行:
            text = self.clean_empty_lines(text)
        
        return (text, next_idx)