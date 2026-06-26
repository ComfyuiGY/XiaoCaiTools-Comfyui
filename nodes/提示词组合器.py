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
                "分隔符": ("STRING", {"default": ", ", "tooltip": "各段落之间的分隔符"}),
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
            分隔符: 各段落之间的分隔符
            **parts: 段落_1 到 段落_6
        
        Returns:
            (组合后的提示词,)
        """
        # 按顺序获取各部分
        ordered = [parts.get(f"段落_{i}", "") for i in range(1, 7)]
        
        # 清理：去除首尾空白和多余的逗号
        cleaned = [(p or "").strip().strip(",") for p in ordered]
        cleaned = [p for p in cleaned if p]
        
        # 使用分隔符连接
        separator = 分隔符 or ", "
        result = separator.join(cleaned)
        
        return (result,)


# ========== 如果需要兼容旧版接口，可以保留原类名 ==========
class AnimaPromptCombinerT8(PromptCombiner):
    """兼容旧版节点名称"""
    pass


NODE_CLASS_MAPPINGS = {
    "PromptCombiner": PromptCombiner,
    "AnimaPromptCombinerT8": AnimaPromptCombinerT8,  # 保留旧名称兼容
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptCombiner": "🔗 提示词组合器",
    "AnimaPromptCombinerT8": "🔗 提示词组合器(兼容)",
}