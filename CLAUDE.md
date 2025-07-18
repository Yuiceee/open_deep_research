# CLAUDE.md

这个文件为Claude Code (claude.ai/code) 在该仓库中工作时提供指导。

请时刻注意用中文回复用户
# Open Deep Research

## 关于 Open Deep Research

Open Deep Research 是一个实验性的、完全开源的研究助手，可以自动化深度研究并生成任何主题的综合报告。它旨在帮助研究人员、分析师和好奇的个人生成详细、有据可查的报告，无需手动研究开销。

### 主要特性
- **自动化研究**：搜索多个来源（网络、学术论文、专业数据库）
- **综合报告**：生成带有适当引用的结构化markdown报告
- **多种搜索API**：支持Tavily、Perplexity、Exa、ArXiv、PubMed、DuckDuckGo等
- **灵活的模型**：与任何支持`init_chat_model()`API的LLM兼容
- **质量评估**：内置评估系统来评估报告质量
- **MCP集成**：支持模型上下文协议进行工具集成

## 仓库结构

仓库分为两个主要模块：

### 1. Open Deep Research (`src/open_deep_research/`)
核心研究自动化，包含两种不同的实现：

- **图形化工作流** (`graph.py`)：具有人在循环中的结构化计划-执行工作流
- **多智能体实现** (`multi_agent.py`)：具有并行处理的监督者-研究者架构
- **配置管理** (`configuration.py`)：两种实现的集中化配置管理
- **状态管理** (`state.py`)：用于LangGraph状态管理的Pydantic模型
- **工具库** (`utils.py`)：搜索API集成和核心工具
- **提示词** (`prompts.py`)：AI智能体指令模板

### 2. 蛋白质设计 (`src/protein_design/`)
使用MCP工具的专业蛋白质设计工作流，支持迭代优化：

- **蛋白质设计图** (`graph.py`)：迭代式工作流，支持单序列和配体优化
- **配置管理** (`configuration.py`)：蛋白质设计专用配置，支持中文
- **状态管理** (`state.py`)：完整的状态追踪和迭代管理
- **提示词** (`prompts.py`)：中文蛋白质设计指令模板
- **工具函数** (`utils.py`)：输入验证和结果格式化
- **MCP工具集成**：`/tool/chai_fold/`、`/tool/ligandmpnn/`、`/tool/score/`

## 常用开发命令

### 环境设置
```bash
# 使用pixi安装依赖
pixi install

# 或者使用pip
pip install -e .
```

### 测试
```bash
# 运行所有测试，带有丰富输出
python tests/run_test.py --all

# 测试特定的智能体实现
python tests/run_test.py --agent multi_agent
python tests/run_test.py --agent graph

# 使用自定义模型运行测试
python tests/run_test.py --agent multi_agent --supervisor-model "anthropic:claude-3-5-sonnet-latest"

# 直接运行pytest
python -m pytest tests/test_report_quality.py -v

# 蛋白质设计模块测试
cd src/protein_design/
python test_basic.py          # 基础组件测试
python test_workflow.py       # 工作流逻辑测试
python test_integration.py    # 集成测试
python test_summary.py        # 完整性检查
python test_complete_workflow.py  # 完整工作流测试（推荐）
python visualize_graph.py     # 图结构可视化
```

### 代码质量
```bash
# 运行代码检查（ruff在pyproject.toml中配置）
ruff check src/
ruff format src/

# 类型检查（mypy作为开发依赖可用）
mypy src/
```

### LangGraph开发
```bash
# 启动LangGraph应用服务
langgraph serve

# 部署到LangGraph Cloud
langgraph deploy
```

## 架构概述

### 两种研究实现

代码库提供两种不同的自动化研究方法：

#### 1. 图形化工作流 (`src/open_deep_research/graph.py`)
- **规划器 → 查询编写器 → 搜索 → 章节编写器 → 评分器** 流程
- 人在循环中进行计划批准和反馈
- 带有反思的顺序章节创建
- 可配置的搜索深度和迭代限制
- 适用于：需要准确性和控制的高风险研究

