# -*- coding: utf-8 -*-
import os
import random
from pathlib import Path
from typing import List, Dict
import folder_paths


class TextFileStorage:
    """存储文本文件状态"""
    file_cache: Dict[str, str] = {}
    
    @classmethod
    def clear_cache(cls):
        cls.file_cache.clear()
    
    @classmethod
    def get_file_content(cls, file_path: str) -> str:
        if file_path in cls.file_cache:
            return cls.file_cache[file_path]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            cls.file_cache[file_path] = content
            return content
        except Exception as e:
            return f"读取文件失败: {str(e)}"
    
    @classmethod
    def get_file_line_count(cls, file_path: str) -> int:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception as e:
            return 0
    
    @classmethod
    def scan_folder(cls, folder_path: str, extensions: List[str] = None) -> List[str]:
        if extensions is None:
            extensions = ['.txt', '.md', '.json']
        
        files = []
        folder = Path(folder_path)
        
        if not folder.exists():
            return []
        
        try:
            for ext in extensions:
                files.extend(folder.glob(f"*{ext}"))
        except Exception:
            pass
        
        return sorted([str(f) for f in files])
    
    @classmethod
    def get_file_names(cls, folder_path: str, extensions: List[str] = None) -> List[str]:
        if extensions is None:
            extensions = ['.txt', '.md', '.json']
        
        files = cls.scan_folder(folder_path, extensions)
        return [os.path.basename(f) for f in files]


