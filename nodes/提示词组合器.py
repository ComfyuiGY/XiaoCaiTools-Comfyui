# -*- coding: utf-8 -*-
"""提示词组合器 - 将多段提示词按指定分隔符拼接"""


class PromptCombiner:
    """
    提示词组合器
    将多段提示词按指定分隔符拼接，支持6个输入部分
    """
    
    CATEGORY = "🥣 清粥小菜工具箱"
    FUNCTION = "combine"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("组合提示词",)
    
    @classmethod
    def INPUT_TYPES(cls):
        text_opt = ("STRING", {"multiline": True, "default": ""})
        return {
            "required": {
                "分隔符": ("STRING", {"default": ", ", "tooltip": "各段落之间的分隔符，留空表示直接拼接"}),
            },
            "optional": {
                "段落_1": text_opt,
                "段落_2": text_opt,
                "段落_3": text_opt,
                "段落_4": text_opt,
                "段落_5": text_opt,
                "段落_6": text_opt,
            },
        }
    
    def combine(self, 分隔符: str = ", ", **parts):
        """
        组合多段提示词
        
        Args:
            分隔符: 各段落之间的分隔符，留空表示直接拼接
            **parts: 段落_1 到 段落_6
        
        Returns:
            (组合后的提示词,)
        """
        # 按顺序获取各部分
        ordered = [parts.get(f"段落_{i}", "") for i in range(1, 7)]
        
        # 只去除首尾空白，保留逗号等特殊字符
        cleaned = [(p or "").strip() for p in ordered]
        cleaned = [p for p in cleaned if p]
        
        # 如果分隔符为空或只有空白，直接拼接（不加任何分隔符）
        if not 分隔符 or not 分隔符.strip():
            result = "".join(cleaned)
        else:
            # 使用指定分隔符连接
            result = 分隔符.join(cleaned)
        
        return (result,)


# ========== 兼容旧版接口 ==========
class AnimaPromptCombinerT8(PromptCombiner):
    """兼容旧版节点名称"""
    pass


NODE_CLASS_MAPPINGS = {
    "PromptCombiner": PromptCombiner,
    "AnimaPromptCombinerT8": AnimaPromptCombinerT8,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptCombiner": "🔗 提示词组合器",
    "AnimaPromptCombinerT8": "🔗 提示词组合器(兼容)",
}