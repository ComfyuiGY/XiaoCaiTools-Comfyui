# -*- coding: utf-8 -*-
import os
import random
from pathlib import Path
from typing import List, Dict
import folder_paths


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


any_type = AnyType("*")


class TextFileStorage:
    """存储文本文件状态"""
    file_list: List[str] = []
    file_names: List[str] = []
    current_index: int = 0
    last_read_file: str = ""
    last_read_content: str = ""
    fixed_file: str = ""
    fixed_filename: str = ""
    last_folder: str = ""
    last_extensions: str = ""
    last_include_sub: bool = False
    file_cache: Dict[str, str] = {}
    
    @classmethod
    def clear_cache(cls):
        """清空缓存"""
        cls.file_cache.clear()
    
    @classmethod
    def get_file_content(cls, file_path: str) -> str:
        """获取文件内容（带缓存）"""
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
    def scan_folder(cls, folder_path: str, extensions: List[str] = None, include_sub: bool = False) -> List[str]:
        """扫描文件夹中的文本文件"""
        if extensions is None:
            extensions = ['.txt', '.md', '.json', '.csv', '.py', '.js', '.html', '.css', '.xml']
        
        files = []
        folder = Path(folder_path)
        
        if not folder.exists():
            # 尝试创建文件夹
            try:
                folder.mkdir(parents=True, exist_ok=True)
                print(f"已创建文件夹: {folder_path}")
            except Exception as e:
                print(f"无法创建文件夹 {folder_path}: {str(e)}")
                return []
        
        try:
            if include_sub:
                for ext in extensions:
                    files.extend(folder.rglob(f"*{ext}"))
                    files.extend(folder.rglob(f"*{ext.upper()}"))
            else:
                for ext in extensions:
                    files.extend(folder.glob(f"*{ext}"))
                    files.extend(folder.glob(f"*{ext.upper()}"))
        except Exception as e:
            print(f"扫描文件夹出错: {str(e)}")
            return []
        
        # 排序确保顺序一致
        return sorted([str(f) for f in files])
    
    @classmethod
    def update_file_list(cls, folder_path: str, extensions: str, include_sub: bool):
        """更新文件列表和文件名列表"""
        # 解析扩展名
        ext_list = [ext.strip() for ext in extensions.split(",") if ext.strip()]
        if not ext_list:
            ext_list = ['.txt', '.md', '.json']
        ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
        
        # 扫描文件
        files = cls.scan_folder(folder_path, ext_list, include_sub)
        cls.file_list = files
        cls.file_names = [os.path.basename(f) for f in files]
        cls.last_folder = folder_path
        cls.last_extensions = extensions
        cls.last_include_sub = include_sub
        
        return len(files)


