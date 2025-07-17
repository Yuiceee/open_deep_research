/**
 * API客户端 - 处理与后端的通信
 * 包括REST API调用和WebSocket连接
 */
class ApiClient {
    constructor() {
        this.baseUrl = window.location.origin;
        this.websocket = null;
        this.currentTaskId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.statusCallbacks = new Set();
        this.connectionCallbacks = new Set();
        
        this.init();
    }

    init() {
        // 检查后端连接
        this.checkConnection();
    }

    /**
     * 检查后端连接状态
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.notifyConnectionStatus(true);
                return true;
            }
        } catch (error) {
            console.error('后端连接检查失败:', error);
        }
        
        this.notifyConnectionStatus(false);
        return false;
    }

    /**
     * 获取示例序列
     */
    async getExamples() {
        try {
            const response = await fetch(`${this.baseUrl}/api/examples`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.examples;
        } catch (error) {
            console.error('获取示例序列失败:', error);
            throw error;
        }
    }

    /**
     * 启动蛋白质设计工作流
     */
    async startDesign(designRequest) {
        try {
            const response = await fetch(`${this.baseUrl}/api/design`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(designRequest)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.currentTaskId = data.task_id;
            
            // 建立WebSocket连接
            this.connectWebSocket(data.task_id);
            
            return data;
        } catch (error) {
            console.error('启动设计工作流失败:', error);
            throw error;
        }
    }

    /**
     * 获取任务状态
     */
    async getTaskStatus(taskId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/task/${taskId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('获取任务状态失败:', error);
            throw error;
        }
    }

    /**
     * 获取所有任务列表
     */
    async getAllTasks() {
        try {
            const response = await fetch(`${this.baseUrl}/api/tasks`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('获取任务列表失败:', error);
            throw error;
        }
    }

    /**
     * 建立WebSocket连接
     */
    connectWebSocket(taskId) {
        if (this.websocket) {
            this.websocket.close();
        }

        const wsUrl = `${this.baseUrl.replace('http', 'ws')}/ws/${taskId}`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('WebSocket连接已建立');
            this.reconnectAttempts = 0;
            this.notifyConnectionStatus(true);
        };

        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleStatusUpdate(data);
            } catch (error) {
                console.error('WebSocket消息解析失败:', error);
            }
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.notifyConnectionStatus(false);
        };

        this.websocket.onclose = (event) => {
            console.log('WebSocket连接已关闭', event);
            this.notifyConnectionStatus(false);
            
            // 如果不是主动关闭，尝试重连
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    console.log(`尝试重连WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    this.connectWebSocket(taskId);
                }, this.reconnectDelay * this.reconnectAttempts);
            }
        };
    }

    /**
     * 关闭WebSocket连接
     */
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    /**
     * 处理状态更新
     */
    handleStatusUpdate(data) {
        console.log('收到状态更新:', data);
        
        // 通知所有状态回调
        this.statusCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('状态回调执行失败:', error);
            }
        });
    }

    /**
     * 通知连接状态变化
     */
    notifyConnectionStatus(connected) {
        this.connectionCallbacks.forEach(callback => {
            try {
                callback(connected);
            } catch (error) {
                console.error('连接状态回调执行失败:', error);
            }
        });
    }

    /**
     * 添加状态更新回调
     */
    onStatusUpdate(callback) {
        this.statusCallbacks.add(callback);
        return () => this.statusCallbacks.delete(callback);
    }

    /**
     * 添加连接状态回调
     */
    onConnectionChange(callback) {
        this.connectionCallbacks.add(callback);
        return () => this.connectionCallbacks.delete(callback);
    }

    /**
     * 获取当前任务ID
     */
    getCurrentTaskId() {
        return this.currentTaskId;
    }

    /**
     * 设置当前任务ID
     */
    setCurrentTaskId(taskId) {
        this.currentTaskId = taskId;
    }

    /**
     * 清除当前任务
     */
    clearCurrentTask() {
        this.currentTaskId = null;
        this.disconnectWebSocket();
    }

    /**
     * 发送WebSocket消息
     */
    sendMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket未连接，无法发送消息');
        }
    }

    /**
     * 检查WebSocket连接状态
     */
    isWebSocketConnected() {
        return this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }

    /**
     * 销毁API客户端
     */
    destroy() {
        this.disconnectWebSocket();
        this.statusCallbacks.clear();
        this.connectionCallbacks.clear();
    }
}

// 创建全局API客户端实例
window.apiClient = new ApiClient();