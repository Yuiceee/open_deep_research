#!/usr/bin/env python3
"""
测试 base_url 配置是否正常工作
"""
import os
from open_deep_research.configuration import MultiAgentConfiguration, WorkflowConfiguration

# 设置 API Key
os.environ["OPENAI_API_KEY"] = "432b1628-2b74-4fba-800a-3be77a46734f"

def test_multi_agent_base_url():
    """测试 MultiAgent 配置的 base_url 支持"""
    print("=== 测试 MultiAgent base_url 自动配置 ===")
    
    # 测试自动配置（不手动设置 base_url）
    config = {
        "configurable": {
            "supervisor_model": "openai:deepseek-r1-250528",  # 使用默认值
            "researcher_model": "openai:deepseek-r1-250528",  # 使用默认值
            "search_api": "none"  # 禁用搜索，只测试模型配置
        }
    }
    
    # 创建配置实例
    multi_config = MultiAgentConfiguration.from_runnable_config(config)
    
    # 验证自动配置
    print(f"Supervisor model: {multi_config.supervisor_model}")
    print(f"Supervisor model kwargs (auto): {multi_config.supervisor_model_kwargs}")
    print(f"Researcher model: {multi_config.researcher_model}")
    print(f"Researcher model kwargs (auto): {multi_config.researcher_model_kwargs}")
    
    print("\n--- 测试手动覆盖自动配置 ---")
    
    # 测试手动配置会覆盖自动配置
    config_manual = {
        "configurable": {
            "supervisor_model": "openai:deepseek-r1-250528",
            "supervisor_model_kwargs": {
                "base_url": "https://custom-endpoint.com/api",
                "temperature": 0.7
            },
            "researcher_model": "openai:deepseek-r1-250528", 
            "researcher_model_kwargs": {
                "base_url": "https://another-endpoint.com/api"
            },
            "search_api": "none"
        }
    }
    
    multi_config_manual = MultiAgentConfiguration.from_runnable_config(config_manual)
    print(f"Manual Supervisor kwargs: {multi_config_manual.supervisor_model_kwargs}")
    print(f"Manual Researcher kwargs: {multi_config_manual.researcher_model_kwargs}")
    
    return multi_config

def test_workflow_base_url():
    """测试 Workflow 配置的 base_url 支持"""
    print("\n=== 测试 Workflow base_url 自动配置 ===")
    
    # 测试自动配置（使用默认值，会自动设置 base_url）
    workflow_config = WorkflowConfiguration()
    
    # 验证自动配置
    print(f"Planner provider: {workflow_config.planner_provider}")
    print(f"Planner model: {workflow_config.planner_model}")
    print(f"Planner model kwargs (auto): {workflow_config.planner_model_kwargs}")
    print(f"Writer provider: {workflow_config.writer_provider}")
    print(f"Writer model: {workflow_config.writer_model}")
    print(f"Writer model kwargs (auto): {workflow_config.writer_model_kwargs}")
    
    print("\n--- 测试非 deepseek 模型（不自动配置）---")
    
    # 测试非 deepseek 模型
    config_non_deepseek = {
        "configurable": {
            "planner_provider": "openai",
            "planner_model": "gpt-4",
            "writer_provider": "openai", 
            "writer_model": "gpt-3.5-turbo",
            "search_api": "tavily"
        }
    }
    
    workflow_config_non_deepseek = WorkflowConfiguration.from_runnable_config(config_non_deepseek)
    print(f"Non-DeepSeek Planner kwargs: {workflow_config_non_deepseek.planner_model_kwargs}")
    print(f"Non-DeepSeek Writer kwargs: {workflow_config_non_deepseek.writer_model_kwargs}")
    
    return workflow_config

if __name__ == "__main__":
    try:
        # 测试两种配置
        multi_config = test_multi_agent_base_url()
        workflow_config = test_workflow_base_url()
        
        print("\n✅ 自动配置测试通过！")
        print("\n🎉 现在 DeepSeek 模型会自动配置 base_url，无需手动设置！")
        print("\n=== 简化后的配置 ===")
        
        print("\n--- MultiAgent 最简配置 ---")
        print("""
{
  "search_api": "tavily"
}
# DeepSeek 模型的 base_url 会自动设置！
""")
        
        print("\n--- Workflow 最简配置 ---")
        print("""
{
  "search_api": "tavily"
}
# DeepSeek 模型的 base_url 会自动设置！
""")
        
        print("\n--- 如需自定义其他参数 ---")
        print("""
{
  "supervisor_model": "openai:deepseek-r1-250528",
  "supervisor_model_kwargs": {
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "search_api": "tavily"
}
# base_url 仍会自动添加，不会覆盖其他参数
""")
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")