"""
蛋白质设计工作流 FastAPI 后端服务器
与 src/protein_design 模块完全集成
"""
import os
import sys
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

import uvicorn
import json
import traceback

# 定义前端目录
frontend_dir = Path(__file__).parent.parent / "frontend"

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入蛋白质设计模块
from src.protein_design.utils import create_single_sequence_input, get_example_sequences
from src.protein_design.graph import create_protein_design_graph
from src.protein_design.configuration import ProteinDesignConfiguration

# 创建FastAPI应用
app = FastAPI(
    title="蛋白质设计工作流API",
    description="基于LangGraph的蛋白质设计迭代优化工作流",
    version="1.0.0"
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# 数据模型
class ProteinDesignRequest(BaseModel):
    """蛋白质设计请求模型"""
    sequence: str = Field(..., description="蛋白质序列")
    design_type: str = Field(default="single", description="设计类型: single 或 ligand")
    max_iterations: int = Field(default=3, ge=1, le=10, description="最大迭代次数")
    convergence_threshold: float = Field(default=0.01, ge=0.001, le=0.1, description="收敛阈值")
    
class ProteinDesignResponse(BaseModel):
    """蛋白质设计响应模型"""
    task_id: str
    status: str
    message: str
    
class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, running, completed, error
    progress: float
    current_step: str
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 全局状态管理
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
    async def create_task(self, task_id: str, request: ProteinDesignRequest) -> TaskStatus:
        """创建新任务"""
        task_status = TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0.0,
            current_step="初始化",
            message="任务已创建，等待执行"
        )
        self.tasks[task_id] = task_status
        return task_status
    
    async def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # 通知WebSocket客户端
            if task_id in self.websocket_connections:
                try:
                    await self.websocket_connections[task_id].send_json(task.dict())
                except:
                    # 连接已断开，清理
                    del self.websocket_connections[task_id]
    
    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    async def register_websocket(self, task_id: str, websocket: WebSocket):
        """注册WebSocket连接"""
        self.websocket_connections[task_id] = websocket
        
    async def unregister_websocket(self, task_id: str):
        """注销WebSocket连接"""
        if task_id in self.websocket_connections:
            del self.websocket_connections[task_id]

# 全局任务管理器
task_manager = TaskManager()

# 工作流执行器
class WorkflowExecutor:
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
    
    async def execute_workflow(self, task_id: str, request: ProteinDesignRequest):
        """执行蛋白质设计工作流"""
        try:
            # 更新任务状态
            await self.task_manager.update_task(
                task_id,
                status="running",
                progress=10.0,
                current_step="初始化配置",
                message="正在初始化蛋白质设计配置..."
            )
            
            # 创建输入数据
            examples = get_example_sequences()
            if request.sequence:
                input_sequence = request.sequence
            else:
                input_sequence = examples["short_enzyme"]
            
            input_data = create_single_sequence_input(
                sequence=input_sequence,
                max_iterations=request.max_iterations,
                convergence_threshold=request.convergence_threshold
            )
            
            # 创建配置
            config = ProteinDesignConfiguration()
            runnable_config = {"configurable": {"configuration": config}}
            
            # 创建工作流图
            graph = create_protein_design_graph()
            
            await self.task_manager.update_task(
                task_id,
                progress=20.0,
                current_step="开始工作流",
                message="工作流图创建完成，开始执行..."
            )
            
            # 执行工作流并收集结果
            final_result = {}
            step_progress = 20.0
            progress_increment = 60.0 / request.max_iterations  # 60%的进度用于迭代
            
            async for chunk in graph.astream(input_data, config=runnable_config):
                if chunk:
                    # 解析节点输出
                    node_name = list(chunk.keys())[0]
                    node_output = chunk[node_name]
                    
                    # 更新进度
                    step_progress += progress_increment / 5  # 每个节点平均分配进度
                    
                    # 根据节点类型更新状态
                    if node_name == "input_analysis":
                        await self.task_manager.update_task(
                            task_id,
                            progress=step_progress,
                            current_step="输入分析",
                            message="正在分析输入序列..."
                        )
                    elif node_name == "iteration_control":
                        await self.task_manager.update_task(
                            task_id,
                            progress=step_progress,
                            current_step="迭代控制",
                            message="正在控制迭代流程..."
                        )
                    elif node_name == "prediction":
                        await self.task_manager.update_task(
                            task_id,
                            progress=step_progress,
                            current_step="结构预测",
                            message="正在进行蛋白质结构预测..."
                        )
                    elif node_name == "scoring":
                        await self.task_manager.update_task(
                            task_id,
                            progress=step_progress,
                            current_step="质量评分",
                            message="正在评估预测质量..."
                        )
                    elif node_name == "optimization":
                        await self.task_manager.update_task(
                            task_id,
                            progress=step_progress,
                            current_step="序列优化",
                            message="正在优化序列..."
                        )
                    elif node_name == "reporting":
                        await self.task_manager.update_task(
                            task_id,
                            progress=90.0,
                            current_step="生成报告",
                            message="正在生成最终报告..."
                        )
                    
                    # 保存最终结果
                    final_result = chunk
            
            # 任务完成
            await self.task_manager.update_task(
                task_id,
                status="completed",
                progress=100.0,
                current_step="完成",
                message="蛋白质设计工作流执行完成！",
                result=final_result
            )
            
        except Exception as e:
            # 错误处理
            error_msg = f"工作流执行出错: {str(e)}"
            await self.task_manager.update_task(
                task_id,
                status="error",
                current_step="错误",
                message=error_msg,
                error=traceback.format_exc()
            )

# 工作流执行器实例
workflow_executor = WorkflowExecutor(task_manager)

# API端点
@app.get("/")
async def root():
    """根路径，返回前端页面"""
    return FileResponse(frontend_dir / "index.html")

@app.get("/api/examples")
async def get_examples():
    """获取示例序列"""
    try:
        examples = get_example_sequences()
        return {
            "success": True,
            "examples": examples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/design", response_model=ProteinDesignResponse)
async def start_design(request: ProteinDesignRequest):
    """启动蛋白质设计工作流"""
    try:
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务
        await task_manager.create_task(task_id, request)
        
        # 异步执行工作流
        asyncio.create_task(workflow_executor.execute_workflow(task_id, request))
        
        return ProteinDesignResponse(
            task_id=task_id,
            status="pending",
            message="蛋白质设计任务已创建，正在执行..."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task

@app.get("/api/tasks")
async def list_tasks():
    """获取所有任务列表"""
    return {
        "tasks": list(task_manager.tasks.values())
    }

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket端点，用于实时状态更新"""
    await websocket.accept()
    await task_manager.register_websocket(task_id, websocket)
    
    try:
        # 发送当前任务状态
        task = task_manager.get_task(task_id)
        if task:
            await websocket.send_json(task.dict())
        
        # 保持连接
        while True:
            try:
                # 等待客户端消息或保持连接
                message = await websocket.receive_text()
                # 这里可以处理客户端发送的消息
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await task_manager.unregister_websocket(task_id)

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# 启动服务器
if __name__ == "__main__":
    print("🧬 启动蛋白质设计工作流后端服务器...")
    print("🌐 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )