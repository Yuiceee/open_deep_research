import os
import uuid
import tempfile
from typing import Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from langchain_mcp_adapters.client import MultiServerMCPClient

from protein_design.state import (
    ProteinDesignState,
    ProteinDesignInput,
    ProteinDesignOutput,
    PredictionResult,
    ScoreResult,
    OptimizationResult
)
from protein_design.prompts import (
    PROTEIN_DESIGN_REPORTER_INSTRUCTIONS,
    PROTEIN_DESIGN_ERROR_HANDLER_INSTRUCTIONS
)
from protein_design.configuration import ProteinDesignConfiguration
from protein_design.utils import create_session_directory, create_directories_async

def get_today_str() -> str:
    """获取今天的日期字符串"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

async def get_mcp_tools(config: ProteinDesignConfiguration):
    """获取MCP工具"""
    client = MultiServerMCPClient(config.mcp_server_config)
    return await client.get_tools()

# 工作流节点

async def input_analysis_node(state: ProteinDesignState, config: RunnableConfig = None):
    """输入分析节点 - 确定设计场景并初始化状态"""
    
    # 确定设计场景
    if state.get("single_sequence"):
        design_scenario = "single_sequence"
        current_sequence = state["single_sequence"]
    elif state.get("receptor_sequence") and state.get("ligand_sequence"):
        design_scenario = "ligand_optimization"
        current_sequence = state["ligand_sequence"]  # 优化配体序列
    else:
        return {
            "current_step": "error",
            "errors": ["输入数据不完整：需要单条序列或受体+配体序列"]
        }
    
    # 设置默认值
    max_iterations = state.get("max_iterations", 3)
    convergence_threshold = state.get("convergence_threshold", 0.01)
    optimization_target = state.get("optimization_target", "binding_affinity" if design_scenario == "ligand_optimization" else "enzyme_activity")
    
    return {
        "design_scenario": design_scenario,
        "current_sequence": current_sequence,
        "max_iterations": max_iterations,
        "convergence_threshold": convergence_threshold,
        "optimization_target": optimization_target,
        "current_iteration": 0,
        "best_score": float('-inf'),
        "previous_score": float('-inf'),
        "has_converged": False,
        "current_step": "iteration_control",
        "completed_steps": ["input_analysis"],
        "work_dir": state.get("work_dir") or create_session_directory()
    }

async def iteration_control_node(state: ProteinDesignState, config: RunnableConfig = None):
    """迭代控制节点 - 决定是否继续迭代"""
    
    # 检查是否达到最大迭代次数
    if state["current_iteration"] >= state["max_iterations"]:
        return {
            "current_step": "reporting",
            "completed_steps": ["iteration_control"]
        }
    
    # 检查是否收敛
    if state["has_converged"]:
        return {
            "current_step": "reporting",
            "completed_steps": ["iteration_control"]
        }
    
    # 继续迭代
    return {
        "current_step": "prediction",
        "completed_steps": ["iteration_control"]
    }

async def prediction_node(state: ProteinDesignState, config: RunnableConfig):
    """预测节点 - 根据场景进行结构预测"""
    configuration = ProteinDesignConfiguration.from_runnable_config(config)
    
    try:
        # 获取MCP工具
        try:
            tools = await get_mcp_tools(configuration)
        except Exception as mcp_error:
            return {
                "current_step": "error", 
                "errors": [f"获取MCP工具失败: {str(mcp_error)}"]
            }
        
        chaifold_tool = next((t for t in tools if "run_chaifold" in t.name), None)
        scoring_tool = next((t for t in tools if "create_fasta_from_sequences" in t.name), None)
        
        if not chaifold_tool:
            return {
                "current_step": "error", 
                "errors": [f"未找到ChAI-fold工具，可用工具: {[t.name for t in tools]}"]
            }
        if not scoring_tool:
            return {
                "current_step": "error", 
                "errors": [f"未找到Scoring工具，可用工具: {[t.name for t in tools]}"]
            }
        
        predictions = []
        
        # 使用新的工作目录管理系统创建目录结构
        dirs = await create_directories_async(state["work_dir"], state["current_iteration"])
        iteration_dir = dirs["iteration_dir"]
        input_files_dir = dirs["input_files_dir"]
        chaifold_output_dir = dirs["chaifold_output_dir"]
        
        if state["design_scenario"] == "single_sequence":
            # 单序列预测 - 创建FASTA文件
            fasta_file = os.path.join(input_files_dir, "input.fasta")
            fasta_result = await scoring_tool.ainvoke({
                "sequences": [state["current_sequence"]],
                "output_file": fasta_file,
                "sequence_names": [f"protein|iter_{state['current_iteration']}"]
            })
            
            if "error" in fasta_result:
                return {
                    "current_step": "error",
                    "errors": [f"创建FASTA文件失败: {fasta_result}"]
                }
            
            # 运行ChAI-fold预测
            output_folder = chaifold_output_dir
            _ = await chaifold_tool.ainvoke({
                "fasta_file": fasta_file,
                "output_folder": output_folder
            })
            
            prediction = PredictionResult(
                receptor_structure=os.path.join(output_folder, "pred.model_idx_0.cif"),
                ligand_structure=None,
                complex_structure=None,
                confidence_scores={},
                prediction_id=f"single_iter_{state['current_iteration']}"
            )
            predictions.append(prediction)
            
        elif state["design_scenario"] == "ligand_optimization":
            # 配体优化 - 创建复合物FASTA文件
            fasta_file = os.path.join(input_files_dir, "complex.fasta")
            sequences = [state["receptor_sequence"], state["current_sequence"]]
            sequence_names = ["receptor|A", "ligand|B"]
            
            fasta_result = await scoring_tool.ainvoke({
                "sequences": sequences,
                "output_file": fasta_file,
                "sequence_names": sequence_names
            })
            
            if "error" in fasta_result:
                return {
                    "current_step": "error",
                    "errors": [f"创建复合物FASTA文件失败: {fasta_result}"]
                }
            
            # 运行ChAI-fold预测
            output_folder = chaifold_output_dir
            _ = await chaifold_tool.ainvoke({
                "fasta_file": fasta_file,
                "output_folder": output_folder
            })
            
            prediction = PredictionResult(
                receptor_structure=None,
                ligand_structure=None,
                complex_structure=os.path.join(output_folder, "pred.model_idx_0.cif"),
                confidence_scores={},
                prediction_id=f"complex_iter_{state['current_iteration']}"
            )
            predictions.append(prediction)
        
        return {
            "current_step": "scoring",
            "completed_steps": ["prediction"],
            "predictions": predictions
        }
        
    except Exception as e:
        return {
            "current_step": "error",
            "errors": [f"预测阶段出错: {str(e)}"]
        }

async def scoring_node(state: ProteinDesignState, config: RunnableConfig):
    """评分节点 - 根据优化目标进行评分"""
    configuration = ProteinDesignConfiguration.from_runnable_config(config)
    
    try:
        # 获取MCP工具
        tools = await get_mcp_tools(configuration)
        find_best_model_tool = next((t for t in tools if "find_best_model" in t.name), None)
        analyze_quality_tool = next((t for t in tools if "analyze_prediction_quality" in t.name), None)
        
        if not find_best_model_tool or not analyze_quality_tool:
            return {
                "current_step": "error",
                "errors": ["未找到评分分析工具"]
            }
        
        scores = []
        
        # 对当前迭代的预测结果进行评分
        current_predictions = [p for p in state["predictions"] if f"iter_{state['current_iteration']}" in p["prediction_id"]]
        
        for prediction in current_predictions:
            # 确定结果目录
            if prediction.get("complex_structure"):
                result_dir = os.path.dirname(prediction["complex_structure"])
            elif prediction.get("receptor_structure"):
                result_dir = os.path.dirname(prediction["receptor_structure"])
            else:
                continue
            
            # 找到最佳模型
            best_model_result = await find_best_model_tool.ainvoke({
                "result_dir": result_dir,
                "model_count": 5
            })
            
            if "error" not in best_model_result:
                import json
                best_model_data = json.loads(best_model_result)
                if best_model_data["status"] == "success":
                    best_model = best_model_data["best_model"]
                    
                    # 分析预测质量
                    quality_result = await analyze_quality_tool.ainvoke({
                        "npz_file": best_model["npz_file"]
                    })
                    
                    if "error" not in quality_result:
                        quality_data = json.loads(quality_result)
                        if quality_data["status"] == "success":
                            quality_assessment = quality_data["quality_assessment"]
                            
                            score = ScoreResult(
                                binding_affinity=quality_assessment.get("iptm", 0.0),  # 使用iptm作为结合亲和力
                                structural_quality=quality_assessment.get("ptm", 0.0),
                                interaction_strength=quality_assessment.get("iptm", 0.0),
                                druggability_score=quality_assessment.get("aggregate_score", 0.0),
                                prediction_id=prediction["prediction_id"]
                            )
                            scores.append(score)
        
        # 计算当前迭代的最佳分数
        current_best_score = 0.0
        if scores:
            if state["optimization_target"] == "binding_affinity":
                current_best_score = max(scores, key=lambda x: x["binding_affinity"])["binding_affinity"]
            elif state["optimization_target"] == "enzyme_activity":
                current_best_score = max(scores, key=lambda x: x["structural_quality"])["structural_quality"]
        
        # 更新迭代状态
        score_improvement = current_best_score - state["previous_score"]
        has_converged = abs(score_improvement) < state["convergence_threshold"]
        
        # 记录迭代历史
        iteration_record = {
            "iteration": state["current_iteration"],
            "sequence": state["current_sequence"],
            "score": current_best_score,
            "improvement": score_improvement,
            "predictions": current_predictions,
            "scores": scores
        }
        
        # 更新最佳结果
        best_complex = None
        if current_best_score > state["best_score"]:
            best_score = current_best_score
            best_prediction = current_predictions[0] if current_predictions else None
            best_complex = {
                "prediction": best_prediction,
                "score": scores[0] if scores else None,
                "iteration": state["current_iteration"]
            }
        else:
            best_score = state["best_score"]
            best_complex = state.get("best_complex")
        
        return {
            "current_step": "optimization",
            "completed_steps": ["scoring"],
            "scores": scores,
            "best_score": best_score,
            "previous_score": current_best_score,
            "has_converged": has_converged,
            "best_complex": best_complex,
            "iteration_history": [iteration_record]
        }
        
    except Exception as e:
        return {
            "current_step": "error",
            "errors": [f"评分阶段出错: {str(e)}"]
        }

async def optimization_node(state: ProteinDesignState, config: RunnableConfig):
    """优化节点 - 根据场景优化序列"""
    configuration = ProteinDesignConfiguration.from_runnable_config(config)
    
    try:
        # 获取目录信息
        dirs = await create_directories_async(state["work_dir"], state["current_iteration"])
        iteration_dir = dirs["iteration_dir"]
        ligandmpnn_output_dir = dirs["ligandmpnn_output_dir"]
        
        # 获取MCP工具
        tools = await get_mcp_tools(configuration)
        ligand_basic_tool = next((t for t in tools if "ligand_design_basic" in t.name), None)
        convert_cif_tool = next((t for t in tools if "convert_cif_to_pdb" in t.name), None)
        
        if not ligand_basic_tool or not convert_cif_tool:
            # 如果没有优化工具，直接结束迭代
            return {
                "current_step": "reporting",
                "completed_steps": ["optimization"],
                "optimizations": []
            }
        
        # 获取当前最佳预测结果
        current_predictions = [p for p in state["predictions"] if f"iter_{state['current_iteration']}" in p["prediction_id"]]
        if not current_predictions:
            return {
                "current_step": "error",
                "errors": ["没有找到当前迭代的预测结果"]
            }
        
        target_prediction = current_predictions[0]
        
        # 根据场景选择优化策略
        if state["design_scenario"] == "single_sequence":
            # 单序列优化场景暂时跳过LigandMPNN优化
            return {
                "current_step": "iteration_control", 
                "completed_steps": ["optimization"],
                "optimizations": [],
                "current_sequence": state["current_sequence"],  # 保持原序列
                "current_iteration": state["current_iteration"] + 1
            }
            
        elif state["design_scenario"] == "ligand_optimization":
            # 配体优化 - 使用LigandMPNN
            
            # 首先转换CIF文件为PDB
            complex_cif = target_prediction.get("complex_structure")
            if not complex_cif or not os.path.exists(complex_cif):
                return {
                    "current_step": "error",
                    "errors": ["复合物结构文件不存在"]
                }
            
            pdb_prefix = os.path.join(iteration_dir, "complex")
            
            convert_result = await convert_cif_tool.ainvoke({
                "cif_file": complex_cif,
                "output_prefix": pdb_prefix
            })
            
            if "error" in convert_result:
                return {
                    "current_step": "error",
                    "errors": [f"CIF转PDB失败: {convert_result}"]
                }
            
            import json
            convert_data = json.loads(convert_result)
            if convert_data["status"] != "success":
                return {
                    "current_step": "error",
                    "errors": [f"CIF转PDB失败: {convert_data.get('message', 'Unknown error')}"]
                }
            
            pdb_file = convert_data["main_pdb"]
            
            # 运行LigandMPNN优化
            output_dir = ligandmpnn_output_dir
            
            optimization_result = await ligand_basic_tool.ainvoke({
                "pdb_file": pdb_file,
                "output_dir": output_dir,
                "design_chain": "B",  # 假设配体在B链
                "parse_chains": "A,B"  # 受体在A链，配体在B链
            })
            
            if "error" in optimization_result:
                return {
                    "current_step": "error",
                    "errors": [f"LigandMPNN优化失败: {optimization_result}"]
                }
            
            optimization_data = json.loads(optimization_result)
            if optimization_data["status"] != "success":
                return {
                    "current_step": "error",
                    "errors": [f"LigandMPNN优化失败: {optimization_data.get('message', 'Unknown error')}"]
                }
            
            # 提取优化后的序列（这里简化处理，实际需要解析LigandMPNN输出）
            new_sequence = state["current_sequence"]  # 暂时保持原序列
            
            optimization = OptimizationResult(
                optimized_sequence=new_sequence,
                optimization_type="ligand_binding",
                improvement_score=0.0,  # 需要从LigandMPNN结果中提取
                iteration_number=state["current_iteration"],
                parent_prediction_id=target_prediction["prediction_id"]
            )
            
            return {
                "current_step": "iteration_control",
                "completed_steps": ["optimization"],
                "optimizations": [optimization],
                "current_sequence": new_sequence,
                "current_iteration": state["current_iteration"] + 1
            }
        
    except Exception as e:
        return {
            "current_step": "error",
            "errors": [f"优化阶段出错: {str(e)}"]
        }

async def reporting_node(state: ProteinDesignState, config: RunnableConfig):
    """报告节点 - 生成迭代优化报告"""
    configuration = ProteinDesignConfiguration.from_runnable_config(config)
    
    if not configuration.generate_report:
        return {
            "current_step": "completed",
            "completed_steps": ["reporting"],
            "final_report": "报告生成已禁用"
        }
    
    try:
        # 初始化LLM
        model = init_chat_model(
            configuration.supervisor_model,
            model_kwargs=configuration.supervisor_model_kwargs or {}
        )
        
        # 处理预测结果中的路径显示
        processed_predictions = []
        work_dir = state.get("work_dir", "")
        
        for pred in state.get("predictions", []):
            processed_pred = pred.copy()
            
            # 处理受体结构路径
            if pred.get("receptor_structure"):
                full_path = pred["receptor_structure"]
                if work_dir and full_path.startswith(work_dir):
                    processed_pred["receptor_structure"] = full_path.replace(work_dir, "workspace")
                else:
                    processed_pred["receptor_structure"] = os.path.basename(full_path)
            
            # 处理配体结构路径
            if pred.get("ligand_structure"):
                full_path = pred["ligand_structure"]
                if work_dir and full_path.startswith(work_dir):
                    processed_pred["ligand_structure"] = full_path.replace(work_dir, "workspace")
                else:
                    processed_pred["ligand_structure"] = os.path.basename(full_path)
            
            # 处理复合物结构路径
            if pred.get("complex_structure"):
                full_path = pred["complex_structure"]
                if work_dir and full_path.startswith(work_dir):
                    processed_pred["complex_structure"] = full_path.replace(work_dir, "workspace")
                else:
                    processed_pred["complex_structure"] = os.path.basename(full_path)
            
            processed_predictions.append(processed_pred)
        
        # 构建报告提示
        prompt = PROTEIN_DESIGN_REPORTER_INSTRUCTIONS.format(
            predictions=processed_predictions,
            scores=state.get("scores", []),
            optimizations=state.get("optimizations", []),
            today=get_today_str()
        )
        
        # 添加迭代历史信息
        iteration_summary = f"""
