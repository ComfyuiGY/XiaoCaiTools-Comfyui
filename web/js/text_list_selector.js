// web/js/text_list_selector.js
import { app } from "../../../scripts/app.js";

// 获取文件选项的 API 函数
async function fetchOptions(filename) {
    if (!filename || filename === "无可用文件") {
        return [];
    }
    
    try {
        const response = await fetch(`/api/textlistselector/options?filename=${encodeURIComponent(filename)}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.options) {
                return data.options;
            }
        }
    } catch (error) {
        console.error("[TextListSelector] 获取选项失败:", error);
    }
    return [];
}

// 更新选项下拉列表
function updateOptionsWidget(node, options) {
    const optionsWidget = node.widgets?.find(w => w.name === "选项列表");
    if (!optionsWidget) return;
    
    if (options && options.length > 0) {
        const currentValue = optionsWidget.value;
        optionsWidget.options.values = options;
        
        if (currentValue && options.includes(currentValue)) {
            optionsWidget.value = currentValue;
        } else {
            optionsWidget.value = options[0];
        }
    } else {
        optionsWidget.options.values = ["无可用选项"];
        optionsWidget.value = "无可用选项";
    }
    
    node.setSize?.(node.computeSize());
    if (app.canvas) app.canvas.setDirty(true);
}

app.registerExtension({
    name: "ComfyUI.TextListSelector",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "TextListSelector") {
            return;
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        
        nodeType.prototype.onNodeCreated = function() {
            const result = onNodeCreated?.apply(this, arguments);
            
            const node = this;
            const fileWidget = node.widgets?.find(w => w.name === "文件列表");
            
            if (!fileWidget) return result;
            
            // 创建刷新按钮
            const refreshButton = {
                name: "🔄 刷新选项列表",
                type: "button",
                callback: async () => {
                    console.log("[TextListSelector] 点击刷新按钮");
                    const currentFile = fileWidget.value;
                    if (currentFile && currentFile !== "无可用文件") {
                        const options = await fetchOptions(currentFile);
                        updateOptionsWidget(node, options);
                    }
                    
                    if (node.graph) {
                        node.graph.afterChange();
                    }
                    if (app.canvas) {
                        app.canvas.setDirty(true);
                    }
                }
            };
            
            node.addCustomWidget(refreshButton);
            node.setSize?.(node.computeSize());
            
            if (app.canvas) {
                app.canvas.setDirty(true);
            }
            
            return result;
        };
    }
});