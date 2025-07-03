
目标，基于workflow的类型，构建蛋白设计的workflow，input一条receptor序列，可以查询这个receptor序列的特性，为这条receptor 设计对应的ligand。
初期目标
1.  input为receptor 和 候选ligand的序列。fasata格式，先接受一条
2.  chaifold进行打分。基于已有的chaifold mcp，生成receptor、ligand、receptor+receptor三种结构
3.  对结果进行打分，基于score mcp，
4. 基于打分结果进行优化设计liandmpnn
5. 报告生成


参考chatgpt的回答：https://chatgpt.com/share/68652ec5-7978-8007-b4b8-bd9b2b543764

------



参考文件 
 prompts.py - 提示词模板库

  定义了研究系统中所有AI智能体的提示词指令：

  主要组件：
  - report_planner_query_writer_instructions - 报告规划查询生成器的指令
  - report_planner_instructions - 报告结构规划器的指令
  - section_writer_instructions - 章节写作器的指令（150-200字限制）
  - SUPERVISOR_INSTRUCTIONS - 多智能体系统监督者指令
  - RESEARCH_INSTRUCTIONS - 研究员智能体指令
  - SUMMARIZATION_PROMPT - 网页内容摘要提示词

  特点：
  - 每个智能体都有详细的角色定义和任务流程
  - 包含格式化要求和质量检查标准
  - 支持中英文混合使用

  state.py - 状态数据结构

  定义了系统中的数据模型和状态管理：

  核心模型：
  - Section - 报告章节模型（名称、描述、是否需要研究、内容）
  - SearchQuery - 搜索查询模型
  - ReportState - 完整报告状态（话题、反馈、章节、完成状态等）
  - SectionState - 单个章节的处理状态

  用途：
  - LangGraph工作流的状态管理
  - 数据验证和类型安全
  - 多智能体间的数据传递

  utils.py - 核心工具库

  包含所有搜索API集成和工具函数：

  搜索引擎支持：
  - Tavily - 优化的web搜索API
  - Perplexity - AI驱动的搜索
  - Exa - 语义搜索引擎
  - ArXiv - 学术论文搜索
  - PubMed - 医学文献搜索
  - Google搜索 - 支持API和爬虫模式
  - DuckDuckGo - 隐私友好搜索

  核心功能：
  - 异步并发搜索处理
  - 搜索结果去重和格式化
  - 内容摘要和重排序
  - 网页抓取和Markdown转换
  - MCP服务器配置加载

  configuration.py - 配置管理

  提供系统配置的数据类和管理：

  配置类：
  - WorkflowConfiguration - 图工作流配置（graph.py使用）
  - MultiAgentConfiguration - 多智能体配置（multi_agent.py使用）

  配置项包括：
  - 搜索API选择和参数
  - 模型提供商和模型名称
  - 查询数量和搜索深度
  - MCP工具集成配置
  - 结果处理策略（摘要/重排序）

  智能特性：
  - 自动配置DeepSeek模型的base_url
  - 从环境变量和运行时配置读取参数
  - 支持向后兼容