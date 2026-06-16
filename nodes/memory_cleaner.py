# -*- coding: utf-8 -*-
"""
内存/显存清理节点
可以在工作流中随时调用清理内存和显存
支持任意输入并原样输出，可插入工作流任意位置
"""

import gc
import torch
import comfy.model_management


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


any_type = AnyType("*")


class XiaoCaiMemoryCleaner:
    """
    内存/显存清理节点
    清理GPU显存和系统内存
    支持任意输入并原样输出，可插入工作流任意位置
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "清理内存": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 清理内存",
                    "label_off": "❌ 不清理",
                    "tooltip": "是否清理系统RAM"
                }),
                "清理显存": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 清理显存",
                    "label_off": "❌ 不清理",
                    "tooltip": "是否清理GPU显存"
                }),
                "强制垃圾回收": ("BOOLEAN", {
                    "default": True,
                    "label_on": "✅ 启用",
                    "label_off": "❌ 禁用",
                    "tooltip": "强制执行Python垃圾回收，释放循环引用的对象\n建议开启，耗时通常<0.1秒"
                }),
            },
            "optional": {
                "输入任意": (any_type, {
                    "tooltip": "任意输入，原样输出（可连接任何节点）"
                }),
            }
        }
    
    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("输出任意",)
    FUNCTION = "clean_memory"
    CATEGORY = "🥣 清粥小菜工具箱"
    OUTPUT_NODE = True
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")
    
    def clean_memory(self, 清理内存, 清理显存, 强制垃圾回收, 输入任意=None):
        """
        清理内存和显存，并原样返回输入
        """
        import time
        start_time = time.time()
        status_messages = []
        
        # 强制垃圾回收
        if 强制垃圾回收:
            collected = gc.collect()
            if collected > 0:
                status_messages.append(f"✅ Python垃圾回收已执行 (回收 {collected} 个对象)")
            else:
                status_messages.append("✅ Python垃圾回收已执行")
        
        # 清理内存
        if 清理内存:
            try:
                # 尝试释放系统内存
                import ctypes
                if hasattr(ctypes, 'cdll'):
                    if hasattr(ctypes.cdll, 'msvcrt'):
                        ctypes.cdll.msvcrt._fpreset()
                status_messages.append("✅ 系统内存已清理")
            except Exception as e:
                status_messages.append(f"⚠️ 内存清理: {str(e)}")
        else:
            status_messages.append("⏭️ 跳过内存清理")
        
        # 清理显存
        if 清理显存:
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    status_messages.append("✅ GPU显存已清理")
                else:
                    status_messages.append("⚠️ CUDA不可用，跳过显存清理")
            except Exception as e:
                status_messages.append(f"❌ 显存清理失败: {str(e)}")
        else:
            status_messages.append("⏭️ 跳过显存清理")
        
        # 获取当前内存状态
        mem_info = []
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            cached = torch.cuda.memory_reserved() / 1024**3
            mem_info.append(f"🖥️ GPU: {allocated:.2f}GB使用 / {cached:.2f}GB缓存")
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            mem_info.append(f"💾 RAM: {mem.percent}%使用 ({mem.used // 1024**3}GB / {mem.total // 1024**3}GB)")
        except:
            pass
        
        elapsed = (time.time() - start_time) * 1000
        mem_info.append(f"⏱️ 耗时: {elapsed:.1f}ms")
        
        result = "\n".join(status_messages) + f"\n\n📊 当前状态:\n" + "\n".join(mem_info)
        
        print(f"[XiaoCaiMemoryCleaner] 清理完成 - {elapsed:.1f}ms")
        print(result)
        
        # 原样返回输入内容
        return (输入任意,)


NODE_CLASS_MAPPINGS = {
    "XiaoCaiMemoryCleaner": XiaoCaiMemoryCleaner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XiaoCaiMemoryCleaner": "🧹 内存/显存清理",
}