#### 2. 多智能体实现 (`src/open_deep_research/multi_agent.py`)
- **监督者智能体** 管理整体流程
- **研究者智能体** 并行处理不同章节
- 由于并行处理执行更快
- 适用于：快速研究和快速报告生成

### 配置管理

两种实现都使用集中化配置：

- **WorkflowConfiguration**：用于图形化实现
- **MultiAgentConfiguration**：用于多智能体实现
- 自动配置DeepSeek模型与火山API端点
- 支持环境变量和运行时配置

### 搜索API集成

系统通过`utils.py`支持多种搜索API：

- **Tavily**：优化的网络搜索API
- **Perplexity**：AI驱动的搜索
- **Exa**：语义搜索引擎
- **ArXiv**：学术论文搜索
- **PubMed**：医学文献搜索
- **DuckDuckGo**：隐私友好的搜索
- **Google搜索**：API和爬虫模式

### 模型集成

- **DeepSeek集成**：为火山API自动配置
- **提供商支持**：OpenAI、Anthropic、Groq、DeepSeek
- **模型上下文协议**：用于工具的MCP服务器集成
- **灵活的模型选择**：不同角色使用不同模型

## 开发指南

### 测试策略
- 使用`tests/run_test.py`进行丰富输出的交互式测试
- 测试根据9个质量标准评估报告
- LangSmith集成用于实验跟踪
- 两种实现都有全面的测试覆盖

### 配置最佳实践
- 使用环境变量进行敏感配置
- 利用DeepSeek模型的自动配置
- 测试不同的搜索API找到最佳设置
- 考虑MCP工具集成用于专业工作流

### 模型选择
- **规划**：使用具有推理能力的模型（DeepSeek R1、Claude）
- **研究**：根据用例平衡速度和质量
- **评估**：使用一致的模型进行公平比较

### MCP工具开发
- 遵循蛋白质设计模块模式开发新的MCP工具
- 实现适当的错误处理和验证
- 使用FastMCP进行服务器实现
- 记录工具功能和限制

### 蛋白质设计模块开发
- **状态管理**：使用TypedDict进行强类型状态管理
- **错误处理**：统一的错误处理节点和异常管理
- **迭代控制**：支持用户自定义的收敛条件和最大迭代次数
- **工具集成**：原生MCP工具集成，支持异步调用
- **中文支持**：完整的中文提示词和用户界面

## 质量评估

系统包含全面的评估：

### 报告质量标准
1. **主题相关性**：与输入主题的整体一致性
2. **章节相关性**：每个章节与主要主题的相关性
3. **结构和流程**：逻辑进展和叙述性
4. **引言质量**：上下文和范围设定
5. **结论质量**：总结和关键发现
6. **结构元素**：表格、列表、格式的正确使用
7. **章节标题**：正确的Markdown格式
8. **引用**：适当的来源归属
9. **整体质量**：专业写作和准确性

### 评估使用
```bash
# 带有视觉反馈的快速评估
python tests/run_test.py --agent multi_agent --rich-output

# 自定义评估模型
python tests/run_test.py --eval-model "anthropic:claude-3-5-sonnet-latest"

# 特定搜索API测试
python tests/run_test.py --search-api tavily
```

## 蛋白质设计工作流

蛋白质设计模块提供专业的迭代优化工作流：

### 架构特点
- **迭代循环**：支持用户控制的多轮优化
- **双场景支持**：单序列优化和配体优化
- **收敛检测**：基于分数阈值的自动收敛
- **中文界面**：完整的中文提示词和配置
- **MCP集成**：原生支持模型上下文协议

