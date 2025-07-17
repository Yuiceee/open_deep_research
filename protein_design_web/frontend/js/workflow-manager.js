/**
 * 工作流可视化管理器
 * 使用LogicFlow实现蛋白质设计工作流的可视化
 */
class WorkflowManager {
    constructor() {
        this.lf = null;
        this.nodes = new Map();
        this.edges = new Map();
        this.currentStep = null;
        this.init();
    }

    init() {
        // 初始化LogicFlow
        this.lf = new LogicFlow({
            container: document.getElementById('workflow-container'),
            width: 800,
            height: 500,
            grid: {
                size: 20,
                type: 'dot',
                config: {
                    color: '#f0f0f0',
                    thickness: 1
                }
            },
            keyboard: {
                enabled: true
            },
            style: {
                rect: {
                    fill: '#f8f9fa',
                    stroke: '#d9d9d9',
                    strokeWidth: 2
                },
                text: {
                    fontSize: 12,
                    fill: '#333'
                }
            }
        });

        // 自定义节点样式
        this.lf.setTheme({
            rect: {
                fill: '#f8f9fa',
                stroke: '#d9d9d9',
                strokeWidth: 2,
                radius: 8
            },
            circle: {
                fill: '#f8f9fa',
                stroke: '#d9d9d9',
                strokeWidth: 2
            },
            diamond: {
                fill: '#f8f9fa',
                stroke: '#d9d9d9',
                strokeWidth: 2
            },
            text: {
                fontSize: 12,
                fill: '#333'
            },
            edge: {
                stroke: '#d9d9d9',
                strokeWidth: 1
            },
            edgeText: {
                fontSize: 10,
                fill: '#666'
            }
        });

        this.createWorkflowNodes();
        this.lf.render();
    }

    createWorkflowNodes() {
        // 定义工作流节点
        const nodes = [
            {
                id: 'input_analysis',
                type: 'rect',
                x: 150,
                y: 100,
                text: '输入分析',
                description: '分析输入序列和参数'
            },
            {
                id: 'iteration_control',
                type: 'diamond',
                x: 350,
                y: 100,
                text: '迭代控制',
                description: '控制迭代流程'
            },
            {
                id: 'prediction',
                type: 'rect',
                x: 550,
                y: 100,
                text: '结构预测',
                description: '使用ChAI-fold预测结构'
            },
            {
                id: 'scoring',
                type: 'rect',
                x: 750,
                y: 100,
                text: '质量评分',
                description: '评估预测质量'
            },
            {
                id: 'optimization',
                type: 'rect',
                x: 550,
                y: 250,
                text: '序列优化',
                description: '使用LigandMPNN优化'
            },
            {
                id: 'reporting',
                type: 'circle',
                x: 350,
                y: 250,
                text: '生成报告',
                description: '生成最终报告'
            }
        ];

        // 添加节点
        nodes.forEach(node => {
            this.lf.addNode({
                id: node.id,
                type: node.type,
                x: node.x,
                y: node.y,
                text: node.text,
                properties: {
                    status: 'pending',
                    description: node.description
                }
            });
            this.nodes.set(node.id, node);
        });

        // 定义连接关系
        const edges = [
            {
                id: 'e1',
                sourceNodeId: 'input_analysis',
                targetNodeId: 'iteration_control',
                text: '开始'
            },
            {
                id: 'e2',
                sourceNodeId: 'iteration_control',
                targetNodeId: 'prediction',
                text: '继续迭代'
            },
            {
                id: 'e3',
                sourceNodeId: 'prediction',
                targetNodeId: 'scoring',
                text: '预测完成'
            },
            {
                id: 'e4',
                sourceNodeId: 'scoring',
                targetNodeId: 'optimization',
                text: '需要优化'
            },
            {
                id: 'e5',
                sourceNodeId: 'optimization',
                targetNodeId: 'iteration_control',
                text: '返回控制'
            },
            {
                id: 'e6',
                sourceNodeId: 'iteration_control',
                targetNodeId: 'reporting',
                text: '收敛/完成'
            }
        ];

        // 添加连接
        edges.forEach(edge => {
            this.lf.addEdge({
                id: edge.id,
                sourceNodeId: edge.sourceNodeId,
                targetNodeId: edge.targetNodeId,
                text: edge.text || ''
            });
            this.edges.set(edge.id, edge);
        });
    }