class XiaoCaiTextFileReader:
    """
    文本文件读取器
    支持顺序读取、随机读取、固定读取、索引读取
    固定读取文件夹: ComfyUI/output
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 固定使用 output 文件夹
        output_dir = folder_paths.output_directory
        
        # 获取实际文件列表
        actual_files = TextFileStorage.get_file_names(output_dir)
        if not actual_files:
            actual_files = ["无可用文件"]
        
        return {
            "required": {
                "读取模式": (["顺序读取", "随机读取", "固定读取", "索引读取"], {
                    "default": "顺序读取",
                }),
                "固定文件名": (actual_files, {
                    "default": actual_files[0] if actual_files else "无文件",
                }),
                "索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("文本内容", "当前索引", "文件行数", "状态信息")
    FUNCTION = "read_text"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def __init__(self):
        self.current_index = 0
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")
    
    def read_text(self, 读取模式, 固定文件名, 索引):
        
        # 固定使用 output 文件夹
        folder_path = folder_paths.output_directory
        folder = Path(folder_path)
        
        if not folder.exists():
            error_msg = f"❌ 文件夹不存在: {folder_path}"
            return (error_msg, -1, 0, error_msg)
        
        # 每次执行都重新扫描文件列表
        extensions = ['.txt', '.md', '.json']
        files = []
        for ext in extensions:
            files.extend(folder.glob(f"*{ext}"))
        
        file_list = sorted([str(f) for f in files])
        file_names = [os.path.basename(f) for f in file_list]
        
        if not file_list:
            status_msg = f"⚠️ 未找到文本文件\n📁 文件夹: {folder_path}\n📄 支持格式: .txt, .md, .json"
            return (status_msg, -1, 0, status_msg)
        
        # 根据模式选择文件
        if 读取模式 == "顺序读取":
            file_path = file_list[self.current_index]
            current_idx = self.current_index
            self.current_index = (self.current_index + 1) % len(file_list)
            status = f"🔄 顺序读取 [{current_idx + 1}/{len(file_list)}]"
            
        elif 读取模式 == "随机读取":
            current_idx = random.randint(0, len(file_list) - 1)
            file_path = file_list[current_idx]
            status = f"🎲 随机读取 [{current_idx + 1}/{len(file_list)}]"
            
        elif 读取模式 == "固定读取":
            found = False
            for idx, f in enumerate(file_list):
                if os.path.basename(f) == 固定文件名:
                    file_path = f
                    current_idx = idx
                    found = True
                    break
            
            if not found:
                file_path = file_list[0]
                current_idx = 0
                status = f"⚠️ 未找到文件 '{固定文件名}'，已使用第一个文件: {os.path.basename(file_path)}"
            else:
                status = f"📌 固定读取: {固定文件名}"
            
        else:  # 索引读取
            current_idx = min(索引, len(file_list) - 1)
            file_path = file_list[current_idx]
            status = f"🔢 索引读取 [{current_idx + 1}/{len(file_list)}]"
        
        try:
            content = TextFileStorage.get_file_content(file_path)
            line_count = TextFileStorage.get_file_line_count(file_path)
            filename = os.path.basename(file_path)
            
            try:
                file_size = os.path.getsize(file_path)
                if file_size < 1024:
                    size_str = f"{file_size}B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f}KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f}MB"
            except:
                size_str = "未知"
            
            status_info = f"{status}\n📄 文件: {filename}\n📊 大小: {size_str}\n📍 索引: {current_idx}\n📝 行数: {line_count}\n📁 路径: {folder_path}"
            
            if len(file_names) > 1:
                file_list_preview = ", ".join(file_names[:5])
                if len(file_names) > 5:
                    file_list_preview += f" 等 {len(file_names)} 个文件"
                status_info += f"\n📚 文件列表: {file_list_preview}"
            
            return (content, current_idx, line_count, status_info)
            
        except Exception as e:
            error_msg = f"❌ 读取文件失败: {str(e)}"
            return (error_msg, -1, 0, error_msg)


class XiaoCaiTextBatchReader:
    """批量文本读取器"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "读取数量": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                }),
                "读取方式": (["顺序", "随机", "索引范围"], {
                    "default": "顺序",
                }),
                "起始索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                }),
                "结束索引": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                }),
                "分隔符": ("STRING", {
                    "default": "\n---\n",
                    "multiline": False,
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "STRING")
    RETURN_NAMES = ("合并文本", "文件数量", "状态信息")
    FUNCTION = "read_batch"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def read_batch(self, 读取数量, 读取方式, 起始索引=0, 结束索引=10, 分隔符="\n---\n"):
        
        folder_path = folder_paths.output_directory
        folder = Path(folder_path)
        
        if not folder.exists():
            return (f"❌ 文件夹不存在: {folder_path}", 0, "文件夹不存在")
        
        extensions = ['.txt', '.md', '.json']
        files = []
        for ext in extensions:
            files.extend(folder.glob(f"*{ext}"))
        
        file_list = sorted([str(f) for f in files])
        
        if not file_list:
            return (f"⚠️ 未找到文本文件\n📁 文件夹: {folder_path}", 0, "未找到文件")
        
        selected_files = []
        
        if 读取方式 == "顺序":
            count = min(读取数量, len(file_list))
            selected_files = file_list[:count]
            status = f"📖 顺序读取: 前 {count} 个文件"
            
        elif 读取方式 == "随机":
            count = min(读取数量, len(file_list))
            selected_files = random.sample(file_list, count)
            status = f"🎲 随机读取: {count} 个文件"
            
        else:
            start = max(0, min(起始索引, len(file_list) - 1))
            end = min(结束索引 + 1, len(file_list))
            selected_files = file_list[start:end]
            status = f"🔢 索引范围读取: [{start} - {end-1}] 共 {len(selected_files)} 个文件"
        
        contents = []
        file_names = []
        for file_path in selected_files:
            content = TextFileStorage.get_file_content(file_path)
            filename = os.path.basename(file_path)
            file_names.append(filename)
            contents.append(f"【{filename}】\n{content}")
        
        merged_text = 分隔符.join(contents)
        
        file_list_str = ", ".join(file_names[:5])
        if len(file_names) > 5:
            file_list_str += f" 等 {len(file_names)} 个文件"
        
        status_info = f"{status}\n📄 文件: {file_list_str}\n📊 总计: {len(selected_files)} 个文件\n📁 路径: {folder_path}"
        
        return (merged_text, len(selected_files), status_info)


class XiaoCaiTextFolderScanner:
    """文件夹文本扫描器"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "显示完整路径": ("BOOLEAN", {
                    "default": False,
                    "label_on": "显示完整路径",
                    "label_off": "仅文件名",
                }),
                "关键词过滤": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "STRING")
    RETURN_NAMES = ("文件列表", "文件数量", "详细信息")
    FUNCTION = "scan_folder"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def scan_folder(self, 显示完整路径=False, 关键词过滤=""):
        
        folder_path = folder_paths.output_directory
        folder = Path(folder_path)
        
        if not folder.exists():
            return (f"❌ 文件夹不存在: {folder_path}", 0, "文件夹不存在")
        
        extensions = ['.txt', '.md', '.json', '.csv']
        files = []
        for ext in extensions:
            files.extend(folder.glob(f"*{ext}"))
        
        files = sorted(files)
        
        if 关键词过滤:
            keyword = 关键词过滤.lower()
            files = [f for f in files if keyword in str(f).lower() or keyword in f.name.lower()]
        
        if not files:
            return ("未找到匹配的文件", 0, f"在 {folder_path} 中没有找到文本文件")
        
        file_list = []
        for f in files:
            if 显示完整路径:
                file_list.append(str(f))
            else:
                file_list.append(f.name)
        
        total_size = sum(f.stat().st_size for f in files)
        size_mb = total_size / (1024 * 1024)
        
        details = f"✅ 找到 {len(files)} 个文件，总大小: {size_mb:.2f} MB\n📁 路径: {folder_path}"
        
        return ("\n".join(file_list), len(files), details)


NODE_CLASS_MAPPINGS = {
    "XiaoCaiTextFileReader": XiaoCaiTextFileReader,
    "XiaoCaiTextBatchReader": XiaoCaiTextBatchReader,
    "XiaoCaiTextFolderScanner": XiaoCaiTextFolderScanner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XiaoCaiTextFileReader": "📄 文本文件读取器",
    "XiaoCaiTextBatchReader": "📚 批量文本读取器",
    "XiaoCaiTextFolderScanner": "🔍 文件夹文本扫描器",
}