# ultraSwitch.py
from comfy_execution.graph import ExecutionBlocker

class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False
    def __eq__(self, __value: object) -> bool:
        return True
    def __str__(self):
        return "*"

ANY = AnyType("*")

class UltraSwitch:
    """动态输入开关 - 自动选择第一个有效输入（最多20路）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # 动态生成输入定义
        inputs = {
            "required": {
                "接入数量": (["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"], 
                               {"default": "2", "tooltip": "输入数量（1-20）"}),
            },
            "optional": {
                "输入_1": (ANY, {"optional": True}),
            }
        }
        # 动态添加 输入_2 到 输入_20 到可选参数
        for i in range(2, 21):
            inputs["optional"][f"输入_{i}"] = (ANY, {"optional": True})
        
        return inputs
    
    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("输出任意",)
    FUNCTION = "check_auto"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def check_auto(self, 接入数量, **kwargs):
        """自动模式：按顺序返回第一个有效输入"""
        接入数量 = int(接入数量)
        
        for i in range(1, 接入数量 + 1):
            input_key = f"输入_{i}"
            input_value = kwargs.get(input_key, None)
            
            if self._is_valid_input(input_value):
                print(f"[万能判断切换] 自动模式 - 使用 输入_{i}")
                return (input_value,)
        
        print("[万能判断切换] 自动模式 - 没有找到有效输入")
        return (None,)
    
    def _is_valid_input(self, input_value) -> bool:
        """检查输入是否有效"""
        if input_value is None or isinstance(input_value, ExecutionBlocker):
            return False
        
        if isinstance(input_value, dict) and 'samples' in input_value:
            try:
                samples = input_value['samples']
                if hasattr(samples, 'any') and not samples.any():
                    return False
            except Exception:
                pass
        
        if isinstance(input_value, (list, dict, tuple)) and len(input_value) == 0:
            return False
        
        if isinstance(input_value, str) and input_value == "":
            return False
        
        return True


class UltraSwitchSelect:
    """手动选择开关 - 手动指定使用哪一路输入（最多20路）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        # 生成选择列表
        select_options = []
        for i in range(1, 21):
            select_options.append((f"选择输入{i}", {"default": "选择输入1" if i == 1 else ""}))
        
        inputs = {
            "required": {
                "接入数量": (["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"], 
                               {"default": "2", "tooltip": "输入数量（1-20）"}),
                "选择": (tuple([f"选择输入{i}" for i in range(1, 21)]), 
                        {"default": "选择输入1", "tooltip": "手动选择使用哪一路输入"}),
            },
            "optional": {
                "输入_1": (ANY, {"optional": True}),
            }
        }
        # 动态添加 输入_2 到 输入_20 到可选参数
        for i in range(2, 21):
            inputs["optional"][f"输入_{i}"] = (ANY, {"optional": True})
        
        return inputs
    
    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("输出任意",)
    FUNCTION = "check_manual"
    CATEGORY = "🥣 清粥小菜工具箱"
    
    def check_manual(self, 接入数量, 选择, **kwargs):
        """手动模式：返回指定索引的输入"""
        接入数量 = int(接入数量)
        
        # 从 "选择输入X" 中提取数字
        select_index = int(选择.replace("选择输入", ""))
        
        # 检查选择是否有效
        if select_index < 1 or select_index > 接入数量:
            print(f"[万能判断切换] 错误: 选择的索引 {select_index} 超出范围 1-{接入数量}")
            return (None,)
        
        input_key = f"输入_{select_index}"
        input_value = kwargs.get(input_key, None)
        
        if self._is_valid_input(input_value):
            print(f"[万能判断切换] 手动模式 - 使用 {选择}")
            return (input_value,)
        else:
            print(f"[万能判断切换] 手动模式 - {选择} 无效，尝试查找其他有效输入")
            # 如果选中的输入无效，尝试其他输入
            for i in range(1, 接入数量 + 1):
                if i == select_index:
                    continue
                input_key = f"输入_{i}"
                input_value = kwargs.get(input_key, None)
                if self._is_valid_input(input_value):
                    print(f"[万能判断切换] 手动模式 - 备用使用 输入_{i}")
                    return (input_value,)
        
        print("[万能判断切换] 手动模式 - 没有找到有效输入")
        return (None,)
    
    def _is_valid_input(self, input_value) -> bool:
        """检查输入是否有效"""
        if input_value is None or isinstance(input_value, ExecutionBlocker):
            return False
        
        if isinstance(input_value, dict) and 'samples' in input_value:
            try:
                samples = input_value['samples']
                if hasattr(samples, 'any') and not samples.any():
                    return False
            except Exception:
                pass
        
        if isinstance(input_value, (list, dict, tuple)) and len(input_value) == 0:
            return False
        
        if isinstance(input_value, str) and input_value == "":
            return False
        
        return True


NODE_CLASS_MAPPINGS = {
    "UltraSwitch": UltraSwitch,
    "UltraSwitchSelect": UltraSwitchSelect,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UltraSwitch": "万能判断切换(自动)",
    "UltraSwitchSelect": "万能判断切换(手动)",
}