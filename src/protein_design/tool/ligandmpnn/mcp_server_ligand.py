#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import subprocess
from typing import Dict, Any, List, Optional, Union, Literal
from enum import Enum
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# 初始化MCP服务器
mcp = FastMCP("ligandmpnn_ligand_design")

class LigandDesignComplexity(str, Enum):
    """配体结合蛋白质设计的复杂度等级"""
    BASIC = "basic"                    # 基础配体设计：保守，高质量
    INTERMEDIATE = "intermediate"       # 中等复杂度：平衡探索与稳定性
    ADVANCED = "advanced"              # 高级探索：最大多样性，全面搜索

class ModelType(str, Enum):
    """LigandMPNN模型类型"""
    LIGAND_MPNN = "ligand_mpnn"        # 含配体的蛋白质设计（推荐）
    PROTEIN_MPNN = "protein_mpnn"      # 通用蛋白质设计

# 专门针对配体设计的预设配置
LIGAND_DESIGN_PRESETS = {
    LigandDesignComplexity.BASIC: {
        "model_type": ModelType.LIGAND_MPNN,
        "temperature": 0.1,
        "number_of_batches": 20,
        "seed": 42,
        "omit_AA": "CX",
        "use_side_chain_context": True,
        "pack_side_chains": True,
        "number_of_packs_per_design": 2,
        "description": "基础配体设计：保守策略，确保配体结合稳定性，适合初步探索"
    },
    LigandDesignComplexity.INTERMEDIATE: {
        "model_type": ModelType.LIGAND_MPNN,
        "temperature": 0.2,
        "number_of_batches": 50,
        "seed": 111,
        "omit_AA": "CX",
        "use_side_chain_context": True,
        "pack_side_chains": True,
        "number_of_packs_per_design": 3,
        "description": "中级配体设计：平衡探索与稳定性，增加序列多样性同时保持结合能力"
    },
    LigandDesignComplexity.ADVANCED: {
        "model_type": ModelType.LIGAND_MPNN,
        "temperature": 0.3,
        "number_of_batches": 100,
        "seed": None,  # 随机种子，最大多样性
        "omit_AA": "X",  # 只排除非标准氨基酸
        "use_side_chain_context": True,
        "pack_side_chains": True,
        "number_of_packs_per_design": 5,
        "description": "高级配体设计：最大多样性探索，深度挖掘序列空间，用于创新性设计"
    }
}

