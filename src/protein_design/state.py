from typing import TypedDict, List, Dict, Any, Annotated, Optional
import operator

class ProteinDesignState(TypedDict):
    """蛋白质设计状态管理"""
    
    # 输入数据
    single_sequence: Optional[str]
    receptor_sequence: Optional[str]
    ligand_sequence: Optional[str]
    work_dir: str
    optimization_target: str
    max_iterations: int
    convergence_threshold: float
    
    # 设计场景
    design_scenario: str  # 'single_sequence' 或 'ligand_optimization'
    
    # 迭代状态
    current_iteration: int
    iteration_history: Annotated[List[Dict[str, Any]], operator.add]
    best_score: float
    previous_score: float
    has_converged: bool
    current_sequence: str  # 当前正在优化的序列
    
    # 结果累积 - 使用operator.add进行状态合并
    predictions: Annotated[List[Dict[str, Any]], operator.add]
    scores: Annotated[List[Dict[str, Any]], operator.add]
    optimizations: Annotated[List[Dict[str, Any]], operator.add]
    
    # 流程状态
    current_step: str
    completed_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    
    # 最终结果
    final_report: Optional[str]
    best_complex: Optional[Dict[str, Any]]

class ProteinDesignInput(TypedDict):
    """蛋白质设计输入"""
    # 两种场景：单条序列优化 OR 配体优化
    single_sequence: Optional[str]           # 单条序列优化场景
    receptor_sequence: Optional[str]         # 配体优化场景 - 固定的受体
    ligand_sequence: Optional[str]           # 配体优化场景 - 待优化的配体
    
    work_dir: Optional[str]
    optimization_target: Optional[str]       # 优化目标：'enzyme_activity', 'binding_affinity'
    max_iterations: Optional[int]            # 最大迭代轮次
    convergence_threshold: Optional[float]   # 收敛阈值

class ProteinDesignOutput(TypedDict):
    """蛋白质设计输出"""
    final_report: str
    best_complex: Dict[str, Any]
    optimization_results: List[Dict[str, Any]]

class PredictionResult(TypedDict):
    """结构预测结果"""
    receptor_structure: Optional[str]
    ligand_structure: Optional[str]
    complex_structure: Optional[str]
    confidence_scores: Dict[str, float]
    prediction_id: str

class ScoreResult(TypedDict):
    """评分结果"""
    binding_affinity: float
    structural_quality: float
    interaction_strength: float
    druggability_score: float
    prediction_id: str

class OptimizationResult(TypedDict):
    """优化结果"""
    optimized_sequence: str
    optimization_type: str
    improvement_score: float
    iteration_number: int
    parent_prediction_id: str