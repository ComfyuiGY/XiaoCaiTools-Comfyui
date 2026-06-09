# -*- coding: utf-8 -*-
"""
图像保存节点
支持时间表达式和动态文件名
"""

import os
import re
import json
import folder_paths
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image, PngImagePlugin
import numpy as np


class ImageSaver:
    """
    图像保存节点
    支持时间表达式：%date:yyyyMMddhhmmss% 和 [time(%Y-%m-%d-%hhmmss)]
    """
    
    def __init__(self):
        self.output_dir = folder_paths.output_directory
        self.type = 'output'
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE", {"tooltip": "要保存的图像"}),
                "输出路径": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "输出路径，支持时间表达式\n例如：[time(%Y-%m-%d)] 或 %date:yyyyMMdd%"
                }),
                "文件名前缀": ("STRING", {
                    "default": "Image",
                    "multiline": False,
                    "tooltip": "文件名前缀"
                }),
                "文件名分隔符": ("STRING", {
                    "default": "_",
                    "multiline": False,
                    "tooltip": "前缀和序号之间的分隔符"
                }),
                "文件名序号位数": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 9,
                    "step": 1,
                    "tooltip": "序号位数（如3位：001）"
                }),
                "起始序号": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "tooltip": "起始序号值"
                }),
                "dpi": ("INT", {
                    "default": 300,
                    "min": 72,
                    "max": 1200,
                    "step": 1,
                    "tooltip": "图像DPI"
                }),
                "质量": ("INT", {
                    "default": 100,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "JPEG/WEBP压缩质量（1-100）"
                }),
                "图片格式": (["png", "jpg", "jpeg", "webp", "bmp", "tiff"], {
                    "default": "png",
                    "tooltip": "输出图片格式"
                }),
                "保存工作流": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 保存",
                    "label_off": "❌ 不保存",
                    "tooltip": "开启：将工作流信息保存到图片中（PNG格式支持）\n关闭：不保存工作流信息"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("图像", "保存路径",)
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "🥣 清粥小菜工具箱"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")
    
    def parse_time_expressions(self, text, current_time=None):
        """解析时间表达式"""
        if not text:
            return text
        
        if current_time is None:
            current_time = datetime.now()
        
        result = text
        
        # 解析 [time(format)] 格式
        time_pattern = re.compile(r'\[time\(([^)]+)\)\]')
        
        def replace_time(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = time_pattern.sub(replace_time, result)
        
        # 解析 %date:format% 格式
        date_pattern = re.compile(r'%date:([^%]+)%')
        
        def replace_date(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = date_pattern.sub(replace_date, result)
        
        return result
    
    def get_save_directory(self, base_path, current_time):
        """获取保存目录"""
        if not base_path or not base_path.strip():
            save_dir = self.output_dir
        else:
            parsed_path = self.parse_time_expressions(base_path, current_time)
            save_dir = os.path.abspath(parsed_path)
            
            if not os.path.isabs(save_dir):
                save_dir = os.path.join(folder_paths.base_path, save_dir)
        
        # 创建目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        return save_dir
    
    def get_next_filename(self, directory, prefix, delimiter, number_padding, start_number):
        """获取下一个可用的文件名"""
        # 查找现有序号
        pattern = f"{re.escape(prefix)}{re.escape(delimiter)}(\\d+)"
        existing_counters = []
        
        try:
            for filename in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, filename)):
                    match = re.match(pattern, os.path.basename(filename))
                    if match:
                        existing_counters.append(int(match.group(1)))
            
            if existing_counters:
                next_num = max(existing_counters) + 1
            else:
                next_num = start_number
        except:
            next_num = start_number
        
        return next_num
    
    def tensor2pil(self, tensor):
        """将 ComfyUI 的图像张量转换为 PIL Image"""
        if tensor is None:
            return None
        
        # 确保在 CPU 上
        i = tensor.cpu()
        
        # 处理形状
        if i.dim() == 4:
            i = i.squeeze(0)
        
        # 转换为 numpy
        i = i.numpy()
        
        # 归一化 (0-1 范围转 0-255)
        if i.max() <= 1.0:
            i = i * 255.0
        
        i = np.clip(i, 0, 255).astype(np.uint8)
        
        # 转换为 PIL Image
        img = Image.fromarray(i)
        return img
    
    def save_images(self, 图像, 输出路径="", 文件名前缀="Image", 文件名分隔符="_",
                    文件名序号位数=4, 起始序号=1, dpi=300, 质量=100, 
                    图片格式="png", 保存工作流=True, prompt=None, extra_pnginfo=None):
        
        current_time = datetime.now()
        
        # 解析文件名前缀中的时间表达式
        parsed_prefix = self.parse_time_expressions(文件名前缀, current_time)
        
        # 解析输出路径
        save_dir = self.get_save_directory(输出路径, current_time)
        
        # 获取文件扩展名
        file_extension = '.' + 图片格式.lower()
        if file_extension == '.jpg':
            file_extension = '.jpeg'
        
        # 获取起始序号
        current_num = self.get_next_filename(save_dir, parsed_prefix, 文件名分隔符, 文件名序号位数, 起始序号)
        
        # 结果列表
        output_files = []
        results = []
        
        # 处理每一张图像
        for idx, image in enumerate(图像):
            # 转换为 PIL Image
            img = self.tensor2pil(image)
            if img is None:
                print(f"[ImageSaver] 图像转换失败")
                continue
            
            # 生成文件名
            num_str = str(current_num + idx).zfill(文件名序号位数)
            filename = f"{parsed_prefix}{文件名分隔符}{num_str}{file_extension}"
            full_path = os.path.join(save_dir, filename)
            
            try:
                # 准备元数据（仅当需要保存工作流时）
                metadata = None
                if 保存工作流 and 图片格式.lower() == "png":
                    metadata = PngImagePlugin.PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for key in extra_pnginfo:
                            metadata.add_text(key, json.dumps(extra_pnginfo[key]))
                
                # 保存图像
                if 图片格式.lower() in ["jpg", "jpeg"]:
                    img.save(full_path, quality=质量, dpi=(dpi, dpi))
                elif 图片格式.lower() == "webp":
                    img.save(full_path, quality=质量)
                elif 图片格式.lower() == "png":
                    if metadata:
                        img.save(full_path, pnginfo=metadata, dpi=(dpi, dpi))
                    else:
                        img.save(full_path, dpi=(dpi, dpi))
                elif 图片格式.lower() == "bmp":
                    img.save(full_path)
                elif 图片格式.lower() == "tiff":
                    img.save(full_path, dpi=(dpi, dpi))
                else:
                    img.save(full_path)
                
                print(f"[ImageSaver] 图像已保存: {full_path}")
                output_files.append(full_path)
                
                # 用于前端显示的路径
                subfolder = self.get_subfolder_path(full_path, self.output_dir)
                results.append({
                    "filename": os.path.basename(full_path),
                    "subfolder": subfolder,
                    "type": self.type
                })
                
            except Exception as e:
                print(f"[ImageSaver] 保存失败: {e}")
        
        # 返回结果
        return {"ui": {"images": results}, "result": (图像, "\n".join(output_files))}
    
    def get_subfolder_path(self, image_path, output_path):
        """获取子文件夹路径"""
        output_parts = output_path.strip(os.sep).split(os.sep)
        image_parts = image_path.strip(os.sep).split(os.sep)
        
        try:
            common_parts = os.path.commonprefix([output_parts, image_parts])
            subfolder_parts = image_parts[len(common_parts):]
            subfolder_path = os.sep.join(subfolder_parts[:-1])
            return subfolder_path
        except:
            return ""


