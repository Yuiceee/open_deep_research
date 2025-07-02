# LigandMPNN Tool - 优化版设计说明

## 设计理念

这个优化版MCP工具解决了LLM调用复杂生物信息学工具时的核心问题：**如何让LLM智能选择合适的参数**。

### 核心策略

1. **预设模板 + 自定义参数**
   - 提供5个精心设计的预设配置
   - LLM可根据用户需求智能选择预设
   - 专家用户仍可使用自定义参数

2. **清晰的Schema + 丰富的文档**
   - 每个参数都有详细说明和建议值
   - 在docstring中提供使用场景和示例
   - 参数验证和错误提示

3. **层次化工具设计**
   - `run_ligandmpnn_preset`: 简单易用，LLM优先选择
   - `run_ligandmpnn_custom`: 高级功能，专家使用
   - `run_ligandmpnn_workflow`: 批量处理，集成工作流
   - `get_ligandmpnn_presets`: 信息查询，辅助决策

## 预设配置策略

基于`run_examples.sh`中的典型用法，设计了5个预设：

| 预设 | 温度 | 批次数 | 使用场景 |
|------|------|--------|----------|
| standard | 0.1 | 40 | 标准蛋白质设计，推荐起始点 |
| diverse | 0.3 | 80 | 高多样性探索，突破局部最优 |
| conservative | 0.05 | 20 | 保守设计，接近原始序列 |
| quick | 0.2 | 10 | 快速测试，验证工具 |
| batch_production | 0.2 | 100 | 大规模生产，充足资源 |

## LLM使用指南

### 典型对话流程

**用户**: "我想用LigandMPNN设计一个蛋白质序列，PDB文件是complex.pdb，设计B链"

**LLM推理过程**:
1. 识别关键信息：PDB文件路径、设计链B
2. 选择工具：优先使用`run_ligandmpnn_preset`
3. 选择预设：标准设计场景 → `standard`预设
4. 调用工具

**用户**: "我需要更多样化的序列，生成更多候选"

**LLM推理过程**:
1. 理解需求：多样化 + 更多序列
2. 选择预设：`diverse`预设（温度0.3，80个序列）

### Few-shot示例

工具文档中包含丰富的使用示例：

```python
# 标准设计
run_ligandmpnn_preset(pdb_file="complex.pdb", preset="standard", design_chain="B")

# 多样化探索  
run_ligandmpnn_preset(pdb_file="complex.pdb", preset="diverse", design_chain="A,B")

# 批量工作流程
run_ligandmpnn_workflow(cluster_results_file="score.json", preset="standard")
```

## 与现有config.py的关系

1. **继承核心概念**: 保留了ModelType、参数验证等设计
2. **简化复杂度**: 将复杂的嵌套配置扁平化为直接参数
3. **保持兼容性**: 底层仍调用相同的`run_mpnn`函数

## 优势

### 对LLM友好
- **明确的选择空间**: 5个预设 vs 数十个参数组合
- **丰富的上下文**: 每个选项都有详细说明
- **实用的示例**: 覆盖常见使用场景

### 对用户友好
- **快速上手**: 新手使用预设即可
- **专业控制**: 专家可使用custom工具
- **工作流集成**: 直接支持迭代设计流程

### 对系统友好
- **参数验证**: 防止无效输入
- **错误处理**: 清晰的错误信息
- **结构化输出**: JSON格式便于解析

## 工作流程集成

完美支持蛋白质设计的迭代循环：

```
chaifold评分(score.json) → LigandMPNN批量设计 → 序列提取 → 下一轮chaifold
```

`run_ligandmpnn_workflow`工具专门为此设计，可以：
- 自动读取chaifold的评分结果
- 批量处理多个聚类结构
- 应用一致的设计参数
- 生成统计报告

## 未来扩展

1. **动态预设**: 根据PDB特征自动推荐预设
2. **参数学习**: 从历史使用中学习最优参数组合
3. **质量预测**: 预估不同参数组合的成功概率
4. **自适应批次**: 根据资源情况动态调整批次数

这个设计在保持专业功能的同时，大大降低了LLM调用的复杂度，是复杂科学工具MCP化的一个很好的范例。