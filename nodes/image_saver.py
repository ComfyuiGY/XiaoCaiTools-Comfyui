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
                    "default": "Comfyui",
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
                "预览图像": ("BOOLEAN", {
                    "default": True,
                    "label_on": "👁️ 预览",
                    "label_off": "🚫 不预览",
                    "tooltip": "开启：在节点输出中显示图像预览\n关闭：不显示预览，节省内存"
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
            
            # 判断是否为绝对路径：
            # 1. Windows: 包含盘符（如 C:）或以 \ 开头
            # 2. Unix: 以 / 开头
            # 3. 包含 :\ 或 :/ 等路径分隔符组合
            is_abs = False
            if os.path.isabs(parsed_path):
                is_abs = True
            # 额外检查：Windows 盘符模式
            if re.match(r'^[a-zA-Z]:[/\\]', parsed_path):
                is_abs = True
            # 检查是否包含 :\ 或 :/ （Windows 路径特征）
            if re.search(r'[a-zA-Z]:[/\\]', parsed_path):
                is_abs = True
            
            if is_abs:
                save_dir = parsed_path
            else:
                # 相对路径：拼接到 output 目录下
                if parsed_path.startswith('./') or parsed_path.startswith('.\\'):
                    parsed_path = parsed_path[2:]
                # 去除首尾的斜杠
                parsed_path = parsed_path.strip('/\\')
                save_dir = os.path.join(self.output_dir, parsed_path)
        
        # 确保目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        return save_dir
    
    def get_next_filename(self, directory, prefix, delimiter, number_padding, start_number):
        """获取下一个可用的文件名"""
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
        
        i = tensor.cpu()
        
        if i.dim() == 4:
            i = i.squeeze(0)
        
        i = i.numpy()
        
        if i.max() <= 1.0:
            i = i * 255.0
        
        i = np.clip(i, 0, 255).astype(np.uint8)
        
        img = Image.fromarray(i)
        return img
    
    def save_images(self, 图像, 输出路径="", 文件名前缀="Comfyui", 文件名分隔符="_",
                    文件名序号位数=4, 起始序号=1, dpi=300, 质量=100, 
                    图片格式="png", 保存工作流=True, 预览图像=True,
                    prompt=None, extra_pnginfo=None):
        
        current_time = datetime.now()
        
        # 解析文件名前缀中的时间表达式
        parsed_prefix = self.parse_time_expressions(文件名前缀, current_time)
        
        # 获取保存目录
        save_dir = self.get_save_directory(输出路径, current_time)
        
        file_extension = '.' + 图片格式.lower()
        if file_extension == '.jpg':
            file_extension = '.jpeg'
        
        current_num = self.get_next_filename(save_dir, parsed_prefix, 文件名分隔符, 文件名序号位数, 起始序号)
        
        output_files = []
        results = []
        
        # 计算子文件夹路径
        subfolder = ""
        if save_dir != self.output_dir:
            rel_path = os.path.relpath(save_dir, self.output_dir)
            if rel_path != ".":
                subfolder = rel_path.replace(os.sep, "/")
        
        for idx, image in enumerate(图像):
            img = self.tensor2pil(image)
            if img is None:
                print(f"[ImageSaver] 图像转换失败")
                continue
            
            num_str = str(current_num + idx).zfill(文件名序号位数)
            filename = f"{parsed_prefix}{文件名分隔符}{num_str}{file_extension}"
            full_path = os.path.join(save_dir, filename)
            
            try:
                metadata = None
                if 保存工作流 and 图片格式.lower() == "png":
                    metadata = PngImagePlugin.PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for key in extra_pnginfo:
                            metadata.add_text(key, json.dumps(extra_pnginfo[key]))
                
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
                
                results.append({
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": self.type
                })
                
            except Exception as e:
                print(f"[ImageSaver] 保存失败: {e}")
        
        if 预览图像:
            return {"ui": {"images": results}, "result": (图像, "\n".join(output_files))}
        else:
            return {"ui": {"images": []}, "result": (图像, "\n".join(output_files))}


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
                    "default": "Comfyui_[time(%Y%m%d_%H%M%S)]",
                    "multiline": False,
                    "tooltip": "文件名模板，支持时间表达式\n如已存在相同文件会自动添加序号"
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
                "预览图像": ("BOOLEAN", {
                    "default": True,
                    "label_on": "👁️ 预览",
                    "label_off": "🚫 不预览",
                    "tooltip": "开启：在节点输出中显示图像预览\n关闭：不显示预览，节省内存"
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
    
    def parse_time_expressions(self, text):
        """解析时间表达式"""
        if not text:
            return text
        
        current_time = datetime.now()
        
        time_pattern = re.compile(r'\[time\(([^)]+)\)\]')
        
        def replace_time(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = time_pattern.sub(replace_time, text)
        
        date_pattern = re.compile(r'%date:([^%]+)%')
        
        def replace_date(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = date_pattern.sub(replace_date, result)
        
        return result
    
    def get_save_directory(self, base_path):
        """获取保存目录"""
        if not base_path or not base_path.strip():
            save_dir = self.output_dir
        else:
            parsed_path = self.parse_time_expressions(base_path)
            
            # 判断是否为绝对路径
            is_abs = False
            if os.path.isabs(parsed_path):
                is_abs = True
            if re.match(r'^[a-zA-Z]:[/\\]', parsed_path):
                is_abs = True
            if re.search(r'[a-zA-Z]:[/\\]', parsed_path):
                is_abs = True
            
            if is_abs:
                save_dir = parsed_path
            else:
                if parsed_path.startswith('./') or parsed_path.startswith('.\\'):
                    parsed_path = parsed_path[2:]
                parsed_path = parsed_path.strip('/\\')
                save_dir = os.path.join(self.output_dir, parsed_path)
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        return save_dir
    
    def get_unique_filename(self, directory, base_filename, extension):
        """获取唯一文件名，如果文件已存在则自动添加序号"""
        if not extension:
            base, ext = os.path.splitext(base_filename)
            ext = extension if extension else ext
        else:
            base = base_filename
            ext = extension
        
        if not ext.startswith('.'):
            ext = '.' + ext
        
        full_path = os.path.join(directory, f"{base}{ext}")
        if not os.path.exists(full_path):
            return f"{base}{ext}"
        
        counter = 1
        while True:
            new_base = f"{base}_{counter:03d}"
            full_path = os.path.join(directory, f"{new_base}{ext}")
            if not os.path.exists(full_path):
                return f"{new_base}{ext}"
            counter += 1
    
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
    
    def save_image(self, 图像, 输出路径, 文件名模板, 图片格式, 质量, 保存工作流=True, 预览图像=True,
                   prompt=None, extra_pnginfo=None):
        
        current_time = datetime.now()
        
        parsed_template = self.parse_time_expressions(文件名模板)
        file_extension = '.' + 图片格式.lower()
        
        save_dir = self.get_save_directory(输出路径)
        
        subfolder = ""
        if save_dir != self.output_dir:
            rel_path = os.path.relpath(save_dir, self.output_dir)
            if rel_path != ".":
                subfolder = rel_path.replace(os.sep, "/")
        
        output_files = []
        results = []
        
        for idx, image in enumerate(图像):
            img = self.tensor2pil(image)
            if img is None:
                continue
            
            if 图像.shape[0] > 1:
                base_filename = parsed_template
                unique_filename = self.get_unique_filename(save_dir, base_filename, file_extension)
                base_without_ext, ext = os.path.splitext(unique_filename)
                final_filename = f"{base_without_ext}_{idx+1}{ext}"
            else:
                final_filename = self.get_unique_filename(save_dir, parsed_template, file_extension)
            
            save_path = os.path.join(save_dir, final_filename)
            
            try:
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
                
                results.append({
                    "filename": os.path.basename(save_path),
                    "subfolder": subfolder,
                    "type": self.type
                })
                
            except Exception as e:
                print(f"[ImageSaverSimple] 保存失败: {e}")
        
        if 预览图像:
            return {"ui": {"images": results}, "result": (图像, "\n".join(output_files))}
        else:
            return {"ui": {"images": []}, "result": (图像, "\n".join(output_files))}


NODE_CLASS_MAPPINGS = {
    "ImageSaver": ImageSaver,
    "ImageSaverSimple": ImageSaverSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageSaver": "📸 图像保存(高级)",
    "ImageSaverSimple": "📸 图像保存(简单)",
}