### 工作流步骤
1. **输入分析** (`input_analysis_node`)：确定设计场景并初始化状态
2. **迭代控制** (`iteration_control_node`)：决定是否继续优化循环
3. **结构预测** (`prediction_node`)：使用ChAI-fold进行蛋白质结构预测
4. **质量评分** (`scoring_node`)：分析预测质量和相互作用
5. **序列优化** (`optimization_node`)：使用LigandMPNN优化序列
6. **报告生成** (`reporting_node`)：生成综合分析报告和建议

### 支持的设计场景
1. **单序列优化**：
   - 针对酶活性等功能的蛋白质优化
   - 适用于提高特定蛋白质性能
   
2. **配体优化**：
   - 固定受体，优化配体结合亲和力
   - 适用于药物设计和分子对接优化

### MCP工具集成
- **ChAI-fold** (`tool/chai_fold/`)：蛋白质结构预测
- **LigandMPNN** (`tool/ligandmpnn/`)：配体设计优化
- **评分工具** (`tool/score/`)：结合亲和力和质量评估

### 使用示例
```python
import asyncio
from protein_design.utils import create_single_sequence_input, get_example_sequences
from protein_design.graph import create_protein_design_graph
from protein_design.configuration import ProteinDesignConfiguration

async def run_protein_design():
    # 创建单序列优化输入
    examples = get_example_sequences()
    input_data = create_single_sequence_input(
        sequence=examples["short_enzyme"],
        max_iterations=3,
        convergence_threshold=0.01
    )
    
    # 创建配置和工作流
    config = ProteinDesignConfiguration()
    runnable_config = {"configurable": {"configuration": config}}
    graph = create_protein_design_graph()
    
    # 异步运行工作流
    result = await graph.ainvoke(input_data, config=runnable_config)
    return result

# 运行异步工作流
result = asyncio.run(run_protein_design())
```

## 重要实现说明

### 统一工作目录管理系统

项目实现了统一的工作目录管理系统，确保所有文件有序组织和易于调试。

#### 目录结构设计
```
project_root/
├── workspace/
│   ├── 2025-01-15_14-30-45_protein_design_session1/
│   │   ├── iteration_0/
│   │   │   ├── input_files/
│   │   │   │   ├── input.fasta
│   │   │   │   └── complex.fasta
│   │   │   ├── chaifold_output/
│   │   │   │   ├── pred.model_idx_0.cif
│   │   │   │   └── scores.model_idx_0.npz
│   │   │   ├── ligandmpnn_output/
│   │   │   └── scoring_results/
│   │   ├── iteration_1/
│   │   ├── final_report.md
│   │   └── session_summary.json
│   └── ...
```

#### 核心工具函数
- `get_project_root()`: 自动定位项目根目录
- `create_session_directory()`: 创建带时间戳的会话目录
- `create_iteration_directory()`: 创建迭代目录及子目录
- `create_directories_async()`: 异步目录创建
- `get_session_info()`: 会话统计信息

#### 文件命名规则
- **主会话目录**: `{YYYY-MM-DD}_{HH-MM-SS}_protein_design_{session_id}`
- **迭代目录**: `iteration_{n}`
- **工具输出目录**: `chaifold_output`, `ligandmpnn_output`, `scoring_results`

#### 自动清理机制
- `cleanup_old_sessions()`: 清理7天前的旧会话
- 目录大小统计和文件数量追踪

### DeepSeek模型配置
系统自动配置DeepSeek模型与火山API端点（`https://ark.cn-beijing.volces.com/api/v3`）。这在配置类的`__post_init__`方法中处理。

### 搜索结果处理
- **摘要**：使用LLM总结搜索结果
- **分割和重排**：用于更好相关性的高级处理
- **去重**：自动删除重复内容
- **来源归属**：适当的引用格式

### 错误处理
- **重试逻辑**：为API失败配置重试
- **优雅降级**：回退到备用搜索API
- **验证**：Pydantic模型确保数据完整性
- **日志记录**：用于调试的全面日志记录

### 性能考虑
- **异步处理**：并发搜索查询
- **缓存**：搜索结果缓存以提高效率
- **速率限制**：遵守API速率限制
- **内存管理**：大文档的高效处理

