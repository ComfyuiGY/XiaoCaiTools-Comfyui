"""
高级分辨率选择器节点
支持横屏、竖屏、方形三种分辨率独立选择，只能同时生效一个
"""

import torch
import comfy.utils
import comfy.model_management


class AdvancedResolutionSelector:
    """
    高级分辨率选择器节点
    """
    
    # 横屏分辨率 (宽 > 高)
    LANDSCAPE_RESOLUTIONS = {
        "不启用": (0, 0),
        "640x360 (16:9) 横屏": (640, 360),
        "832x480 (5.2:3) 横屏": (832, 480),
        "854x480 (16:9) 横屏": (854, 480),
        "960x640 (3:2) 横屏": (960, 640),
        "1024x576 (16:9) 横屏": (1024, 576),
        "1152x896 (9:7) 横屏": (1152, 896),
        "1216x832 (19:13) 横屏": (1216, 832),
        "1280x720 (16:9) 横屏": (1280, 720),
        "1280x800 (16:10) 横屏": (1280, 800),
        "1344x768 (7:4) 横屏": (1344, 768),
        "1536x1024 (3:2) 横屏": (1536, 1024),
        "1920x1080 (16:9) 横屏": (1920, 1080),
        "1920x1200 (16:10) 横屏": (1920, 1200),
        "2048x1152 (16:9) 横屏": (2048, 1152),
        "2560x1440 (16:9) 横屏": (2560, 1440),
        "3072x2048 (3:2) 横屏": (3072, 2048),
        "3840x2160 (16:9) 横屏": (3840, 2160),
        "4096x2160 (17:9) 横屏": (4096, 2160),
        "5120x2880 (16:9) 横屏": (5120, 2880),
        "7680x4320 (16:9) 横屏": (7680, 4320),
    }
    
    # 竖屏分辨率 (高 > 宽) - 宽在前
    PORTRAIT_RESOLUTIONS = {
        "不启用": (0, 0),
        "480x640 (4:3) 竖屏": (480, 640),
        "480x800 (5:8) 竖屏": (480, 800),
        "480x832 (3:5.2) 竖屏": (480, 832),
        "480x854 (9:16) 竖屏": (480, 854),
        "512x768 (2:3) 竖屏": (512, 768),
        "512x896 (4:7) 竖屏": (512, 896),
        "576x1024 (16:9) 竖屏": (576, 1024),
        "640x960 (2:3) 竖屏": (640, 960),
        "720x1280 (9:16) 竖屏": (720, 1280),
        "768x1024 (3:4) 竖屏": (768, 1024),
        "768x1344 (4:7) 竖屏": (768, 1344),
        "800x1280 (5:8) 竖屏": (800, 1280),
        "832x1216 (13:19) 竖屏": (832, 1216),
        "896x1152 (7:9) 竖屏": (896, 1152),
        "1024x1536 (2:3) 竖屏": (1024, 1536),
        "1080x1920 (9:16) 竖屏": (1080, 1920),
        "1080x2160 (18:9) 竖屏": (1080, 2160),
        "1152x2048 (16:9) 竖屏": (1152, 2048),
        "1200x1920 (16:10) 竖屏": (1200, 1920),
        "1440x2560 (16:9) 竖屏": (1440, 2560),
        "2048x3072 (2:3) 竖屏": (2048, 3072),
        "2160x3840 (9:16) 竖屏": (2160, 3840),
        "2160x4096 (9:16) 竖屏": (2160, 4096),
        "2880x5120 (9:16) 竖屏": (2880, 5120),
        "4320x7680 (9:16) 竖屏": (4320, 7680),
    }
    
    # 方形分辨率 (宽 = 高)
    SQUARE_RESOLUTIONS = {
        "不启用": (0, 0),
        "512x512 方形": (512, 512),
        "640x640 方形": (640, 640),
        "768x768 方形": (768, 768),
        "896x896 方形": (896, 896),
        "1024x1024 方形": (1024, 1024),
        "1152x1152 方形": (1152, 1152),
        "1280x1280 方形": (1280, 1280),
        "1536x1536 方形": (1536, 1536),
        "2048x2048 方形": (2048, 2048),
        "2560x2560 方形": (2560, 2560),
        "3072x3072 方形": (3072, 3072),
        "4096x4096 方形": (4096, 4096),
        "5120x5120 方形": (5120, 5120),
        "6144x6144 方形": (6144, 6144),
        "8192x8192 方形": (8192, 8192),
    }
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "横屏": (list(cls.LANDSCAPE_RESOLUTIONS.keys()), {
                    "default": "不启用"
                }),
                "竖屏": (list(cls.PORTRAIT_RESOLUTIONS.keys()), {
                    "default": "不启用"
                }),
                "方形": (list(cls.SQUARE_RESOLUTIONS.keys()), {
                    "default": "不启用"
                }),
                "自定义宽度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 8
                }),
                "自定义高度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 8
                }),
                "使用自定义": ("BOOLEAN", {
                    "default": False,
                    "label_on": "是",
                    "label_off": "否"
                }),
            }
        }
    
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽度", "高度")
    FUNCTION = "get_resolution"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        这个方法确保节点状态变化时会被重新执行
        """
        return float("NaN")
    
    def get_resolution(self, 横屏, 竖屏, 方形, 自定义宽度, 自定义高度, 使用自定义):
        """
        根据选择返回宽度和高度
        注意：由于前端的联动逻辑，同一时间只会有一个分辨率选项被选中
        """
        # 1. 优先使用自定义
        if 使用自定义:
            return (自定义宽度, 自定义高度)
        
        # 2. 检查横屏（非"不启用"）
        if 横屏 != "不启用":
            width, height = self.LANDSCAPE_RESOLUTIONS.get(横屏, (0, 0))
            if width > 0 and height > 0:
                return (width, height)
        
        # 3. 检查竖屏（非"不启用"）
        if 竖屏 != "不启用":
            width, height = self.PORTRAIT_RESOLUTIONS.get(竖屏, (0, 0))
            if width > 0 and height > 0:
                return (width, height)
        
        # 4. 检查方形（非"不启用"）
        if 方形 != "不启用":
            width, height = self.SQUARE_RESOLUTIONS.get(方形, (0, 0))
            if width > 0 and height > 0:
                return (width, height)
        
        # 5. 全部不启用，返回默认值
        return (1024, 1024)


class AdvancedResolutionSelectorLatent:
    """
    高级分辨率选择器节点（带Latent输出）
    基于选择的分辨率生成空的Latent样本
    """
    
    # 复用相同的分辨率字典
    LANDSCAPE_RESOLUTIONS = AdvancedResolutionSelector.LANDSCAPE_RESOLUTIONS
    PORTRAIT_RESOLUTIONS = AdvancedResolutionSelector.PORTRAIT_RESOLUTIONS
    SQUARE_RESOLUTIONS = AdvancedResolutionSelector.SQUARE_RESOLUTIONS
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "横屏": (list(cls.LANDSCAPE_RESOLUTIONS.keys()), {
                    "default": "不启用"
                }),
                "竖屏": (list(cls.PORTRAIT_RESOLUTIONS.keys()), {
                    "default": "不启用"
                }),
                "方形": (list(cls.SQUARE_RESOLUTIONS.keys()), {
                    "default": "不启用"
                }),
                "自定义宽度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 8
                }),
                "自定义高度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 8
                }),
                "使用自定义": ("BOOLEAN", {
                    "default": False,
                    "label_on": "是",
                    "label_off": "否"
                }),
                "批量大小": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 64,
                    "step": 1,
                    "tooltip": "批量大小"
                }),
            }
        }
    
    RETURN_TYPES = ("INT", "INT", "LATENT")
    RETURN_NAMES = ("宽度", "高度", "Latent")
    FUNCTION = "get_resolution_with_latent"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        这个方法确保节点状态变化时会被重新执行
        """
        return float("NaN")
    
    def get_resolution_with_latent(self, 横屏, 竖屏, 方形, 自定义宽度, 自定义高度, 使用自定义, 批量大小):
        """
        根据选择返回宽度、高度和对应的空Latent样本
        """
        # 1. 优先使用自定义
        if 使用自定义:
            width = 自定义宽度
            height = 自定义高度
        # 2. 检查横屏（非"不启用"）
        elif 横屏 != "不启用":
            width, height = self.LANDSCAPE_RESOLUTIONS.get(横屏, (0, 0))
        # 3. 检查竖屏（非"不启用"）
        elif 竖屏 != "不启用":
            width, height = self.PORTRAIT_RESOLUTIONS.get(竖屏, (0, 0))
        # 4. 检查方形（非"不启用"）
        elif 方形 != "不启用":
            width, height = self.SQUARE_RESOLUTIONS.get(方形, (0, 0))
        # 5. 全部不启用，返回默认值
        else:
            width, height = (1024, 1024)
        
        # 确保宽度和高度是8的倍数（VAE要求）
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        # 生成空Latent样本
        device = comfy.model_management.get_torch_device()
        latent = torch.zeros([批量大小, 4, height // 8, width // 8], device=device)
        latent_result = {"samples": latent}
        
        return (width, height, latent_result)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "AdvancedResolutionSelector": AdvancedResolutionSelector,
    "AdvancedResolutionSelectorLatent": AdvancedResolutionSelectorLatent,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AdvancedResolutionSelector": "高级分辨率选择器",
    "AdvancedResolutionSelectorLatent": "高级分辨率选择器(Latent)",
}