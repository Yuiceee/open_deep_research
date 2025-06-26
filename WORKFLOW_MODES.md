# Open Deep Research - 工作流模式说明

Open Deep Research 提供三种不同的工作流模式，每种模式都有其独特的架构和适用场景。

## 模式概览

### 1. `open_deep_research` - 基于图的工作流（无Agent）
**架构特点：**
- 纯函数式节点处理
- 直接调用LLM完成任务
- 状态在节点间传递，无智能代理
- 结构化计划执行：先生成报告计划，再逐段执行
- 人机交互：支持计划审查和反馈循环

**适用场景：**
- 高精度研究任务
- 需要结构化控制的报告生成
- 学术或专业研究环境

### 2. `open_deep_research_multi_agent` - 多Agent架构
**架构特点：**
- 使用 `MessagesState` 基于消息的Agent通信
- **Supervisor Agent**: 管理整体流程和协调
- **Researcher Agents**: 专门负责并行研究任务
- Agent间可以对话和协作
- 并行处理，速度更快

**适用场景：**
- 快速研究和报告生成
- 需要并行处理的复杂任务
- 商业智能和市场研究

### 3. `odr_workflow_v2` - 增强工作流（无Agent）
**架构特点：**
- 类似 graph.py 但功能更丰富
- 增加了用户澄清功能
- 初始路由器决定是否需要澄清
- 仍然是函数式节点，无智能代理
- 改进的状态管理

**适用场景：**
- 交互式研究流程
- 需要用户澄清需求的场景
- 灵活配置的研究任务

## 使用命令

### 启动不同模式

```bash
# 1. 默认模式（基于图的工作流）
langgraph dev

# 或者明确指定
langgraph dev --graph open_deep_research
langgraph dev open_deep_research

# 2. 多Agent模式
langgraph dev --graph open_deep_research_multi_agent
langgraph dev open_deep_research_multi_agent

# 3. 增强工作流模式
langgraph dev --graph odr_workflow_v2
langgraph dev odr_workflow_v2
```

### 测试不同模式

```bash
# 测试多Agent模式
python tests/run_test.py --agent multi_agent

# 测试基于图的工作流
python tests/run_test.py --agent graph
```

## 核心区别总结

| 特性 | open_deep_research | open_deep_research_multi_agent | odr_workflow_v2 |
|------|-------------------|--------------------------------|-----------------|
| **架构类型** | 无Agent（函数式） | 多Agent（智能代理） | 无Agent（函数式增强） |
| **处理方式** | 顺序处理 | 并行处理 | 顺序处理 |
| **交互能力** | 计划审查 | Agent对话协作 | 用户澄清 |
| **速度** | 中等 | 最快 | 中等 |
| **控制精度** | 高 | 中等 | 高 |
| **适用场景** | 高精度研究 | 快速研究 | 交互式研究 |

## 选择建议

- **需要高精度和结构化控制** → 使用 `open_deep_research`
- **需要快速生成报告** → 使用 `open_deep_research_multi_agent`
- **需要用户交互和澄清** → 使用 `odr_workflow_v2`