## 当前项目状态

### 已完成功能
- ✅ **Open Deep Research核心模块**：完整的研究自动化和报告生成
- ✅ **蛋白质设计模块**：完整的迭代优化工作流
- ✅ **MCP工具集成**：ChAI-fold、LigandMPNN、评分工具完整集成
- ✅ **中文本地化**：所有提示词和配置都支持中文
- ✅ **测试覆盖**：完整的单元测试和集成测试套件
- ✅ **双场景支持**：单序列优化和配体优化场景
- ✅ **迭代控制**：用户可控的收敛条件和最大迭代次数
- ✅ **统一工作目录管理**：项目根目录下的workspace结构化管理
- ✅ **完整测试套件**：包含完整工作流测试和报告生成
- ✅ **现代化前端界面**：React + TypeScript + LogicFlow 的完整前端实现
- ✅ **实时工作流可视化**：动态流程图和状态同步
- ✅ **前后端完美适配**：通过适配器实现无缝集成

### 新增前端功能
- **智能用户界面**：对话式交互、文件上传、序列输入
- **实时流程图**：LogicFlow 2.0 动态工作流可视化
- **状态同步**：WebSocket 实时通信和状态更新
- **结果展示**：Markdown 报告、统计图表、数据可视化
- **响应式设计**：适配桌面端、平板、移动设备
- **完整测试**：单元测试、集成测试、兼容性测试

### 开发重点
- **蛋白质设计**：基于MCP工具的专业生物信息学工作流
- **迭代优化**：支持多轮优化和收敛检测
- **质量保证**：全面的测试和验证系统
- **中文支持**：完整的中文界面和文档
- **工作目录管理**：统一的文件组织和清理机制
- **前端体验**：现代化的用户界面和交互体验

### 完整工作流测试

#### 推荐测试方式
```bash
cd src/protein_design/
python test_complete_workflow.py
```

该测试文件提供：
- **完整工作流测试**：从输入到报告的端到端测试
- **性能监控**：执行时间和资源使用统计
- **详细状态跟踪**：每个节点的执行状态记录
- **自动报告生成**：Markdown格式的详细报告
- **工作目录分析**：文件组织和大小统计
- **错误处理验证**：异常情况的完整处理

#### 报告输出
测试完成后会生成：
- `final_report.md`: 详细的蛋白质设计分析报告
- `protein_design_report_{timestamp}.md`: 带时间戳的报告副本
- 会话目录结构分析和统计信息

### 技术栈

#### 后端技术栈
- **LangGraph**：状态图工作流框架
- **MCP**：模型上下文协议工具集成
- **FastMCP**：MCP服务器实现
- **TypedDict**：强类型状态管理
- **asyncio**：异步工具调用

#### 前端技术栈
- **React 18**：现代化前端框架
- **TypeScript**：类型安全的开发体验
- **Ant Design**：企业级UI组件库
- **LogicFlow 2.0**：动态流程图可视化引擎
- **Zustand**：轻量级状态管理
- **Socket.io**：实时双向通信
- **Vite**：现代化构建工具
- **React Router**：单页应用路由

## 前端界面详细说明

### 3. 蛋白质设计前端界面 (`frontend/`)
现代化的React前端应用，为蛋白质设计工作流提供直观的用户界面：

#### 核心组件
- **主工作流组件** (`ProteinDesignWorkflow.tsx`)：整体布局和流程控制
- **用户输入面板** (`UserInputPanel.tsx`)：支持对话交互、文件上传、序列输入
- **工作流可视化** (`WorkflowVisualization.tsx`)：基于LogicFlow的动态流程图
- **对话界面** (`ChatInterface.tsx`)：自然语言交互界面
- **序列输入器** (`SequenceInput.tsx`)：专业的序列编辑组件
- **结果展示** (`ResultDisplay.tsx`)：报告、图表、数据可视化

