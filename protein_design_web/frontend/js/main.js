/**
 * 主应用逻辑
 * 协调前端各个组件的交互
 */
class ProteinDesignApp {
    constructor() {
        this.currentTaskId = null;
        this.currentTaskStatus = null;
        this.isRunning = false;
        this.examples = {};
        
        this.init();
    }

    async init() {
        // 绑定事件监听器
        this.bindEventListeners();
        
        // 加载示例序列
        await this.loadExamples();
        
        // 设置API客户端回调
        this.setupApiCallbacks();
        
        // 初始化UI状态
        this.initializeUI();
        
        console.log('蛋白质设计应用初始化完成');
    }

    bindEventListeners() {
        // 窗口大小变化
        window.addEventListener('resize', () => {
            if (window.workflowManager) {
                window.workflowManager.resize();
            }
        });

        // 防止页面刷新时丢失任务
        window.addEventListener('beforeunload', (event) => {
            if (this.isRunning) {
                event.preventDefault();
                event.returnValue = '工作流正在运行，确定要离开吗？';
            }
        });
    }

    async loadExamples() {
        try {
            this.examples = await window.apiClient.getExamples();
            console.log('示例序列加载成功:', this.examples);
        } catch (error) {
            console.error('加载示例序列失败:', error);
            this.showMessage('加载示例序列失败', 'error');
        }
    }

    setupApiCallbacks() {
        // 状态更新回调
        window.apiClient.onStatusUpdate((taskStatus) => {
            this.handleTaskStatusUpdate(taskStatus);
        });

        // 连接状态回调
        window.apiClient.onConnectionChange((connected) => {
            this.handleConnectionStatusChange(connected);
        });
    }

    initializeUI() {
        // 设置默认值
        this.updateConnectionStatus(false);
        this.updateProgress(0, '等待开始');
        
        // 初始化按钮状态
        const startBtn = document.getElementById('start-workflow');
        const stopBtn = document.getElementById('stop-workflow');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }

    handleTaskStatusUpdate(taskStatus) {
        this.currentTaskStatus = taskStatus;
        
        // 更新任务信息
        this.updateTaskInfo(taskStatus);
        
        // 更新进度条
        this.updateProgress(taskStatus.progress, taskStatus.message);
        
        // 更新工作流可视化
        if (window.workflowManager) {
            window.workflowManager.handleStatusUpdate(taskStatus);
        }
        
        // 添加状态消息
        this.addStatusMessage(taskStatus.message, this.getStatusType(taskStatus.status));
        
        // 处理任务完成
        if (taskStatus.status === 'completed') {
            this.handleTaskCompleted(taskStatus);
        } else if (taskStatus.status === 'error') {
            this.handleTaskError(taskStatus);
        }
    }

