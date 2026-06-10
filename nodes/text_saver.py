# -*- coding: utf-8 -*-
"""
保存文本节点
支持时间表达式和多种写入模式
"""

import os
import re
from datetime import datetime
from pathlib import Path
import folder_paths


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


any_type = AnyType("*")


class TextSaver:
    """
    保存文本节点(高级)
    支持时间表达式：%date:yyyyMMddHHmmss% 和 [time(%Y-%m-%d-%H%M%S)]
    支持多种写入模式：追加、覆盖、仅新增
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "文本": (any_type, {
                    "tooltip": "要保存的文本内容"
                }),
                "根目录": (["output", "input", "temp", "自定义"], {
                    "default": "output",
                    "tooltip": "保存根目录"
                }),
                "自定义路径": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "自定义路径（仅当根目录选择'自定义'时生效）"
                }),
                "文件": ("STRING", {
                    "default": "[time(%Y年%m月%d日)].txt",
                    "multiline": False,
                    "tooltip": "文件名，支持时间表达式"
                }),
                "附加": (["追加", "覆盖", "仅新增"], {
                    "default": "追加",
                    "tooltip": "写入模式\n- 追加：在文件末尾添加内容\n- 覆盖：覆盖整个文件\n- 仅新增：如果文件不存在才创建，存在则不写入"
                }),
                "插入新行": ("BOOLEAN", {
                    "default": False,
                    "label_on": "✅ 是",
                    "label_off": "❌ 否",
                    "tooltip": "是否在每次写入时插入新行"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("状态信息",)
    FUNCTION = "save_text"
    CATEGORY = "🥣 清粥小菜工具箱"
    OUTPUT_NODE = True
    
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
        
        # 解析 %date:format% 格式
        date_pattern = re.compile(r'%date:([^%]+)%')
        
        def replace_date(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = date_pattern.sub(replace_date, result)
        
        # 解析 [time(format)] 格式
        time_pattern = re.compile(r'\[time\(([^)]+)\)\]')
        
        def replace_time(match):
            format_str = match.group(1)
            try:
                return current_time.strftime(format_str)
            except:
                return match.group(0)
        
        result = time_pattern.sub(replace_time, result)
        
        return result
    
    def get_save_directory(self, 根目录, 自定义路径):
        """获取保存目录"""
        if 根目录 == "自定义":
            if 自定义路径 and 自定义路径.strip():
                save_dir = 自定义路径.strip()
            else:
                save_dir = folder_paths.output_directory
        elif 根目录 == "input":
            save_dir = folder_paths.input_directory
        elif 根目录 == "temp":
            save_dir = folder_paths.temp_directory
        else:  # output
            save_dir = folder_paths.output_directory
        
        # 创建目录
        os.makedirs(save_dir, exist_ok=True)
        
        return save_dir
    
    def convert_to_string(self, text_input):
        """将输入转换为字符串"""
        if text_input is None:
            return ""
        
        if isinstance(text_input, str):
            return text_input
        
        if isinstance(text_input, (list, tuple)):
            if len(text_input) > 0:
                return self.convert_to_string(text_input[0])
            return ""
        
        if isinstance(text_input, dict):
            if 'samples' in text_input:
                return f"Tensor: {text_input['samples'].shape if hasattr(text_input['samples'], 'shape') else 'unknown'}"
            for key in ['text', 'content', 'string', 'value']:
                if key in text_input:
                    return self.convert_to_string(text_input[key])
            return str(text_input)
        
        try:
            return str(text_input)
        except:
            return ""
    
    def save_text(self, 文本, 根目录, 自定义路径, 文件, 附加, 插入新行):
        """
        保存文本到文件
        """
        current_time = datetime.now()
        
        # 转换文本输入为字符串
        content = self.convert_to_string(文本)
        
        # 解析文件名中的时间表达式
        parsed_filename = self.parse_time_expressions(文件, current_time)
        
        # 获取保存目录
        save_dir = self.get_save_directory(根目录, 自定义路径)
        
        # 完整文件路径
        file_path = os.path.join(save_dir, parsed_filename)
        
        if not content:
            status_msg = f"⚠️ 文本内容为空，未保存 - {parsed_filename}"
            print(f"[TextSaver] {status_msg}")
            return (status_msg,)
        
        # 写入模式
        status_msg = ""
        
        try:
            if 附加 == "仅新增":
                if os.path.exists(file_path):
                    status_msg = f"⏭️ 文件已存在，跳过写入: {parsed_filename}"
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    status_msg = f"✅ 新增文件成功: {parsed_filename}"
                    
            elif 附加 == "覆盖":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                status_msg = f"✅ 覆盖写入成功: {parsed_filename}"
                
            else:  # 追加模式
                with open(file_path, 'a', encoding='utf-8') as f:
                    # 只在需要添加分隔符时才添加
                    if 插入新行 and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        f.write('\n')
                    f.write(content)
                status_msg = f"✅ 追加写入成功: {parsed_filename}"
                
        except Exception as e:
            status_msg = f"❌ 写入失败: {str(e)}"
            print(f"[TextSaver] 错误: {e}")
        
        print(f"[TextSaver] {status_msg} - {file_path}")
        
        return (status_msg,)


NODE_CLASS_MAPPINGS = {
    "TextSaver": TextSaver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextSaver": "📝 保存文本(高级)",
}