    updateNodeStatus(nodeId, status, message = '') {
        const node = this.lf.getNodeModelById(nodeId);
        if (!node) return;

        // 更新节点属性
        node.updateProperties({
            status: status,
            message: message
        });

        // 定义状态对应的颜色
        const statusColors = {
            pending: { fill: '#f8f9fa', stroke: '#d9d9d9' },
            running: { fill: '#fff7e6', stroke: '#fa8c16' },
            completed: { fill: '#f6ffed', stroke: '#52c41a' },
            error: { fill: '#fff2f0', stroke: '#ff4d4f' }
        };

        // 应用颜色
        if (statusColors[status]) {
            node.updateStyle(statusColors[status]);
        }

        // 更新当前步骤
        this.currentStep = nodeId;
    }

    highlightCurrentStep(nodeId) {
        // 重置所有节点为默认状态
        this.resetAllNodes();
        
        // 高亮当前步骤
        this.updateNodeStatus(nodeId, 'running');
    }

    completeStep(nodeId) {
        this.updateNodeStatus(nodeId, 'completed');
    }

    errorStep(nodeId, message = '') {
        this.updateNodeStatus(nodeId, 'error', message);
    }

    resetAllNodes() {
        // 重置所有节点为待处理状态
        this.nodes.forEach((nodeInfo, nodeId) => {
            this.updateNodeStatus(nodeId, 'pending');
        });
    }

    // 处理来自后端的状态更新
    handleStatusUpdate(taskStatus) {
        const { current_step, status, message, progress } = taskStatus;
        
        // 根据当前步骤名称映射到节点ID
        const stepToNodeMap = {
            '初始化': 'input_analysis',
            '初始化配置': 'input_analysis',
            '开始工作流': 'iteration_control',
            '输入分析': 'input_analysis',
            '迭代控制': 'iteration_control',
            '结构预测': 'prediction',
            '质量评分': 'scoring',
            '序列优化': 'optimization',
            '生成报告': 'reporting',
            '完成': 'reporting',
            '错误': this.currentStep || 'input_analysis'
        };

        const nodeId = stepToNodeMap[current_step];
        if (!nodeId) return;

        // 根据任务状态更新节点
        if (status === 'running') {
            this.highlightCurrentStep(nodeId);
        } else if (status === 'completed') {
            this.completeStep(nodeId);
        } else if (status === 'error') {
            this.errorStep(nodeId, message);
        }
    }

    // 获取工作流统计信息
    getWorkflowStats() {
        const stats = {
            total: this.nodes.size,
            pending: 0,
            running: 0,
            completed: 0,
            error: 0
        };

        this.nodes.forEach((nodeInfo, nodeId) => {
            const node = this.lf.getNodeModelById(nodeId);
            if (node) {
                const status = node.properties.status || 'pending';
                stats[status]++;
            }
        });

        return stats;
    }

    // 重置整个工作流
    reset() {
        this.resetAllNodes();
        this.currentStep = null;
    }

    // 销毁工作流
    destroy() {
        if (this.lf) {
            this.lf.destroy();
            this.lf = null;
        }
    }

    // 获取工作流的JSON表示
    getWorkflowData() {
        if (!this.lf) return null;
        return this.lf.getGraphData();
    }

    // 调整画布大小
    resize() {
        if (this.lf) {
            const container = document.getElementById('workflow-container');
            if (container) {
                this.lf.resize(container.offsetWidth, container.offsetHeight);
            }
        }
    }
}

// 全局工作流管理器实例
window.workflowManager = new WorkflowManager();

// 监听窗口大小变化
window.addEventListener('resize', () => {
    if (window.workflowManager) {
        window.workflowManager.resize();
    }
});