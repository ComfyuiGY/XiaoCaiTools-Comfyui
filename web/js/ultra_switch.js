// web/js/ultra_switch.js
import { app } from "../../../scripts/app.js";

/**
 * 动态更新节点的输入接口
 * @param {object} node - ComfyUI节点对象
 * @param {number} targetCount - 目标输入数量 (1-20)
 */
function updateDynamicInputs(node, targetCount) {
    if (!node || !node.inputs) return;
    
    console.log(`[万能判断切换] 更新动态输入, 目标数量=${targetCount}`);
    
    // 保存现有连接（不包括 输入_1，因为它始终存在）
    const connections = {};
    for (const input of node.inputs) {
        if (input.link !== null && input.name && input.name.startsWith("输入_") && input.name !== "输入_1") {
            const link = node.graph.links[input.link];
            if (link) {
                connections[input.name] = {
                    link: input.link,
                    sourceId: link.source_id,
                    sourceSlot: link.source_slot,
                    targetId: link.target_id,
                    targetSlot: link.target_slot
                };
            }
        }
    }
    
    // 移除超出数量的输入（从高索引开始）
    const toRemove = [];
    for (let i = node.inputs.length - 1; i >= 0; i--) {
        const input = node.inputs[i];
        if (input.name && input.name.startsWith("输入_") && input.name !== "输入_1") {
            const idx = parseInt(input.name.split("_")[1]);
            if (idx > targetCount) {
                toRemove.push(i);
                console.log(`[万能判断切换] 移除 ${input.name}`);
            }
        }
    }
    // 从后往前移除避免索引问题
    for (const idx of toRemove.sort((a, b) => b - a)) {
        node.removeInput(idx);
    }
    
    // 添加缺失的输入（从 2 到 targetCount）
    for (let i = 2; i <= targetCount; i++) {
        const inputName = `输入_${i}`;
        const exists = node.inputs.some(inp => inp.name === inputName);
        if (!exists) {
            console.log(`[万能判断切换] 添加 ${inputName}`);
            node.addInput(inputName, "*");
            
            // 恢复之前保存的连接
            if (connections[inputName]) {
                const conn = connections[inputName];
                setTimeout(() => {
                    const targetSlot = node.inputs.findIndex(inp => inp.name === inputName);
                    if (targetSlot !== -1) {
                        // 重新建立连接
                        const linkId = conn.link;
                        node.graph.links[linkId] = {
                            link_id: linkId,
                            target_id: node.id,
                            target_slot: targetSlot,
                            source_id: conn.sourceId,
                            source_slot: conn.sourceSlot,
                            type: "*"
                        };
                        node.graph.afterChange();
                        if (app.canvas) app.canvas.setDirty(true);
                    }
                }, 50);
            }
        }
    }
    
    // 调整节点大小并刷新画布
    node.setSize?.(node.computeSize());
    if (app.canvas) app.canvas.setDirty(true);
}

app.registerExtension({
    name: "XiaoCaiTools.UltraSwitch",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 支持两种节点类型
        if (nodeData.name !== "UltraSwitch" && nodeData.name !== "UltraSwitchSelect") {
            return;
        }
        
        console.log(`[万能判断切换] 注册节点: ${nodeData.name}`);
        
        // 节点创建时的处理
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            const result = onNodeCreated?.apply(this, arguments);
            
            const self = this;
            
            // 查找接入数量控件（注意中文名称）
            const inputcountWidget = this.widgets?.find(w => w.name === "接入数量");
            if (inputcountWidget) {
                // 初始化时更新输入接口（默认2个）
                setTimeout(() => {
                    const defaultValue = parseInt(inputcountWidget.value) || 2;
                    updateDynamicInputs(self, defaultValue);
                }, 100);
                
                // 监听接入数量变化
                const originalCallback = inputcountWidget.callback;
                inputcountWidget.callback = function(value) {
                    console.log(`[万能判断切换] 接入数量变更为 ${value}`);
                    if (originalCallback) originalCallback.call(this, value);
                    updateDynamicInputs(self, parseInt(value));
                };
            } else {
                // 如果没有找到控件，默认设置为2个输入
                setTimeout(() => {
                    updateDynamicInputs(self, 2);
                }, 100);
            }
            
            return result;
        };
        
        // 节点配置加载时的处理（用于加载保存的工作流）
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function() {
            const result = onConfigure?.apply(this, arguments);
            const self = this;
            setTimeout(() => {
                const inputcountWidget = this.widgets?.find(w => w.name === "接入数量");
                if (inputcountWidget) {
                    updateDynamicInputs(self, parseInt(inputcountWidget.value));
                } else {
                    // 默认2个输入
                    updateDynamicInputs(self, 2);
                }
            }, 200);
            return result;
        };
        
        // 对于手动选择节点，还需要处理选择控件的动态范围
        if (nodeData.name === "UltraSwitchSelect") {
            const onNodeCreatedSelect = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreatedSelect?.apply(this, arguments);
                
                const self = this;
                const inputcountWidget = this.widgets?.find(w => w.name === "接入数量");
                const selectWidget = this.widgets?.find(w => w.name === "选择");
                
                if (inputcountWidget && selectWidget) {
                    // 更新选择控件的可选范围
                    const updateSelectRange = (count) => {
                        const maxVal = parseInt(count);
                        const options = [];
                        for (let i = 1; i <= maxVal; i++) {
                            options.push(`选择输入${i}`);
                        }
                        selectWidget.options.values = options;
                        // 如果当前值超出范围，重置为第一个
                        const currentMatch = selectWidget.value.match(/选择输入(\d+)/);
                        if (currentMatch) {
                            const currentIndex = parseInt(currentMatch[1]);
                            if (currentIndex > maxVal) {
                                selectWidget.value = `选择输入1`;
                            }
                        } else {
                            selectWidget.value = `选择输入1`;
                        }
                        self.setSize?.(self.computeSize());
                        if (app.canvas) app.canvas.setDirty(true);
                    };
                    
                    // 监听接入数量变化
                    const originalCallback = inputcountWidget.callback;
                    inputcountWidget.callback = function(value) {
                        if (originalCallback) originalCallback.call(this, value);
                        updateSelectRange(value);
                    };
                    
                    // 初始化范围
                    setTimeout(() => {
                        updateSelectRange(inputcountWidget.value || "2");
                    }, 100);
                }
                
                return result;
            };
        }
    }
});