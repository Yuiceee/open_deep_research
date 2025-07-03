#!/usr/bin/env python
"""
MCP工具使用示例
展示如何在Open Deep Research中集成和使用MCP工具
"""

import asyncio
import json
from open_deep_research.multi_agent import graph
from open_deep_research.configuration import MultiAgentConfiguration

# MCP服务器配置
MCP_SERVER_CONFIG = {
    "servers": {
        "ligandmpnn": {
            "command": [
                "python", 
                "src/open_deep_research/tool/ligandmpnn/mcp_server_ligand.py"
            ],
            "env": {}
        }
    }
}

async def example_with_mcp_tools():
    """使用MCP工具进行蛋白质设计研究的示例"""
    
    # 配置Multi-Agent系统
    config = {
        "configurable": MultiAgentConfiguration(
            # 模型配置
            supervisor_model="anthropic:claude-3-7-sonnet-latest",
            researcher_model="anthropic:claude-3-5-sonnet-latest",
            
            # 搜索配置
            search_api="tavily",
            number_of_queries=3,
            
            # MCP工具配置
            mcp_server_config=MCP_SERVER_CONFIG,
            mcp_prompt="""
你现在可以使用专业的配体蛋白设计工具：
- ligand_design_basic: 基础配体蛋白设计（保守策略）
- ligand_design_intermediate: 中级配体蛋白设计（平衡策略）  
- ligand_design_advanced: 高级配体蛋白设计（探索策略）
- get_ligand_design_presets: 获取设计预设信息

在需要进行分子设计、蛋白质优化或结构分析时，请使用这些工具。
            """,
            # 可选：指定要包含的工具
            mcp_tools_to_include=[
                "ligand_design_basic", 
                "ligand_design_intermediate",
                "get_ligand_design_presets"
            ]
        )
    }
    
    # 执行研究任务
    print("🧬 开始蛋白质设计研究...")
    
    research_topic = """
    请为我生成一份关于"配体结合蛋白设计方法与工具"的详细研究报告。
    
    重点关注：
    1. 当前主流的配体结合蛋白设计方法
    2. 计算工具和算法比较
    3. 实际应用案例分析
    4. 如果可能，请使用可用的设计工具展示具体设计流程
    """
    
    try:
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": research_topic}]},
            config=config
        )
        
        print("✅ 研究完成！")
        print("\n" + "="*80)
        print("📋 生成的研究报告:")
        print("="*80)
        print(result["final_report"])
        
        # 如果有源资料信息，也打印出来
        if result.get("source_str"):
            print("\n" + "="*80)
            print("📚 研究源资料:")
            print("="*80)
            print(result["source_str"])
            
    except Exception as e:
        print(f"❌ 研究过程中出现错误: {str(e)}")

async def example_direct_mcp_usage():
    """直接使用MCP工具的示例（不通过研究框架）"""
    
    print("🔧 直接MCP工具使用示例...")
    
    # 这里展示如何直接调用MCP工具
    # 注意：实际使用中MCP工具会通过LangChain集成到对话流程中
    
    print("""
    直接使用MCP工具的步骤：
    
    1. 启动MCP服务器：
       python src/open_deep_research/tool/ligandmpnn/mcp_server_ligand.py
    
    2. 通过Multi-Agent系统调用：
       - 系统会自动加载配置的MCP工具
       - AI智能体可以根据需要调用相应工具
       - 工具调用结果会集成到研究报告中
    
    3. 可用的配体设计工具：
       - ligand_design_basic(pdb_file, output_dir, design_chain)
       - ligand_design_intermediate(pdb_file, output_dir, design_chain, custom_temperature)
       - ligand_design_advanced(pdb_file, output_dir, design_chain, max_batches, include_rare_aa)
    """)

async def example_custom_mcp_config():
    """自定义MCP配置的示例"""
    
    # 更复杂的MCP配置示例
    advanced_mcp_config = {
        "servers": {
            "ligandmpnn": {
                "command": [
                    "python", 
                    "src/open_deep_research/tool/ligandmpnn/mcp_server_ligand.py"
                ],
                "env": {
                    "CUDA_VISIBLE_DEVICES": "0",  # 指定GPU
                    "DOCKER_HOST": "unix:///var/run/docker.sock"  # Docker配置
                }
            },
            # 可以添加更多MCP服务器
            # "other_tool": {
            #     "command": ["python", "path/to/other_mcp_server.py"],
            #     "env": {}
            # }
        }
    }
    
    config = {
        "configurable": MultiAgentConfiguration(
            supervisor_model="anthropic:claude-3-7-sonnet-latest",
            researcher_model="anthropic:claude-3-5-sonnet-latest",
            search_api="tavily",
            
            # 高级MCP配置
            mcp_server_config=advanced_mcp_config,
            mcp_prompt="""
你是一个专业的生物信息学研究助手，具备以下专业工具：

🧬 配体蛋白设计工具套件：
- 基础设计：保守策略，高稳定性
- 中级设计：平衡质量与多样性  
- 高级设计：最大探索性，创新设计

在进行蛋白质相关研究时，请充分利用这些专业工具来：
1. 验证理论分析
2. 提供实际设计示例
3. 展示计算流程
4. 生成具体结果

请根据具体需求选择合适的设计级别。
            """,
            
            # 精确控制工具包含
            mcp_tools_to_include=[
                "ligand_design_basic",
                "ligand_design_intermediate", 
                "ligand_design_advanced",
                "get_ligand_design_presets"
            ]
        )
    }
    
    print("📋 自定义MCP配置已创建")
    print(json.dumps(advanced_mcp_config, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("🚀 Open Deep Research MCP工具集成示例")
    print("="*60)
    
    # 运行示例
    asyncio.run(example_with_mcp_tools())
    
    print("\n" + "="*60)
    asyncio.run(example_direct_mcp_usage())
    
    print("\n" + "="*60)
    asyncio.run(example_custom_mcp_config())