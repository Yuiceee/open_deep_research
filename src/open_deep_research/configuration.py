import os
from enum import Enum
from dataclasses import dataclass, fields, field
from typing import Any, Optional, Dict, Literal

from langchain_core.runnables import RunnableConfig

DEFAULT_REPORT_STRUCTURE = """Use this structure to create a report on the user-provided topic:

1. Introduction (no research needed)
   - Brief overview of the topic area

2. Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   
3. Conclusion
   - Aim for 1 structural element (either a list or table) that distills the main body sections 
   - Provide a concise summary of the report"""

class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    LINKUP = "linkup"
    DUCKDUCKGO = "duckduckgo"
    GOOGLESEARCH = "googlesearch"
    NONE = "none"

@dataclass(kw_only=True)
class WorkflowConfiguration:
    """Configuration for the workflow/graph-based implementation (graph.py)."""
    # Common configuration
    report_structure: str = DEFAULT_REPORT_STRUCTURE
    search_api: SearchAPI = SearchAPI.TAVILY
    search_api_config: Optional[Dict[str, Any]] = None
    process_search_results: Literal["summarize", "split_and_rerank"] | None = None
    summarization_model_provider: str = "openai"
    summarization_model: str = "deepseek-r1-250528"
    max_structured_output_retries: int = 3
    include_source_str: bool = False
    
    # Workflow-specific configuration
    number_of_queries: int = 2 # Number of search queries to generate per iteration
    max_search_depth: int = 2 # Maximum number of reflection + search iterations
    planner_provider: str = "openai"
    planner_model: str = "deepseek-r1-250528"
    planner_model_kwargs: Optional[Dict[str, Any]] = None
    writer_provider: str = "openai"
    writer_model: str = "deepseek-r1-250528"
    writer_model_kwargs: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Auto-configure model kwargs based on provider and model."""
        # Auto-configure planner model kwargs
        if self.planner_provider.lower() == "openai" and self.planner_model.startswith("deepseek"):
            if self.planner_model_kwargs is None:
                self.planner_model_kwargs = {}
            if "base_url" not in self.planner_model_kwargs:
                self.planner_model_kwargs["base_url"] = "https://ark.cn-beijing.volces.com/api/v3"
        
        # Auto-configure writer model kwargs
        if self.writer_provider.lower() == "openai" and self.writer_model.startswith("deepseek"):
            if self.writer_model_kwargs is None:
                self.writer_model_kwargs = {}
            if "base_url" not in self.writer_model_kwargs:
                self.writer_model_kwargs["base_url"] = "https://ark.cn-beijing.volces.com/api/v3"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "WorkflowConfiguration":
        """Create a WorkflowConfiguration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})

@dataclass(kw_only=True)
class MultiAgentConfiguration:
    """Configuration for the multi-agent implementation (multi_agent.py)."""
    # Common configuration
    search_api: SearchAPI = SearchAPI.TAVILY
    search_api_config: Optional[Dict[str, Any]] = None
    process_search_results: Literal["summarize", "split_and_rerank"] | None = None
    summarization_model_provider: str = "openai"
    summarization_model: str = "deepseek-r1-250528"
    include_source_str: bool = False
    
    # Multi-agent specific configuration
    number_of_queries: int = 2 # Number of search queries to generate per section
    supervisor_model: str = "openai:deepseek-r1-250528"
    supervisor_model_kwargs: Optional[Dict[str, Any]] = None
    researcher_model: str = "openai:deepseek-r1-250528"
    researcher_model_kwargs: Optional[Dict[str, Any]] = None
    ask_for_clarification: bool = False # Whether to ask for clarification from the user
    # MCP server configuration
    mcp_server_config: Optional[Dict[str, Any]] = None
    mcp_prompt: Optional[str] = None
    mcp_tools_to_include: Optional[list[str]] = None
    
    def __post_init__(self):
        """Auto-configure model kwargs based on provider and model."""
        # Parse supervisor model (format: "provider:model" or just "model")
        if ":" in self.supervisor_model:
            supervisor_provider, supervisor_model_name = self.supervisor_model.split(":", 1)
        else:
            supervisor_provider = "openai"  # default
            supervisor_model_name = self.supervisor_model
            
        # Auto-configure supervisor model kwargs
        if supervisor_provider.lower() == "openai" and supervisor_model_name.startswith("deepseek"):
            if self.supervisor_model_kwargs is None:
                self.supervisor_model_kwargs = {}
            if "base_url" not in self.supervisor_model_kwargs:
                self.supervisor_model_kwargs["base_url"] = "https://ark.cn-beijing.volces.com/api/v3"
        
        # Parse researcher model (format: "provider:model" or just "model")
        if ":" in self.researcher_model:
            researcher_provider, researcher_model_name = self.researcher_model.split(":", 1)
        else:
            researcher_provider = "openai"  # default
            researcher_model_name = self.researcher_model
            
        # Auto-configure researcher model kwargs
        if researcher_provider.lower() == "openai" and researcher_model_name.startswith("deepseek"):
            if self.researcher_model_kwargs is None:
                self.researcher_model_kwargs = {}
            if "base_url" not in self.researcher_model_kwargs:
                self.researcher_model_kwargs["base_url"] = "https://ark.cn-beijing.volces.com/api/v3"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "MultiAgentConfiguration":
        """Create a MultiAgentConfiguration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})

# Keep the old Configuration class for backward compatibility
Configuration = WorkflowConfiguration