    handleConnectionStatusChange(connected) {
        this.updateConnectionStatus(connected);
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.className = 'connection-status connected';
            statusElement.innerHTML = '✓ 已连接到后端';
        } else {
            statusElement.className = 'connection-status disconnected';
            statusElement.innerHTML = '✗ 后端连接断开';
        }
    }

    updateTaskInfo(taskStatus) {
        const taskInfo = document.getElementById('task-info');
        const taskIdDisplay = document.getElementById('task-id-display');
        const taskStatusDisplay = document.getElementById('task-status-display');
        
        if (taskStatus && taskStatus.task_id) {
            taskInfo.style.display = 'block';
            taskIdDisplay.textContent = `任务ID: ${taskStatus.task_id.substring(0, 8)}...`;
            taskStatusDisplay.textContent = `状态: ${taskStatus.status} - ${taskStatus.current_step}`;
        } else {
            taskInfo.style.display = 'none';
        }
    }

    updateProgress(progress, message) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}% - ${message}`;
    }

    addStatusMessage(message, type = 'info') {
        const messagesContainer = document.getElementById('status-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `status-item ${type}`;
        
        // 添加时间戳
        const timestamp = new Date().toLocaleTimeString();
        messageElement.innerHTML = `
            <span>[${timestamp}]</span>
            <span>${message}</span>
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // 限制消息数量
        while (messagesContainer.children.length > 20) {
            messagesContainer.removeChild(messagesContainer.firstChild);
        }
    }

    getStatusType(status) {
        const statusMap = {
            'pending': 'info',
            'running': 'running',
            'completed': 'success',
            'error': 'error'
        };
        return statusMap[status] || 'info';
    }

    handleTaskCompleted(taskStatus) {
        this.isRunning = false;
        this.updateButtonStates();
        
        // 显示结果
        if (taskStatus.result) {
            this.displayResults(taskStatus.result);
        }
        
        this.showMessage('工作流执行完成！', 'success');
    }

    handleTaskError(taskStatus) {
        this.isRunning = false;
        this.updateButtonStates();
        
        const errorMsg = taskStatus.error || taskStatus.message;
        this.showMessage(`工作流执行出错: ${errorMsg}`, 'error');
        
        // 在工作流中标记错误
        if (window.workflowManager) {
            window.workflowManager.errorStep(
                window.workflowManager.currentStep || 'input_analysis',
                errorMsg
            );
        }
    }

    displayResults(result) {
        const resultsContent = document.getElementById('results-content');
        resultsContent.innerHTML = '';
        
        if (result.reporting && result.reporting.final_report) {
            // 显示最终报告
            const reportDiv = document.createElement('div');
            reportDiv.className = 'markdown-content';
            reportDiv.innerHTML = this.markdownToHtml(result.reporting.final_report);
            resultsContent.appendChild(reportDiv);
            
            // 自动切换到结果标签
            this.switchTab('results');
        } else {
            // 显示原始结果
            const rawResultDiv = document.createElement('div');
            rawResultDiv.className = 'result-item';
            rawResultDiv.innerHTML = `
                <h4>执行结果</h4>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            `;
            resultsContent.appendChild(rawResultDiv);
        }
    }

    markdownToHtml(markdown) {
        // 简单的Markdown到HTML转换
        return markdown
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^\* (.*$)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.*)$/gm, '<p>$1</p>')
            .replace(/<p><h/g, '<h')
            .replace(/<\/h([1-6])><\/p>/g, '</h$1>')
            .replace(/<p><ul>/g, '<ul>')
            .replace(/<\/ul><\/p>/g, '</ul>')
            .replace(/<p><\/p>/g, '');
    }

    updateButtonStates() {
        const startBtn = document.getElementById('start-workflow');
        const stopBtn = document.getElementById('stop-workflow');
        
        if (this.isRunning) {
            startBtn.disabled = true;
            startBtn.textContent = '运行中...';
            stopBtn.disabled = false;
        } else {
            startBtn.disabled = false;
            startBtn.textContent = '开始工作流';
            stopBtn.disabled = true;
        }
    }

    showMessage(message, type = 'info') {
        // 可以在这里添加toast通知或其他UI反馈
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    // 切换标签页
    switchTab(tabName) {
        // 移除所有active类
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // 添加active类到当前标签
        document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // 如果切换到工作流标签，调整画布大小
        if (tabName === 'workflow' && window.workflowManager) {
            setTimeout(() => {
                window.workflowManager.resize();
            }, 100);
        }
    }
}

// 全局函数，供HTML调用
window.startWorkflow = async function() {
    if (window.app.isRunning) return;
    
    // 获取输入参数
    const sequence = document.getElementById('sequence').value.trim();
    const designType = document.getElementById('design-type').value;
    const maxIterations = parseInt(document.getElementById('max-iterations').value);
    const threshold = parseFloat(document.getElementById('threshold').value);
    
    // 验证输入
    if (!sequence) {
        window.app.showMessage('请输入蛋白质序列', 'error');
        return;
    }
    
    // 创建请求
    const request = {
        sequence: sequence,
        design_type: designType,
        max_iterations: maxIterations,
        convergence_threshold: threshold
    };
    
    try {
        window.app.isRunning = true;
        window.app.updateButtonStates();
        
        // 重置工作流可视化
        if (window.workflowManager) {
            window.workflowManager.reset();
        }
        
        // 清空之前的结果
        document.getElementById('results-content').innerHTML = '<p style="color: #666; text-align: center; margin-top: 50px;">工作流执行中...</p>';
        
        // 启动工作流
        const response = await window.apiClient.startDesign(request);
        window.app.currentTaskId = response.task_id;
        
        window.app.showMessage('工作流已启动，正在执行...', 'info');
        
    } catch (error) {
        window.app.isRunning = false;
        window.app.updateButtonStates();
        window.app.showMessage(`启动工作流失败: ${error.message}`, 'error');
    }
};

window.stopWorkflow = function() {
    if (!window.app.isRunning) return;
    
    // 断开WebSocket连接
    window.apiClient.disconnectWebSocket();
    
    // 重置状态
    window.app.isRunning = false;
    window.app.updateButtonStates();
    window.app.currentTaskId = null;
    
    // 重置工作流可视化
    if (window.workflowManager) {
        window.workflowManager.reset();
    }
    
    window.app.showMessage('工作流已停止', 'info');
};

window.loadExample = function(exampleName) {
    if (window.app.examples && window.app.examples[exampleName]) {
        document.getElementById('sequence').value = window.app.examples[exampleName];
        window.app.showMessage(`已加载示例序列: ${exampleName}`, 'info');
    } else {
        window.app.showMessage(`示例序列 ${exampleName} 未找到`, 'error');
    }
};

window.switchTab = function(tabName) {
    if (window.app) {
        window.app.switchTab(tabName);
    }
};

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProteinDesignApp();
});