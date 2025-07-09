import os
from dataclasses import dataclass, fields
from typing import Any, Optional, Dict

from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class ProteinDesignConfiguration:
    """蛋白质设计配置类"""
    
    # 模型配置
    supervisor_model: str = "openai:deepseek-r1-250528"
    supervisor_model_kwargs: Optional[Dict[str, Any]] = None
    planner_model: str = "openai:deepseek-r1-250528"
    planner_model_kwargs: Optional[Dict[str, Any]] = None
    
    # MCP工具配置 - 详见langchain_adapter_README.md文档
    mcp_server_config: Optional[Dict[str, Any]] = None
    
    # 预测设置（保留用于向后兼容）
    predict_receptor_only: bool = True
    predict_ligand_only: bool = True  
    predict_complex: bool = True
    
    # 输出配置
    output_format: str = "cif"  # cif, pdb, both
    include_detailed_scores: bool = True
    generate_report: bool = True
    
    def __post_init__(self):
        """初始化后处理配置"""
        # 自动配置DeepSeek模型参数
        for model_attr in ["supervisor_model_kwargs", "planner_model_kwargs"]:
            model_name = getattr(self, model_attr.replace("_kwargs", ""))
            if "deepseek" in model_name.lower():
                kwargs = getattr(self, model_attr) or {}
                if "base_url" not in kwargs:
                    kwargs["base_url"] = "https://ark.cn-beijing.volces.com/api/v3"
                setattr(self, model_attr, kwargs)
        
        # 设置默认MCP服务器配置
        if self.mcp_server_config is None:
            # 使用 pixi 环境中的 Python 路径
            python_path = "/root/agent_project/open_deep_research/.pixi/envs/default/bin/python"
            self.mcp_server_config = {
                "chaifold": {
                    "command": python_path,
                    "args": ["/root/agent_project/open_deep_research/src/protein_design/tool/chai_fold/mcp_server_chaifold.py"],
                    "transport": "stdio",
                },
                "scoring": {
                    "command": python_path, 
                    "args": ["/root/agent_project/open_deep_research/src/protein_design/tool/score/mcp_server_scoring.py"],
                    "transport": "stdio",
                },
                "ligandmpnn": {
                    "command": python_path,
                    "args": ["/root/agent_project/open_deep_research/src/protein_design/tool/ligandmpnn/mcp_server_ligand.py"],
                    "transport": "stdio",
                }
            }
    
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "ProteinDesignConfiguration":
        """从RunnableConfig创建配置实例"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})