// web/js/text_saver.js
import { app } from "../../../scripts/app.js";

// 设置节点宽度
function setNodeWidth(node, width) {
    if (node.size) {
        node.size[0] = width;
        node.setSize?.(node.size);
    }
}

// 根据根目录设置自定义路径的可用性
function setCustomPathEnabled(node, rootDir) {
    const customPathWidget = node.widgets?.find(w => w.name === "自定义路径");
    if (!customPathWidget) return;
    
    if (rootDir === "自定义") {
        customPathWidget.disabled = false;
        customPathWidget.color = "";
    } else {
        customPathWidget.disabled = true;
        customPathWidget.color = "#888888";
    }
    
    node.setSize?.(node.computeSize());
    setNodeWidth(node, 320);
    if (app.canvas) app.canvas.setDirty(true);
}

app.registerExtension({
    name: "XiaoCaiTools.TextSaver",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "TextSaver") {
            return;
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        
        nodeType.prototype.onNodeCreated = function() {
            const result = onNodeCreated?.apply(this, arguments);
            
            const node = this;
            
            // 设置默认宽度
            setNodeWidth(node, 320);
            
            // 获取控件
            const rootDirWidget = node.widgets?.find(w => w.name === "根目录");
            
            // 延迟初始化，设置自定义路径可用性
            setTimeout(() => {
                if (rootDirWidget) {
                    setCustomPathEnabled(node, rootDirWidget.value);
                }
            }, 100);
            
            // 监听根目录变化
            if (rootDirWidget) {
                const originalCallback = rootDirWidget.callback;
                rootDirWidget.callback = function(value) {
                    if (originalCallback) originalCallback(value);
                    console.log(`[TextSaver] 根目录变更为: ${value}`);
                    setCustomPathEnabled(node, value);
                };
            }
            
            node.setSize?.(node.computeSize());
            setNodeWidth(node, 320);
            
            if (app.canvas) {
                app.canvas.setDirty(true);
            }
            
            return result;
        };
    }
});