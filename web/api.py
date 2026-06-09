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
    
    # 只使用 input/wildcards 路径
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


print("[TextListSelector API] 已加载")