class ImageSaverSimple:
    """简单图像保存节点"""
    
    def __init__(self):
        self.output_dir = folder_paths.output_directory
        self.type = 'output'
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE", {"tooltip": "要保存的图像"}),
                "输出路径": ("STRING", {
                    "default": "[time(%Y-%m-%d)]",
                    "multiline": False,
                    "tooltip": "输出路径，支持时间表达式"
                }),
                "文件名模板": ("STRING", {
                    "default": "Image_[time(%Y%m%d_%H%M%S)]",
                    "multiline": False,
                    "tooltip": "文件名模板，支持时间表达式"
                }),
                "图片格式": (["png", "jpg", "jpeg", "webp"], {
                    "default": "png",
                    "tooltip": "输出图片格式"
                }),
                "质量": ("INT", {
                    "default": 100,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "JPEG/WEBP压缩质量（1-100）"
                }),
                "保存工作流": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 保存",
                    "label_off": "❌ 不保存",
                    "tooltip": "开启：将工作流信息保存到图片中（PNG格式支持）\n关闭：不保存工作流信息"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("图像", "保存路径",)
    FUNCTION = "save_image"
    OUTPUT_NODE = True
    CATEGORY = "🥣 清粥小菜工具箱"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")
    
    def parse_time_expressions(self, text):
        """解析时间表达式"""
        if not text:
            return text
        
        current_time = datetime.now()
        
        # 解析 [time(format)] 格式
        time_pattern = re.compile(r'\[time\(([^)]+)\)\]')
        
        def replace_time(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = time_pattern.sub(replace_time, text)
        
        # 解析 %date:format% 格式
        date_pattern = re.compile(r'%date:([^%]+)%')
        
        def replace_date(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = date_pattern.sub(replace_date, result)
        
        return result
    
    def tensor2pil(self, tensor):
        """将 ComfyUI 的图像张量转换为 PIL Image"""
        if tensor is None:
            return None
        
        i = tensor.cpu()
        
        if i.dim() == 4:
            i = i.squeeze(0)
        
        i = i.numpy()
        
        if i.max() <= 1.0:
            i = i * 255.0
        
        i = np.clip(i, 0, 255).astype(np.uint8)
        
        img = Image.fromarray(i)
        return img
    
    def save_image(self, 图像, 输出路径, 文件名模板, 图片格式, 质量, 保存工作流=True,
                   prompt=None, extra_pnginfo=None):
        
        current_time = datetime.now()
        
        # 解析文件名模板
        filename = self.parse_time_expressions(文件名模板)
        file_extension = '.' + 图片格式.lower()
        if not filename.endswith(file_extension):
            filename = filename + file_extension
        
        # 解析输出路径
        parsed_path = self.parse_time_expressions(输出路径)
        if not parsed_path:
            save_dir = self.output_dir
        else:
            save_dir = os.path.abspath(parsed_path)
            if not os.path.isabs(save_dir):
                save_dir = os.path.join(folder_paths.base_path, save_dir)
        
        # 创建目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        output_files = []
        results = []
        
        # 处理每一张图像
        for idx, image in enumerate(图像):
            img = self.tensor2pil(image)
            if img is None:
                continue
            
            # 批量处理时添加序号
            if 图像.shape[0] > 1:
                base, ext = os.path.splitext(filename)
                save_path = os.path.join(save_dir, f"{base}_{idx+1}{ext}")
            else:
                save_path = os.path.join(save_dir, filename)
            
            try:
                # 准备元数据（仅当需要保存工作流且为PNG格式时）
                metadata = None
                if 保存工作流 and 图片格式.lower() == "png":
                    metadata = PngImagePlugin.PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for key in extra_pnginfo:
                            metadata.add_text(key, json.dumps(extra_pnginfo[key]))
                
                if 图片格式.lower() in ["jpg", "jpeg"]:
                    img.save(save_path, quality=质量)
                elif 图片格式.lower() == "webp":
                    img.save(save_path, quality=质量)
                elif 图片格式.lower() == "png":
                    if metadata:
                        img.save(save_path, pnginfo=metadata)
                    else:
                        img.save(save_path)
                else:
                    img.save(save_path)
                
                print(f"[ImageSaverSimple] 图像已保存: {save_path}")
                output_files.append(save_path)
                
                subfolder = self.get_subfolder_path(save_path, self.output_dir)
                results.append({
                    "filename": os.path.basename(save_path),
                    "subfolder": subfolder,
                    "type": self.type
                })
                
            except Exception as e:
                print(f"[ImageSaverSimple] 保存失败: {e}")
        
        return {"ui": {"images": results}, "result": (图像, "\n".join(output_files))}
    
    def get_subfolder_path(self, image_path, output_path):
        """获取子文件夹路径"""
        output_parts = output_path.strip(os.sep).split(os.sep)
        image_parts = image_path.strip(os.sep).split(os.sep)
        
        try:
            common_parts = os.path.commonprefix([output_parts, image_parts])
            subfolder_parts = image_parts[len(common_parts):]
            subfolder_path = os.sep.join(subfolder_parts[:-1])
            return subfolder_path
        except:
            return ""


NODE_CLASS_MAPPINGS = {
    "ImageSaver": ImageSaver,
    "ImageSaverSimple": ImageSaverSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSaver": "📸 图像保存(高级)",
    "ImageSaverSimple": "📸 图像保存(简单)",
}