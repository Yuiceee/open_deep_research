i# 蛋白质设计工作流 Web 应用

这是一个**完整的前后端集成项目**，将 `src/protein_design` 模块包装为 Web 应用，提供直观的用户界面和实时的工作流可视化。

## 🎯 项目概述

### 核心特性

- ✅ **完整集成** - 与 `src/protein_design` 模块完美集成
- ✅ **实时可视化** - LogicFlow 动态工作流图
- ✅ **WebSocket通信** - 实时状态更新和进度跟踪
- ✅ **RESTful API** - 标准的API接口
- ✅ **错误处理** - 完整的错误处理和恢复机制
- ✅ **响应式设计** - 现代化的用户界面

### 技术栈

**后端 (FastAPI)**
- FastAPI - 现代化的Web框架
- WebSocket - 实时通信
- Pydantic - 数据验证
- Uvicorn - ASGI服务器

**前端 (原生JavaScript)**
- LogicFlow - 工作流可视化
- WebSocket - 实时通信
- 现代HTML5/CSS3/ES6+

**集成**
- LangGraph - 工作流引擎
- MCP - 模型上下文协议
- ChAI-fold、LigandMPNN - 蛋白质设计工具

## 📁 项目结构

```
protein_design_web/
├── backend/
│   └── main.py                 # FastAPI后端服务器
├── frontend/
│   ├── index.html              # 主页面
│   └── js/
│       ├── main.js             # 主应用逻辑
│       ├── api-client.js       # API客户端
│       └── workflow-manager.js # 工作流可视化
├── requirements.txt            # Python依赖
├── start.sh                   # 启动脚本
└── README.md                  # 项目说明
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- 已配置的 `src/protein_design` 模块
- OpenAI API Key (可选)

### 2. 安装启动

```bash
# 进入项目目录
cd protein_design_web

# 给启动脚本添加执行权限
chmod +x start.sh

# 启动开发服务器
./start.sh dev
```

### 3. 访问应用

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📖 详细使用说明

### 用户界面功能

#### 1. 输入配置
- **蛋白质序列**: 手动输入或选择示例序列
- **设计类型**: 单序列优化或配体优化
- **迭代参数**: 最大迭代次数和收敛阈值

#### 2. 实时监控
- **连接状态**: 显示后端连接状态
- **任务信息**: 当前任务ID和状态
- **进度条**: 实时进度显示
- **状态消息**: 详细的执行日志

#### 3. 工作流可视化
- **动态流程图**: 基于LogicFlow的实时工作流图
- **节点状态**: 不同颜色表示节点状态
- **执行路径**: 清晰的执行路径显示

#### 4. 结果展示
- **Markdown报告**: 格式化的分析报告
- **原始数据**: 完整的执行结果
- **可视化图表**: 结果数据的图表展示

### API接口

#### 核心端点

```python
# 启动设计工作流
POST /api/design
{
    "sequence": "MTMDKSELVQ...",
    "design_type": "single",
    "max_iterations": 3,
    "convergence_threshold": 0.01
}

# 获取任务状态
GET /api/task/{task_id}

# 获取示例序列
GET /api/examples

# WebSocket连接
WS /ws/{task_id}
```

#### 数据模型

```python
class ProteinDesignRequest(BaseModel):
    sequence: str
    design_type: str = "single"
    max_iterations: int = 3
    convergence_threshold: float = 0.01

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, error
    progress: float
    current_step: str
    message: str
    result: Optional[Dict[str, Any]] = None
```

### 工作流执行过程

1. **输入分析** - 验证和解析输入序列
2. **迭代控制** - 管理优化迭代循环
3. **结构预测** - 使用ChAI-fold预测蛋白质结构
4. **质量评分** - 评估预测质量和结合亲和力
5. **序列优化** - 使用LigandMPNN优化序列
6. **收敛检测** - 检查是否满足收敛条件
7. **报告生成** - 生成最终分析报告

## 🛠️ 开发指南

### 启动选项

```bash
# 开发模式 (热重载)
./start.sh dev

# 生产模式 (多进程)
./start.sh prod

# 运行测试
./start.sh test

# 安装依赖
./start.sh install