迭代优化摘要：
- 设计场景: {state.get('design_scenario', 'unknown')}
- 优化目标: {state.get('optimization_target', 'unknown')}
- 总迭代次数: {state.get('current_iteration', 0)}
- 最佳分数: {state.get('best_score', 0.0)}
- 是否收敛: {state.get('has_converged', False)}

迭代历史:
{state.get('iteration_history', [])}
        """
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"请生成详细的蛋白质设计报告。{iteration_summary}")
        ]
        
        response = await model.ainvoke(messages)
        
        return {
            "current_step": "completed",
            "completed_steps": ["reporting"],
            "final_report": response.content
        }
        
    except Exception as e:
        return {
            "current_step": "error",
            "errors": [f"报告阶段出错: {str(e)}"]
        }

async def error_handler_node(state: ProteinDesignState, config: RunnableConfig):
    """错误处理节点"""
    configuration = ProteinDesignConfiguration.from_runnable_config(config)
    
    # 初始化LLM
    model = init_chat_model(
        configuration.supervisor_model,
        model_kwargs=configuration.supervisor_model_kwargs or {}
    )
    
    # 构建错误处理提示
    prompt = PROTEIN_DESIGN_ERROR_HANDLER_INSTRUCTIONS.format(
        today=get_today_str()
    )
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"遇到以下错误，请提供解决方案：\n{state.get('errors', [])}")
    ]
    
    try:
        response = await model.ainvoke(messages)
        
        return {
            "final_report": f"工作流出现错误，错误处理建议：\n{response.content}"
        }
        
    except Exception as e:
        return {
            "final_report": f"工作流出现错误：{state.get('errors', [])}\n错误处理也失败了：{str(e)}"
        }

# 条件路由函数

def should_continue(state: ProteinDesignState) -> Literal["iteration_control", "prediction", "scoring", "optimization", "reporting", "error", "end"]:
    """决定下一步执行什么节点"""
    current_step = state.get("current_step", "input_analysis")
    
    if current_step == "error":
        return "error"
    elif current_step == "iteration_control":
        return "iteration_control"
    elif current_step == "prediction":
        return "prediction"
    elif current_step == "scoring":
        return "scoring"
    elif current_step == "optimization":
        return "optimization"
    elif current_step == "reporting":
        return "reporting"
    elif current_step == "completed":
        return "end"
    else:
        return "iteration_control"

# 构建工作流图

def create_protein_design_graph():
    """创建蛋白质设计工作流图"""
    
    # 创建状态图
    workflow = StateGraph(ProteinDesignState, input=ProteinDesignInput, output=ProteinDesignOutput)
    
    # 添加节点
    workflow.add_node("input_analysis", input_analysis_node)
    workflow.add_node("iteration_control", iteration_control_node)
    workflow.add_node("prediction", prediction_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("optimization", optimization_node)
    workflow.add_node("reporting", reporting_node)
    workflow.add_node("error", error_handler_node)
    
    # 添加边
    workflow.add_edge(START, "input_analysis")
    workflow.add_conditional_edges(
        "input_analysis",
        should_continue,
        {
            "iteration_control": "iteration_control",
            "error": "error",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "iteration_control",
        should_continue,
        {
            "prediction": "prediction",
            "reporting": "reporting",
            "error": "error",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "prediction",
        should_continue,
        {
            "scoring": "scoring",
            "error": "error",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "scoring",
        should_continue,
        {
            "optimization": "optimization",
            "error": "error",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "optimization",
        should_continue,
        {
            "iteration_control": "iteration_control",
            "reporting": "reporting",
            "error": "error",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "reporting",
        should_continue,
        {
            "end": END,
            "error": "error"
        }
    )
    workflow.add_edge("error", END)
    
    return workflow.compile()

# 主要的工作流实例
protein_design_graph = create_protein_design_graph()