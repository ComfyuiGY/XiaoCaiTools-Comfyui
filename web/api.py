# web/api.py
import json
import os
from pathlib import Path
from aiohttp import web
from server import PromptServer


def get_comfyui_base_path():
    """获取 ComfyUI 基础路径"""
    try:
        import folder_paths
        return folder_paths.base_path
    except:
        pass
    
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.basename(current) == 'ComfyUI':
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_options_from_file(filename):
    """从文件读取选项列表"""
    if not filename or filename == "无可用文件":
        return []
    
    base_path = get_comfyui_base_path()
    file_path = Path(base_path) / "input" / "wildcards" / f"{filename}.txt"
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for line in f.readlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        lines.append(line)
                return lines
        except Exception as e:
            print(f"[TextListSelector API] 读取失败: {e}")
            return []
    
    return []


# ========== 文本文件读取器 API ==========
def scan_text_files(folder_path, extensions_str):
    """扫描文本文件，返回文件名列表"""
    if not folder_path or not os.path.exists(folder_path):
        return []
    
    extensions = [ext.strip() for ext in extensions_str.split(",") if ext.strip()]
    if not extensions:
        extensions = ['.txt', '.md', '.json']
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    folder = Path(folder_path)
    if not folder.exists():
        return []
    
    files = []
    try:
        for ext in extensions:
            files.extend(folder.glob(f"*{ext}"))
    except Exception as e:
        print(f"[TextFileReader API] 扫描失败: {e}")
        return []
    
    return sorted([f.name for f in files])


@PromptServer.instance.routes.get("/api/textfilereader/files")
async def get_text_files(request):
    """获取文本文件列表 API"""
    try:
        folder_path = request.query.get("folder", "")
        extensions = request.query.get("extensions", ".txt,.md,.json")
        
        print(f"[TextFileReader API] 请求: folder={folder_path}")
        
        if not folder_path:
            return web.json_response({"success": False, "files": [], "error": "文件夹路径为空"}, status=400)
        
        if not os.path.exists(folder_path):
            return web.json_response({"success": True, "files": [], "error": "文件夹不存在"})
        
        files = scan_text_files(folder_path, extensions)
        
        print(f"[TextFileReader API] 找到 {len(files)} 个文件")
        
        return web.json_response({"success": True, "files": files})
    except Exception as e:
        print(f"[TextFileReader API] 错误: {e}")
        return web.json_response({"success": False, "files": [], "error": str(e)}, status=500)


# ========== 原有 API ==========
@PromptServer.instance.routes.get("/api/textlistselector/options")
async def get_options(request):
    """获取文件选项 API"""
    try:
        filename = request.query.get("filename", "")
        if not filename:
            return web.json_response({"success": False, "options": []}, status=400)
        
        print(f"[TextListSelector API] 请求: {filename}")
        options = get_options_from_file(filename)
        return web.json_response({"success": True, "options": options})
    except Exception as e:
        print(f"[TextListSelector API] 错误: {e}")
        return web.json_response({"success": False, "error": str(e), "options": []}, status=500)


print("[API] 已加载 - TextListSelector + TextFileReader")