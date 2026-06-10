// web/js/text_file_reader.js
import { app } from "../../../scripts/app.js";

// 设置节点宽度
function setNodeWidth(node, width) {
    if (node.size) {
        node.size[0] = width;
        node.setSize?.(node.size);
    }
}

// 根据读取模式设置控件的可用性
function setWidgetsEnabled(node, mode) {
    const fixedFileWidget = node.widgets?.find(w => w.name === "固定文件名");
    const indexWidget = node.widgets?.find(w => w.name === "索引");
    
    if (!fixedFileWidget) return;
    
    if (mode === "固定读取") {
        fixedFileWidget.disabled = false;
        fixedFileWidget.color = "";
        if (indexWidget) indexWidget.disabled = true;
    } else if (mode === "索引读取") {
        fixedFileWidget.disabled = true;
        fixedFileWidget.color = "#888888";
        if (indexWidget) indexWidget.disabled = false;
    } else {
        fixedFileWidget.disabled = true;
        fixedFileWidget.color = "#888888";
        if (indexWidget) indexWidget.disabled = true;
    }
    
    node.setSize?.(node.computeSize());
    setNodeWidth(node, 270);
    if (app.canvas) app.canvas.setDirty(true);
}

app.registerExtension({
    name: "XiaoCaiTools.TextFileReader",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 检查节点名称（支持新旧两种名称）
        if (nodeData.name !== "XiaoCaiTextFileReader" && nodeData.name !== "TextFileReader") {
            return;
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        
        nodeType.prototype.onNodeCreated = function() {
            const result = onNodeCreated?.apply(this, arguments);
            
            const node = this;
            
            // 设置默认宽度为 270
            setNodeWidth(node, 270);
            
            // 获取控件
            const modeWidget = node.widgets?.find(w => w.name === "读取模式");
            
            // 延迟初始化，设置控件可用性
            setTimeout(() => {
                if (modeWidget) {
                    setWidgetsEnabled(node, modeWidget.value);
                }
            }, 100);
            
            // 监听读取模式变化
            if (modeWidget) {
                const originalModeCallback = modeWidget.callback;
                modeWidget.callback = function(value) {
                    if (originalModeCallback) originalModeCallback(value);
                    console.log(`[TextFileReader] 读取模式变更为: ${value}`);
                    setWidgetsEnabled(node, value);
                };
            }
            
            node.setSize?.(node.computeSize());
            setNodeWidth(node, 270);
            
            if (app.canvas) {
                app.canvas.setDirty(true);
            }
            
            return result;
        };
    }
});