def run_ligandmpnn_docker(
    pdb_file: str,
    output_dir: str,
    model_type: str = "ligand_mpnn",
    design_chain: str = "B",
    temperature: float = 0.1,
    number_of_batches: int = 20,
    seed: Optional[int] = 42,
    omit_AA: str = "CX",
    parse_chains: str = "",
    use_side_chain_context: bool = True,
    pack_side_chains: bool = True,
    number_of_packs_per_design: int = 3
) -> Dict[str, Any]:
    """
    使用Docker运行LigandMPNN
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取PDB文件名（无扩展名）
    pdb_name = os.path.splitext(os.path.basename(pdb_file))[0]
    
    # 构建Docker命令
    docker_cmd = [
        "docker", "run", "--rm", "-it", "--gpus", "all", "--dns", "8.8.8.8",
        "-v", f"{os.path.dirname(pdb_file)}:/opt/input",
        "-v", f"{output_dir}:/opt/output",
        "registry.dp.tech/dptech/prod-15874/ligandmpnn:1.4",
        "python", "/root/LigandMPNN/run.py"
    ]
    
    # 添加基本参数
    docker_cmd.extend([
        "--model_type", model_type,
        "--checkpoint_ligand_mpnn", "/root/LigandMPNN/model_params/ligandmpnn_v_32_005_25.pt",
        "--pdb_path", f"/opt/input/{os.path.basename(pdb_file)}",
        "--out_folder", f"/opt/output/{pdb_name}",
        "--number_of_batches", str(number_of_batches),
        "--temperature", str(temperature),
        "--chains_to_design", design_chain,
        "--omit_AA", omit_AA
    ])
    
    # 添加可选参数
    if seed is not None:
        docker_cmd.extend(["--seed", str(seed)])
    
    if parse_chains:
        docker_cmd.extend(["--parse_these_chains_only", parse_chains])
    
    if use_side_chain_context:
        docker_cmd.extend(["--ligand_mpnn_use_side_chain_context", "1"])
    
    if pack_side_chains:
        docker_cmd.extend([
            "--pack_side_chains", "1",
            "--checkpoint_path_sc", "/root/LigandMPNN/model_params/ligandmpnn_sc_v_32_002_16.pt",
            "--number_of_packs_per_design", str(number_of_packs_per_design)
        ])
    
    try:
        # 执行Docker命令
        result = subprocess.run(
            docker_cmd, 
            capture_output=True, 
            text=True, 
            timeout=3600  # 1小时超时
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": " ".join(docker_cmd),
            "output_path": f"{output_dir}/{pdb_name}"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "任务超时（超过1小时）",
            "command": " ".join(docker_cmd)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"执行错误: {str(e)}",
            "command": " ".join(docker_cmd)
        }

@mcp.tool()
async def ligand_design_basic(
    pdb_file: str,
    output_dir: str,
    design_chain: str = "B",
    parse_chains: str = "A,B,C"
) -> str:
    """
    基础配体结合蛋白质设计
    
    ## 适用场景：
    - 初次设计含配体的蛋白质复合物
    - 需要高稳定性和可靠结合能力
    - 保守的序列优化策略
    
    ## 设计策略：
    - 低温度采样(0.1)确保高质量序列
    - 中等数量序列(20)平衡质量与数量
    - 启用侧链上下文建模，精确预测配体-蛋白质相互作用
    - 包含侧链预测，提供完整的原子级结构
    
    ## 使用示例：
    ```
    # 设计配体结合蛋白的B链
    ligand_design_basic(
        pdb_file="/path/to/complex.pdb",
        output_dir="/path/to/output", 
        design_chain="B"
    )
    ```
    
    Args:
        pdb_file: str - 输入的蛋白质-配体复合物PDB文件路径
        output_dir: str - 结果保存目录
        design_chain: str - 需要设计的蛋白质链（默认"B"）
        parse_chains: str - 解析的所有链（默认"A,B,C"，包含配体）
        
    Returns:
        str - 设计任务执行结果（JSON格式）
    """
    try:
        if not os.path.exists(pdb_file):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file}"
            }, indent=2)
        
        config = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.BASIC]
        
        result = run_ligandmpnn_docker(
            pdb_file=pdb_file,
            output_dir=output_dir,
            model_type=config["model_type"].value,
            design_chain=design_chain,
            temperature=config["temperature"],
            number_of_batches=config["number_of_batches"],
            seed=config["seed"],
            omit_AA=config["omit_AA"],
            parse_chains=parse_chains,
            use_side_chain_context=config["use_side_chain_context"],
            pack_side_chains=config["pack_side_chains"],
            number_of_packs_per_design=config["number_of_packs_per_design"]
        )
        
        return json.dumps({
            "status": "success",
            "design_level": "basic",
            "description": config["description"],
            "parameters": {
                "pdb_file": pdb_file,
                "output_dir": output_dir,
                "design_chain": design_chain,
                "parse_chains": parse_chains,
                "temperature": config["temperature"],
                "number_of_batches": config["number_of_batches"],
                "model_type": config["model_type"].value
            },
            "execution_result": result
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"基础设计执行错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def ligand_design_intermediate(
    pdb_file: str,
    output_dir: str,
    design_chain: str = "B",
    parse_chains: str = "A,B,C",
    custom_temperature: Optional[float] = None
) -> str:
    """
    中级配体结合蛋白质设计
    
    ## 适用场景：
    - 需要在稳定性和多样性间找到平衡
    - 已有初步结果，希望扩展序列选择范围
    - 进行序列优化和改进
    
    ## 设计策略：
    - 中等温度采样(0.2)平衡质量与多样性
    - 更多序列数量(50)提供充足选择
    - 完整的侧链建模和配体上下文分析
    - 增加每个设计的侧链预测数量
    
    ## 使用示例：
    ```
    # 中级多样性设计
    ligand_design_intermediate(
        pdb_file="/path/to/complex.pdb",
        output_dir="/path/to/output",
        design_chain="B",
        custom_temperature=0.25  # 可自定义温度
    )
    ```
    
    Args:
        pdb_file: str - 输入的蛋白质-配体复合物PDB文件路径
        output_dir: str - 结果保存目录
        design_chain: str - 需要设计的蛋白质链
        parse_chains: str - 解析的所有链
        custom_temperature: Optional[float] - 自定义采样温度(0.1-0.4)
        
    Returns:
        str - 设计任务执行结果（JSON格式）
    """
    try:
        if not os.path.exists(pdb_file):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file}"
            }, indent=2)
        
        config = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.INTERMEDIATE]
        
        # 允许自定义温度
        temperature = custom_temperature if custom_temperature is not None else config["temperature"]
        if not (0.05 <= temperature <= 0.5):
            return json.dumps({
                "status": "error",
                "message": "自定义温度必须在0.05-0.5之间"
            }, indent=2)
        
        result = run_ligandmpnn_docker(
            pdb_file=pdb_file,
            output_dir=output_dir,
            model_type=config["model_type"].value,
            design_chain=design_chain,
            temperature=temperature,
            number_of_batches=config["number_of_batches"],
            seed=config["seed"],
            omit_AA=config["omit_AA"],
            parse_chains=parse_chains,
            use_side_chain_context=config["use_side_chain_context"],
            pack_side_chains=config["pack_side_chains"],
            number_of_packs_per_design=config["number_of_packs_per_design"]
        )
        
        return json.dumps({
            "status": "success",
            "design_level": "intermediate",
            "description": config["description"],
            "parameters": {
                "pdb_file": pdb_file,
                "output_dir": output_dir,
                "design_chain": design_chain,
                "parse_chains": parse_chains,
                "temperature": temperature,
                "number_of_batches": config["number_of_batches"],
                "model_type": config["model_type"].value,
                "custom_temperature_used": custom_temperature is not None
            },
            "execution_result": result
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"中级设计执行错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def ligand_design_advanced(
    pdb_file: str,
    output_dir: str,
    design_chain: str = "B",
    parse_chains: str = "A,B,C",
    max_batches: Optional[int] = None,
    include_rare_aa: bool = False
) -> str:
    """
    高级配体结合蛋白质设计
    
    ## 适用场景：
    - 需要最大序列多样性和创新性设计
    - 深度探索配体结合位点的序列空间
    - 研究级别的全面序列优化
    
    ## 设计策略：
    - 高温度采样(0.3)最大化序列多样性
    - 大量序列生成(100)进行全面搜索
    - 随机种子确保每次运行的独特性
    - 完整的侧链建模和多个构象预测
    - 可选择包含稀有氨基酸进行创新设计
    
    ## 使用示例：
    ```
    # 高级全面设计
    ligand_design_advanced(
        pdb_file="/path/to/complex.pdb",
        output_dir="/path/to/output",
        design_chain="A,B",  # 多链设计
        max_batches=150,     # 增加序列数量
        include_rare_aa=True # 包含稀有氨基酸
    )
    ```
    
    Args:
        pdb_file: str - 输入的蛋白质-配体复合物PDB文件路径
        output_dir: str - 结果保存目录
        design_chain: str - 需要设计的蛋白质链（可多链，如"A,B"）
        parse_chains: str - 解析的所有链
        max_batches: Optional[int] - 最大序列批次数（默认100，可增至200）
        include_rare_aa: bool - 是否包含稀有氨基酸（默认False）
        
    Returns:
        str - 设计任务执行结果（JSON格式）
    """
    try:
        if not os.path.exists(pdb_file):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file}"
            }, indent=2)
        
        config = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.ADVANCED]
        
        # 允许自定义批次数
        batches = max_batches if max_batches is not None else config["number_of_batches"]
        if batches > 200:
            return json.dumps({
                "status": "error",
                "message": "最大批次数不能超过200"
            }, indent=2)
        
        # 根据稀有氨基酸设置调整omit_AA
        omit_aa = "X" if include_rare_aa else config["omit_AA"]
        
        result = run_ligandmpnn_docker(
            pdb_file=pdb_file,
            output_dir=output_dir,
            model_type=config["model_type"].value,
            design_chain=design_chain,
            temperature=config["temperature"],
            number_of_batches=batches,
            seed=config["seed"],  # None for random
            omit_AA=omit_aa,
            parse_chains=parse_chains,
            use_side_chain_context=config["use_side_chain_context"],
            pack_side_chains=config["pack_side_chains"],
            number_of_packs_per_design=config["number_of_packs_per_design"]
        )
        
        return json.dumps({
            "status": "success",
            "design_level": "advanced",
            "description": config["description"],
            "parameters": {
                "pdb_file": pdb_file,
                "output_dir": output_dir,
                "design_chain": design_chain,
                "parse_chains": parse_chains,
                "temperature": config["temperature"],
                "number_of_batches": batches,
                "model_type": config["model_type"].value,
                "include_rare_aa": include_rare_aa,
                "random_seed": True
            },
            "execution_result": result
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"高级设计执行错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def get_ligand_design_presets() -> str:
    """
    获取所有配体设计预设的详细信息
    
    Returns:
        str - 预设配置详细信息（JSON格式）
    """
    preset_info = {}
    
    for level, config in LIGAND_DESIGN_PRESETS.items():
        preset_info[level.value] = {
            "description": config["description"],
            "parameters": {
                "model_type": config["model_type"].value,
                "temperature": config["temperature"],
                "number_of_batches": config["number_of_batches"],
                "use_side_chain_context": config["use_side_chain_context"],
                "pack_side_chains": config["pack_side_chains"],
                "number_of_packs_per_design": config["number_of_packs_per_design"],
                "omit_AA": config["omit_AA"]
            }
        }
    
    # 添加使用场景和建议
    preset_info["basic"]["use_cases"] = [
        "初次配体结合蛋白设计",
        "需要高稳定性保证",
        "保守的序列优化"
    ]
    preset_info["basic"]["recommendations"] = [
        "适合新手用户",
        "结果可靠性高",
        "计算资源需求适中"
    ]
    
    preset_info["intermediate"]["use_cases"] = [
        "平衡质量与多样性",
        "序列优化和改进",
        "扩展设计选择范围"
    ]
    preset_info["intermediate"]["recommendations"] = [
        "经验用户首选",
        "性能与效果平衡",
        "可自定义温度参数"
    ]
    
    preset_info["advanced"]["use_cases"] = [
        "最大序列多样性探索",
        "创新性设计研究",
        "深度序列空间挖掘"
    ]
    preset_info["advanced"]["recommendations"] = [
        "专家级用户使用",
        "需要充足计算资源",
        "结果需要专业筛选"
    ]
    
    return json.dumps({
        "ligand_design_presets": preset_info,
        "design_guidelines": {
            "basic": "保守策略，高稳定性，适合初学者",
            "intermediate": "平衡策略，质量与多样性并重，推荐使用",
            "advanced": "探索策略，最大多样性，专家使用"
        },
        "parameter_explanations": {
            "temperature": {
                "0.1": "低温：保守设计，高质量序列",
                "0.2": "中温：平衡质量与多样性",
                "0.3": "高温：最大多样性探索"
            },
            "number_of_batches": {
                "20": "基础：适中数量，快速结果",
                "50": "中级：充足选择，平衡性能",
                "100+": "高级：大量候选，全面搜索"
            }
        }
    }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")