class TextFileReader:
    """
    文本文件读取器
    支持顺序读取、随机读取、固定读取、索引读取
    """
    @classmethod
    def INPUT_TYPES(cls):
        # 获取 models 目录下的 text 文件夹路径作为默认值
        text_dir = os.path.join(folder_paths.models_dir, "text")
        
        return {
            "required": {
                "读取模式": (["顺序读取", "随机读取", "固定读取", "索引读取"], {
                    "default": "顺序读取",
                    "tooltip": "选择文件读取方式\n- 顺序读取：循环读取文件夹中的文件\n- 随机读取：随机选择文件\n- 固定读取：始终读取指定的固定文件\n- 索引读取：根据索引读取指定文件"
                }),
                "文件夹路径": ("STRING", {
                    "default": text_dir,
                    "multiline": False,
                    "tooltip": "文本文件所在的文件夹路径"
                }),
                "文件扩展名": ("STRING", {
                    "default": ".txt,.md,.json",
                    "multiline": False,
                    "tooltip": "支持的文件扩展名，用逗号分隔"
                }),
            },
            "optional": {
                "固定文件名": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "固定读取模式：输入要固定的文件名（如：example.txt）\n留空则使用第一个文件"
                }),
                "索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                    "tooltip": "索引读取模式：指定读取第几个文件（从0开始）"
                }),
                "自动刷新": ("BOOLEAN", {
                    "default": False,
                    "label_on": "自动刷新",
                    "label_off": "固定",
                    "tooltip": "是否在每次执行时重新扫描文件夹"
                }),
                "包含子文件夹": ("BOOLEAN", {
                    "default": False,
                    "label_on": "包含子文件夹",
                    "label_off": "仅当前文件夹",
                    "tooltip": "是否扫描子文件夹中的文件"
                }),
                "创建文件夹": ("BOOLEAN", {
                    "default": True,
                    "label_on": "自动创建",
                    "label_off": "不创建",
                    "tooltip": "如果文件夹不存在，是否自动创建"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("文本内容", "文件名", "当前索引", "状态信息")
    FUNCTION = "read_text"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def __init__(self):
        self.current_index = 0
    
    @classmethod
    def IS_CHANGED(cls, 读取模式, 文件夹路径, 文件扩展名, 固定文件名="", 索引=0, 
                   自动刷新=False, 包含子文件夹=False, 创建文件夹=True):
        """告诉 ComfyUI 节点何时需要重新执行"""
        if 读取模式 == "随机读取":
            # 随机模式下每次都重新执行
            return float("nan")
        elif 自动刷新:
            # 自动刷新模式，每次都重新执行
            return float("nan")
        return (读取模式, 文件夹路径, 索引, 固定文件名, 文件扩展名)
    
    def read_text(self, 读取模式, 文件夹路径, 文件扩展名, 固定文件名="", 索引=0, 
                  自动刷新=False, 包含子文件夹=False, 创建文件夹=True):
        """
        读取文本文件
        """
        # 检查文件夹是否存在
        folder = Path(文件夹路径)
        if not folder.exists():
            if 创建文件夹:
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    status_msg = f"📁 已创建文件夹: {文件夹路径}\n请将文本文件放入该文件夹"
                    return (status_msg, "无文件", -1, status_msg)
                except Exception as e:
                    error_msg = f"❌ 无法创建文件夹: {文件夹路径}\n错误: {str(e)}"
                    return (error_msg, "无文件", -1, error_msg)
            else:
                error_msg = f"❌ 文件夹不存在: {文件夹路径}\n请创建文件夹或启用'创建文件夹'选项"
                return (error_msg, "无文件", -1, error_msg)
        
        # 检查是否需要重新扫描文件夹
        need_scan = (自动刷新 or 
                    TextFileStorage.last_folder != 文件夹路径 or 
                    TextFileStorage.last_extensions != 文件扩展名 or
                    TextFileStorage.last_include_sub != 包含子文件夹)
        
        if need_scan:
            file_count = TextFileStorage.update_file_list(文件夹路径, 文件扩展名, 包含子文件夹)
            
            # 如果扫描后没有文件，返回提示
            if file_count == 0:
                # 获取支持的扩展名列表用于显示
                ext_list = [ext.strip() for ext in 文件扩展名.split(",") if ext.strip()]
                if not ext_list:
                    ext_list = ['.txt', '.md', '.json']
                
                # 创建一个示例文件
                example_file = folder / "示例文件.txt"
                if not example_file.exists():
                    try:
                        with open(example_file, 'w', encoding='utf-8') as f:
                            f.write("这是一个示例文本文件。\n\n请将您的文本文件放入此文件夹。\n\n支持的格式: " + ", ".join(ext_list))
                    except:
                        pass
                
                status_msg = f"⚠️ 未找到文本文件\n📁 文件夹: {文件夹路径}\n📄 支持格式: {文件扩展名}\n💡 已创建示例文件，请放入您的文本文件"
                return (status_msg, "无文件", -1, status_msg)
        
        if not TextFileStorage.file_list:
            status_msg = f"⚠️ 未找到文本文件\n📁 文件夹: {文件夹路径}\n📄 支持格式: {文件扩展名}"
            return (status_msg, "无文件", -1, status_msg)
        
        # 根据模式选择文件
        if 读取模式 == "顺序读取":
            # 顺序读取：每次读取下一个文件
            file_path = TextFileStorage.file_list[self.current_index]
            current_idx = self.current_index
            # 更新索引供下次使用
            self.current_index = (self.current_index + 1) % len(TextFileStorage.file_list)
            status = f"🔄 顺序读取 [{current_idx + 1}/{len(TextFileStorage.file_list)}]"
            
        elif 读取模式 == "随机读取":
            # 随机读取：完全随机选择
            current_idx = random.randint(0, len(TextFileStorage.file_list) - 1)
            file_path = TextFileStorage.file_list[current_idx]
            status = f"🎲 随机读取 [{current_idx + 1}/{len(TextFileStorage.file_list)}]"
            
        elif 读取模式 == "固定读取":
            # 固定读取：根据输入的固定文件名
            if 固定文件名 and 固定文件名.strip():
                # 查找指定的文件
                found = False
                for idx, f in enumerate(TextFileStorage.file_list):
                    if os.path.basename(f) == 固定文件名.strip():
                        file_path = f
                        current_idx = idx
                        found = True
                        break
                
                if not found:
                    # 如果没找到，使用第一个文件并提示
                    file_path = TextFileStorage.file_list[0]
                    current_idx = 0
                    status = f"⚠️ 未找到文件 '{固定文件名}'，已使用第一个文件"
                else:
                    status = f"📌 固定读取: {固定文件名}"
            else:
                # 没有指定文件名，使用第一个文件
                file_path = TextFileStorage.file_list[0]
                current_idx = 0
                status = f"📌 固定读取(默认): {os.path.basename(file_path)}"
            
        else:  # 索引读取
            # 索引读取：根据指定索引读取
            current_idx = min(索引, len(TextFileStorage.file_list) - 1)
            file_path = TextFileStorage.file_list[current_idx]
            status = f"🔢 索引读取 [{current_idx + 1}/{len(TextFileStorage.file_list)}]"
        
        # 读取文件内容
        try:
            content = TextFileStorage.get_file_content(file_path)
            filename = os.path.basename(file_path)
            
            # 获取文件大小
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
            
            # 构建状态信息
            status_info = f"{status}\n📄 文件: {filename}\n📊 大小: {size_str}\n📍 索引: {current_idx}\n📁 路径: {文件夹路径}"
            
            # 添加文件列表信息
            if len(TextFileStorage.file_list) > 1:
                file_list_preview = ", ".join(TextFileStorage.file_names[:5])
                if len(TextFileStorage.file_names) > 5:
                    file_list_preview += f" 等 {len(TextFileStorage.file_names)} 个文件"
                status_info += f"\n📚 文件列表: {file_list_preview}"
            
            return (content, filename, current_idx, status_info)
            
        except Exception as e:
            error_msg = f"❌ 读取文件失败: {str(e)}"
            return (error_msg, "读取失败", -1, error_msg)


class TextBatchReader:
    """
    批量文本读取器
    一次性读取多个文本文件
    """
    @classmethod
    def INPUT_TYPES(cls):
        text_dir = os.path.join(folder_paths.models_dir, "text")
        
        return {
            "required": {
                "文件夹路径": ("STRING", {
                    "default": text_dir,
                    "multiline": False,
                    "tooltip": "文本文件所在的文件夹路径"
                }),
                "读取数量": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "要读取的文件数量"
                }),
                "读取方式": (["顺序", "随机", "索引范围"], {
                    "default": "顺序",
                    "tooltip": "选择文件读取方式\n- 顺序：从头开始读取指定数量\n- 随机：随机选择指定数量\n- 索引范围：读取指定索引范围内的文件"
                }),
                "文件扩展名": ("STRING", {
                    "default": ".txt,.md,.json",
                    "multiline": False,
                    "tooltip": "支持的文件扩展名"
                }),
            },
            "optional": {
                "起始索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                    "tooltip": "索引范围模式：起始索引"
                }),
                "结束索引": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 999999,
                    "step": 1,
                    "tooltip": "索引范围模式：结束索引"
                }),
                "包含子文件夹": ("BOOLEAN", {
                    "default": False,
                    "label_on": "包含子文件夹",
                    "label_off": "仅当前文件夹",
                }),
                "分隔符": ("STRING", {
                    "default": "\n---\n",
                    "multiline": False,
                    "tooltip": "多个文件内容之间的分隔符"
                }),
                "创建文件夹": ("BOOLEAN", {
                    "default": True,
                    "label_on": "自动创建",
                    "label_off": "不创建",
                    "tooltip": "如果文件夹不存在，是否自动创建"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "STRING")
    RETURN_NAMES = ("合并文本", "文件数量", "状态信息")
    FUNCTION = "read_batch"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def __init__(self):
        self.last_folder = ""
        self.last_extensions = ""
        self.file_list = []
    
    def read_batch(self, 文件夹路径, 读取数量, 读取方式, 文件扩展名, 
                   起始索引=0, 结束索引=10, 包含子文件夹=False, 分隔符="\n---\n", 创建文件夹=True):
        """
        批量读取文本文件
        """
        # 检查文件夹是否存在
        folder = Path(文件夹路径)
        if not folder.exists():
            if 创建文件夹:
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    return (f"📁 已创建文件夹: {文件夹路径}\n请将文本文件放入该文件夹", 0, "文件夹已创建")
                except Exception as e:
                    return (f"❌ 无法创建文件夹: {文件夹路径}", 0, f"错误: {str(e)}")
            else:
                return (f"❌ 文件夹不存在: {文件夹路径}", 0, "请创建文件夹或启用'创建文件夹'选项")
        
        # 检查是否需要重新扫描
        need_scan = (self.last_folder != 文件夹路径 or 
                    self.last_extensions != 文件扩展名)
        
        if need_scan:
            # 解析扩展名
            ext_list = [ext.strip() for ext in 文件扩展名.split(",") if ext.strip()]
            if not ext_list:
                ext_list = ['.txt', '.md', '.json']
            ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
            
            # 扫描文件
            files = []
            if 包含子文件夹:
                for ext in ext_list:
                    files.extend(folder.rglob(f"*{ext}"))
            else:
                for ext in ext_list:
                    files.extend(folder.glob(f"*{ext}"))
            
            self.file_list = sorted([str(f) for f in files])
            self.last_folder = 文件夹路径
            self.last_extensions = 文件扩展名
        
        if not self.file_list:
            return (f"⚠️ 未找到文本文件\n📁 文件夹: {文件夹路径}\n📄 支持格式: {文件扩展名}", 0, "未找到文件")
        
        # 根据读取方式选择文件
        selected_files = []
        
        if 读取方式 == "顺序":
            count = min(读取数量, len(self.file_list))
            selected_files = self.file_list[:count]
            status = f"📖 顺序读取: 前 {count} 个文件"
            
        elif 读取方式 == "随机":
            count = min(读取数量, len(self.file_list))
            selected_files = random.sample(self.file_list, count)
            status = f"🎲 随机读取: {count} 个文件"
            
        else:
            start = max(0, min(起始索引, len(self.file_list) - 1))
            end = min(结束索引 + 1, len(self.file_list))
            selected_files = self.file_list[start:end]
            status = f"🔢 索引范围读取: [{start} - {end-1}] 共 {len(selected_files)} 个文件"
        
        # 读取文件内容
        contents = []
        file_names = []
        for file_path in selected_files:
            content = TextFileStorage.get_file_content(file_path)
            filename = os.path.basename(file_path)
            file_names.append(filename)
            contents.append(f"【{filename}】\n{content}")
        
        # 合并内容
        merged_text = 分隔符.join(contents)
        
        # 构建状态信息
        file_list_str = ", ".join(file_names[:5])
        if len(file_names) > 5:
            file_list_str += f" 等 {len(file_names)} 个文件"
        
        status_info = f"{status}\n📄 文件: {file_list_str}\n📊 总计: {len(selected_files)} 个文件"
        
        return (merged_text, len(selected_files), status_info)


class TextFolderScanner:
    """
    文件夹文本扫描器
    扫描并列出文件夹中的所有文本文件
    """
    @classmethod
    def INPUT_TYPES(cls):
        text_dir = os.path.join(folder_paths.models_dir, "text")
        
        return {
            "required": {
                "文件夹路径": ("STRING", {
                    "default": text_dir,
                    "multiline": False,
                    "tooltip": "要扫描的文件夹路径"
                }),
                "文件扩展名": ("STRING", {
                    "default": ".txt,.md,.json,.csv",
                    "multiline": False,
                    "tooltip": "要扫描的文件扩展名"
                }),
            },
            "optional": {
                "包含子文件夹": ("BOOLEAN", {
                    "default": True,
                    "label_on": "包含子文件夹",
                    "label_off": "仅当前文件夹",
                }),
                "显示完整路径": ("BOOLEAN", {
                    "default": False,
                    "label_on": "显示完整路径",
                    "label_off": "仅文件名",
                }),
                "关键词过滤": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "只显示包含关键词的文件（留空不过滤）"
                }),
                "创建文件夹": ("BOOLEAN", {
                    "default": True,
                    "label_on": "自动创建",
                    "label_off": "不创建",
                    "tooltip": "如果文件夹不存在，是否自动创建"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "STRING")
    RETURN_NAMES = ("文件列表", "文件数量", "详细信息")
    FUNCTION = "scan_folder"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def scan_folder(self, 文件夹路径, 文件扩展名, 包含子文件夹=True, 
                    显示完整路径=False, 关键词过滤="", 创建文件夹=True):
        """
        扫描文件夹并列出文本文件
        """
        # 检查文件夹
        folder = Path(文件夹路径)
        if not folder.exists():
            if 创建文件夹:
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    return (f"📁 已创建文件夹: {文件夹路径}\n请将文本文件放入该文件夹", 0, "文件夹已创建")
                except Exception as e:
                    return (f"❌ 无法创建文件夹: {文件夹路径}", 0, f"错误: {str(e)}")
            else:
                return (f"❌ 文件夹不存在: {文件夹路径}", 0, "请创建文件夹或启用'创建文件夹'选项")
        
        # 解析扩展名
        ext_list = [ext.strip() for ext in 文件扩展名.split(",") if ext.strip()]
        if not ext_list:
            ext_list = ['.txt', '.md', '.json', '.csv']
        ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
        
        # 扫描文件
        files = []
        if 包含子文件夹:
            for ext in ext_list:
                files.extend(folder.rglob(f"*{ext}"))
        else:
            for ext in ext_list:
                files.extend(folder.glob(f"*{ext}"))
        
        # 排序
        files = sorted(files)
        
        # 关键词过滤
        if 关键词过滤:
            keyword = 关键词过滤.lower()
            files = [f for f in files if keyword in str(f).lower() or keyword in f.name.lower()]
        
        if not files:
            return ("未找到匹配的文件", 0, f"在 {文件夹路径} 中没有找到 {文件扩展名} 文件")
        
        # 格式化输出
        file_list = []
        for f in files:
            if 显示完整路径:
                file_list.append(str(f))
            else:
                file_list.append(f.name)
        
        # 统计信息
        total_size = sum(f.stat().st_size for f in files)
        size_mb = total_size / (1024 * 1024)
        
        details = f"✅ 找到 {len(files)} 个文件，总大小: {size_mb:.2f} MB"
        
        return ("\n".join(file_list), len(files), details)


# 扩展节点映射
NODE_CLASS_MAPPINGS = {
    "TextFileReader": TextFileReader,
    "TextBatchReader": TextBatchReader,
    "TextFolderScanner": TextFolderScanner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextFileReader": "📄 文本文件读取器",
    "TextBatchReader": "📚 批量文本读取器",
    "TextFolderScanner": "🔍 文件夹文本扫描器",
}