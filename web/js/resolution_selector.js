import { app } from "../../../scripts/app.js";

// 等待节点注册完成
app.registerExtension({
    name: "AdvancedResolutionSelector.联动",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 支持两种节点类型
        if (nodeData.name !== "AdvancedResolutionSelector" && 
            nodeData.name !== "AdvancedResolutionSelectorLatent") {
            return;
        }
        
        // 保存原始节点创建函数
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        
        nodeType.prototype.onNodeCreated = function() {
            const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
            
            // 获取三个分辨率widget
            let 横屏Widget = this.widgets?.find(w => w.name === "横屏");
            let 竖屏Widget = this.widgets?.find(w => w.name === "竖屏");
            let 方形Widget = this.widgets?.find(w => w.name === "方形");
            
            if (!横屏Widget || !竖屏Widget || !方形Widget) {
                return result;
            }
            
            // 创建联动函数
            const resetOthers = (changedWidget, changedValue) => {
                // 如果当前选择的不是"不启用"
                if (changedValue !== "不启用") {
                    // 重置其他两个widget为"不启用"
                    if (changedWidget !== 横屏Widget && 横屏Widget.value !== "不启用") {
                        横屏Widget.value = "不启用";
                        横屏Widget.callback?.(横屏Widget.value);
                    }
                    if (changedWidget !== 竖屏Widget && 竖屏Widget.value !== "不启用") {
                        竖屏Widget.value = "不启用";
                        竖屏Widget.callback?.(竖屏Widget.value);
                    }
                    if (changedWidget !== 方形Widget && 方形Widget.value !== "不启用") {
                        方形Widget.value = "不启用";
                        方形Widget.callback?.(方形Widget.value);
                    }
                }
            };
            
            // 保存原始回调
            const originalHorizontalCallback = 横屏Widget.callback;
            const originalVerticalCallback = 竖屏Widget.callback;
            const originalSquareCallback = 方形Widget.callback;
            
            // 为横屏添加联动
            横屏Widget.callback = (value) => {
                resetOthers(横屏Widget, value);
                if (originalHorizontalCallback) originalHorizontalCallback(value);
            };
            
            // 为竖屏添加联动
            竖屏Widget.callback = (value) => {
                resetOthers(竖屏Widget, value);
                if (originalVerticalCallback) originalVerticalCallback(value);
            };
            
            // 为方形添加联动
            方形Widget.callback = (value) => {
                resetOthers(方形Widget, value);
                if (originalSquareCallback) originalSquareCallback(value);
            };
            
            return result;
        };
    }
});