# 检查环境
./start.sh check
```

### 环境变量

```bash
# 必需的环境变量
export OPENAI_API_KEY="your-api-key"

# 可选的环境变量
export PORT=8000                    # 服务器端口
export HOST="0.0.0.0"              # 服务器主机
export LOG_LEVEL="info"            # 日志级别
```

### 自定义配置

#### 后端配置

```python
# backend/main.py 中的配置
app = FastAPI(
    title="蛋白质设计工作流API",
    description="基于LangGraph的蛋白质设计迭代优化工作流",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 前端配置

```javascript
// frontend/js/api-client.js 中的配置
class ApiClient {
    constructor() {
        this.baseUrl = window.location.origin;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }
}
```

### 扩展功能

#### 1. 添加新的工作流节点

```python
# backend/main.py 中添加新的状态映射
step_to_node_map = {
    '新节点名称': 'new_node_id',
    # ... 其他节点
}
```

```javascript
// frontend/js/workflow-manager.js 中添加新节点
const nodes = [
    {
        id: 'new_node_id',
        type: 'rect',
        x: 150,
        y: 300,
        text: '新节点',
        description: '新节点描述'
    },
    // ... 其他节点
];
```

#### 2. 添加新的API端点

```python
@app.post("/api/custom-endpoint")
async def custom_endpoint(request: CustomRequest):
    # 自定义逻辑
    return {"message": "成功"}
```

#### 3. 自定义前端组件

```javascript
class CustomComponent {
    constructor() {
        this.init();
    }
    
    init() {
        // 初始化逻辑
    }
}
```

## 🐛 故障排除

### 常见问题

#### 1. 导入错误

```bash
# 错误: ImportError: No module named 'src.protein_design'
# 解决: 确保在正确的项目根目录中运行
export PYTHONPATH="/path/to/project/root:$PYTHONPATH"
```

#### 2. WebSocket连接失败

```bash
# 错误: WebSocket connection failed
# 解决: 检查防火墙设置，确保端口8000开放
sudo ufw allow 8000
```

#### 3. 内存不足

```bash
# 错误: Out of memory
# 解决: 增加系统内存或减少max_iterations
```

### 日志查看

```bash
# 查看应用日志
tail -f backend/app.log

# 查看系统日志
journalctl -u protein-design-web

# 查看错误日志
tail -f backend/error.log
```

### 性能优化

#### 1. 后端优化

```python
# 使用异步处理
@app.post("/api/design")
async def start_design(request: ProteinDesignRequest):
    # 异步执行工作流
    asyncio.create_task(workflow_executor.execute_workflow(task_id, request))
```

#### 2. 前端优化

```javascript
// 使用防抖处理频繁更新
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

## 🔧 维护指南

### 定期任务

1. **清理临时文件**
   ```bash
   # 清理工作区文件
   find workspace/ -name "*.tmp" -delete
   ```

2. **更新依赖**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **备份数据**
   ```bash
   tar -czf backup_$(date +%Y%m%d).tar.gz workspace/
   ```

### 监控指标

- **响应时间**: 平均API响应时间
- **错误率**: 工作流失败率
- **资源使用**: CPU和内存使用情况
- **连接数**: WebSocket连接数量

## 🤝 贡献指南

### 开发流程

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 代码规范

- Python: 遵循PEP 8规范
- JavaScript: 使用ES6+语法
- 注释: 详细的功能说明
- 测试: 完整的单元测试

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📞 支持

如果遇到问题或需要帮助，请：

1. 查看本文档的故障排除部分
2. 检查 [GitHub Issues](https://github.com/your-repo/issues)
3. 创建新的Issue描述问题

## 🎉 总结

这个Web应用提供了一个完整的蛋白质设计工作流解决方案，具有：

- **直观的用户界面** - 无需编程知识即可使用
- **实时的执行监控** - 清晰的进度跟踪和状态显示
- **强大的可视化** - LogicFlow工作流图和结果展示
- **完整的API接口** - 支持程序化调用
- **生产级别的稳定性** - 完整的错误处理和恢复机制

立即启动应用，开始您的蛋白质设计工作流之旅！

```bash
./start.sh dev
```

访问 http://localhost:8000 开始使用！