#### 服务层
- **API服务** (`services/api.ts`)：RESTful API调用和数据处理
- **WebSocket服务** (`services/websocket.ts`)：实时通信和状态同步
- **Mock服务** (`services/mock.ts`)：开发环境模拟数据
- **后端适配器** (`adapters/backendAdapter.ts`)：前后端数据格式转换

#### 状态管理
- **工作流存储** (`store/workflowStore.ts`)：全局状态管理
- **类型定义** (`types/workflow.ts`)：TypeScript类型系统
- **自定义Hooks** (`hooks/useWebSocket.ts`)：可复用的逻辑组件

#### 工具函数
- **流程图工具** (`utils/workflowGraph.ts`)：LogicFlow集成和节点定义
- **样式文件** (`styles/workflow.css`)：专业的UI样式

### 前端启动和使用

#### 开发环境启动
```bash
# 进入前端目录
cd frontend

# 方式1: 使用启动脚本
./start.sh dev

# 方式2: 使用npm
npm install
npm run dev

# 方式3: 查看演示
open demo.html
```

#### 功能特性
1. **智能对话界面**：自然语言描述设计需求
2. **文件上传支持**：支持FASTA、PDB等生物信息学格式
3. **实时工作流可视化**：动态流程图显示执行状态
4. **迭代进度追踪**：实时显示优化进度和收敛状态
5. **结果综合展示**：报告、图表、数据下载
6. **响应式设计**：适配各种设备和屏幕尺寸

#### 前端测试
```bash
# 运行前端测试
npm test

# 兼容性测试
npm run test:compatibility

# 集成测试
./integration-test.js

# 构建生产版本
npm run build
```

### 前后端集成

#### 数据流程
1. **用户输入** → 前端表单验证 → 适配器转换 → 后端API
2. **后端处理** → 状态更新 → WebSocket推送 → 前端状态同步
3. **结果输出** → 后端响应 → 适配器转换 → 前端展示

#### 兼容性保证
- **完整的适配器层**：处理前后端数据格式差异
- **类型安全**：TypeScript确保数据结构一致性
- **测试覆盖**：单元测试和集成测试验证兼容性
- **文档完整**：详细的API文档和使用说明

#### 部署配置
```bash
# 开发环境
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8080

# 生产环境
VITE_API_BASE_URL=https://api.protein-design.com
VITE_WS_URL=wss://ws.protein-design.com
```

## 最新更新记录

### 2024-01-15 前端界面完整实现
- ✅ **完整前端架构**：React 18 + TypeScript + Ant Design + LogicFlow 2.0
- ✅ **用户交互界面**：对话式界面、文件上传、序列输入、参数配置
- ✅ **实时工作流可视化**：动态流程图、节点状态、迭代进度
- ✅ **WebSocket通信**：实时状态同步、错误处理、自动重连
- ✅ **后端适配器**：完美兼容 `src/protein_design` 模块
- ✅ **结果展示系统**：Markdown报告、统计图表、数据下载
- ✅ **响应式设计**：桌面端、平板、移动端适配
- ✅ **完整测试覆盖**：单元测试、集成测试、兼容性测试
- ✅ **部署配置**：开发环境、生产环境、Docker支持

### 前端启动方式
```bash
# 快速启动
cd frontend && ./start.sh dev

# 查看演示
open frontend/demo.html

# 集成测试
./frontend/integration-test.js
```

### 前后端数据流
```
用户界面 → 适配器 → 后端API → MCP工具 → 结果处理 → 前端展示
    ↓         ↓         ↓         ↓         ↓         ↓
  React    Backend   Python   ChAI-fold  Report   LogicFlow
 TypeScript Adapter LangGraph LigandMPNN Analysis Visualization
```

### 技术整合效果
- **无缝集成**：前端与后端 `src/protein_design` 完美对接
- **实时同步**：工作流状态实时可视化
- **用户友好**：直观的交互界面和专业的生物信息学功能
- **生产就绪**：完整的测试、部署、监控体系