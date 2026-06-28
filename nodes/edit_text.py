class EditText:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "forceInput": False,
                        "print_to_screen": True,
                    },
                ),
            },
            "optional": {
                "编辑文本": (
                    "STRING",
                    {"default": "", "multiline": True, "forceInput": True},
                )
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_NODE = True
    FUNCTION = "edit_text"
    CATEGORY = "🥣 清粥小菜工具箱"

    def edit_text(self, text="", 编辑文本=""):
        if 编辑文本 != "":
            text = 编辑文本
            return {"ui": {"text": text}, "result": (text,)}
        else:
            return (text,)