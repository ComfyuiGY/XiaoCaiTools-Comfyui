# -*- coding: utf-8 -*-
"""
忽略分组节点 - 通过开关控制工作流中各编组的忽略/旁路状态
"""

import os
import sys
import json
import folder_paths


class XiaoCaiIgnoreGroups:
    """忽略分组 - 通过开关控制工作流中各编组的忽略/旁路状态"""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    FUNCTION = "execute"
    CATEGORY = "🥣 清粥小菜工具箱"
    OUTPUT_NODE = True

    def execute(self):
        return ()


NODE_CLASS_MAPPINGS = {
    "XiaoCaiIgnoreGroups": XiaoCaiIgnoreGroups,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XiaoCaiIgnoreGroups": "忽略分组",
}