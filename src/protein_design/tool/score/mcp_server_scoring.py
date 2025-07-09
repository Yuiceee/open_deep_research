#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from Bio.PDB import MMCIFParser, PDBIO, PDBParser, is_aa
import MDAnalysis as mda
from MDAnalysis.analysis import rms
import freesasa

# 初始化MCP服务器
mcp = FastMCP("protein_scoring_analysis")

# 文件处理工具

@mcp.tool()
async def create_fasta_from_sequences(
    sequences: List[str],
    output_file: str,
    sequence_names: Optional[List[str]] = None
) -> str:
    """
    从序列列表创建FASTA文件
    
    Args:
        sequences: 蛋白质序列列表
        output_file: 输出FASTA文件路径
        sequence_names: 序列名称列表（可选）
        
    Returns:
        str - 操作结果（JSON格式）
    """
    try:
        # 确保输出目录存在
        # 使用异步方式创建目录，避免阻塞调用
        import asyncio
        await asyncio.to_thread(os.makedirs, os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as f:
            for i, seq in enumerate(sequences):
                # 使用提供的名称或默认名称
                if sequence_names and i < len(sequence_names):
                    seq_name = sequence_names[i]
                else:
                    seq_name = f"protein|seq{i}"
                
                f.write(f">{seq_name}\n")
                f.write(f"{seq}\n")
        
        return json.dumps({
            "status": "success",
            "message": "FASTA文件创建成功",
            "output_file": output_file,
            "sequence_count": len(sequences)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"创建FASTA文件错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def read_sequences_from_fasta(
    fasta_file: str
) -> str:
    """
    从FASTA文件读取序列
    
    Args:
        fasta_file: FASTA文件路径
        
    Returns:
        str - 读取的序列信息（JSON格式）
    """
    try:
        if not os.path.exists(fasta_file):
            return json.dumps({
                "status": "error",
                "message": f"FASTA文件不存在: {fasta_file}"
            }, indent=2)
        
        sequences = []
        current_seq = ""
        current_name = ""
        
        with open(fasta_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    # 保存上一个序列
                    if current_name and current_seq:
                        sequences.append({
                            "name": current_name,
                            "sequence": current_seq
                        })
                    # 开始新序列
                    current_name = line[1:]  # 移除 >
                    current_seq = ""
                else:
                    current_seq += line
            
            # 保存最后一个序列
            if current_name and current_seq:
                sequences.append({
                    "name": current_name,
                    "sequence": current_seq
                })
        
        return json.dumps({
            "status": "success",
            "fasta_file": fasta_file,
            "sequence_count": len(sequences),
            "sequences": sequences
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"读取FASTA文件错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def read_sequences_from_pdb(
    pdb_file: str
) -> str:
    """
    从PDB文件读取序列
    
    Args:
        pdb_file: PDB文件路径
        
    Returns:
        str - 读取的序列信息（JSON格式）
    """
    try:
        if not os.path.exists(pdb_file):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file}"
            }, indent=2)
        
        # 定义三字母到单字母的映射
        aa_dict = {
            'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F',
            'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L',
            'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R',
            'SER': 'S', 'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y'
        }
        
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('Protein', pdb_file)
        
        chains = []
        for model in structure:
            for chain in model:
                chain_id = chain.get_id()
                seq = ''
                for residue in chain:
                    if is_aa(residue):
                        res_name = residue.get_resname()
                        seq += aa_dict.get(res_name, 'X')
                
                if seq:  # 只添加非空序列
                    chains.append({
                        "chain_id": chain_id,
                        "sequence": seq,
                        "length": len(seq)
                    })
        
        return json.dumps({
            "status": "success",
            "pdb_file": pdb_file,
            "chain_count": len(chains),
            "chains": chains
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"读取PDB文件错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def convert_cif_to_pdb(
    cif_file: str,
    output_prefix: str
) -> str:
    """
    将CIF文件转换为PDB格式
    
    Args:
        cif_file: 输入CIF文件路径
        output_prefix: 输出文件前缀
        
    Returns:
        str - 转换结果（JSON格式）
    """
    try:
        if not os.path.exists(cif_file):
            return json.dumps({
                "status": "error",
                "message": f"CIF文件不存在: {cif_file}"
            }, indent=2)
        
        # 读取CIF文件
        parser = MMCIFParser(QUIET=True)
        structure = parser.get_structure('Complex', cif_file)
        
        # 保存整个复合物到PDB文件
        io = PDBIO()
        io.set_structure(structure)
        main_pdb = f'{output_prefix}.pdb'
        io.save(main_pdb)
        
        output_files = [main_pdb]
        
        # 分离不同链为单独文件
        u = mda.Universe(main_pdb)
        chain_ids = []
        for atom in u.atoms:
            if atom.chainID not in chain_ids:
                chain_ids.append(atom.chainID)
        
        chain_files = {}
        if len(chain_ids) > 1:
            for i, chain_id in enumerate(chain_ids):
                selection = u.select_atoms(f'chainID {chain_id}')
                chain_file = f'{output_prefix}_chain_{chain_id}.pdb'
                with mda.Writer(chain_file) as writer:
                    writer.write(selection)
                output_files.append(chain_file)
                chain_files[chain_id] = chain_file
        
        return json.dumps({
            "status": "success",
            "message": "CIF转PDB转换完成",
            "cif_file": cif_file,
            "main_pdb": main_pdb,
            "chain_files": chain_files,
            "all_output_files": output_files,
            "chain_count": len(chain_ids)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"CIF转PDB错误: {str(e)}"
        }, indent=2)

# 评分分析工具

@mcp.tool()
async def extract_model_scores(
    npz_file: str
) -> str:
    """
    从NPZ文件提取模型评分
    
    Args:
        npz_file: NPZ评分文件路径
        
    Returns:
        str - 评分信息（JSON格式）
    """
    try:
        if not os.path.exists(npz_file):
            return json.dumps({
                "status": "error",
                "message": f"NPZ文件不存在: {npz_file}"
            }, indent=2)
        
        data = np.load(npz_file)
        
        scores = {}
        for key in data.files:
            value = data[key]
            # 处理不同类型的数据
            if isinstance(value, np.ndarray):
                if value.size == 1:
                    scores[key] = float(value.item())
                else:
                    scores[key] = value.tolist()
            else:
                scores[key] = value
        
        return json.dumps({
            "status": "success",
            "npz_file": npz_file,
            "scores": scores,
            "available_metrics": list(scores.keys())
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"提取评分错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def analyze_prediction_quality(
    npz_file: str
) -> str:
    """
    分析预测质量
    
    Args:
        npz_file: NPZ评分文件路径
        
    Returns:
        str - 质量分析结果（JSON格式）
    """
    try:
        if not os.path.exists(npz_file):
            return json.dumps({
                "status": "error",
                "message": f"NPZ文件不存在: {npz_file}"
            }, indent=2)
        
        data = np.load(npz_file)
        
        # 提取关键评分
        ptm = float(data['ptm'][0]) if 'ptm' in data else None
        iptm = float(data['iptm'][0]) if 'iptm' in data else None
        aggregate_score = float(data['aggregate_score'][0]) if 'aggregate_score' in data else None
        
        # 质量评估
        quality_assessment = {
            "ptm": ptm,
            "iptm": iptm,
            "aggregate_score": aggregate_score
        }
        
        # 添加质量等级判断
        if aggregate_score is not None:
            if aggregate_score >= 0.8:
                quality_level = "excellent"
            elif aggregate_score >= 0.6:
                quality_level = "good"
            elif aggregate_score >= 0.4:
                quality_level = "moderate"
            else:
                quality_level = "poor"
            
            quality_assessment["quality_level"] = quality_level
        
        # 添加解释
        explanations = {
            "ptm": "预测模板建模得分，评估整体结构质量",
            "iptm": "界面预测模板建模得分，评估分子间相互作用",
            "aggregate_score": "综合评分，选择最佳模型的主要指标"
        }
        
        return json.dumps({
            "status": "success",
            "npz_file": npz_file,
            "quality_assessment": quality_assessment,
            "metric_explanations": explanations
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"质量分析错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def find_best_model(
    result_dir: str,
    model_count: int = 5
) -> str:
    """
    在多个模型中找到最佳模型
    
    Args:
        result_dir: 结果目录路径
        model_count: 模型数量
        
    Returns:
        str - 最佳模型信息（JSON格式）
    """
    try:
        if not os.path.exists(result_dir):
            return json.dumps({
                "status": "error",
                "message": f"结果目录不存在: {result_dir}"
            }, indent=2)
        
        models = []
        
        for i in range(model_count):
            npz_file = os.path.join(result_dir, f"scores.model_idx_{i}.npz")
            cif_file = os.path.join(result_dir, f"pred.model_idx_{i}.cif")
            
            if os.path.exists(npz_file) and os.path.exists(cif_file):
                try:
                    data = np.load(npz_file)
                    ptm = float(data['ptm'][0]) if 'ptm' in data else 0
                    iptm = float(data['iptm'][0]) if 'iptm' in data else 0
                    aggregate_score = float(data['aggregate_score'][0]) if 'aggregate_score' in data else 0
                    
                    models.append({
                        "model_idx": i,
                        "cif_file": cif_file,
                        "npz_file": npz_file,
                        "ptm": ptm,
                        "iptm": iptm,
                        "aggregate_score": aggregate_score
                    })
                except Exception as e:
                    continue
        
        if not models:
            return json.dumps({
                "status": "error",
                "message": "没有找到有效的模型文件"
            }, indent=2)
        
        # 按aggregate_score排序，找到最佳模型
        best_model = max(models, key=lambda x: x["aggregate_score"])
        
        return json.dumps({
            "status": "success",
            "result_dir": result_dir,
            "total_models": len(models),
            "best_model": best_model,
            "all_models": models
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"寻找最佳模型错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def calculate_rmsd(
    pdb_file1: str,
    pdb_file2: str,
    atom_selection: str = "name CA"
) -> str:
    """
    计算两个结构之间的RMSD
    
    Args:
        pdb_file1: 第一个PDB文件路径
        pdb_file2: 第二个PDB文件路径
        atom_selection: 原子选择字符串（默认CA原子）
        
    Returns:
        str - RMSD计算结果（JSON格式）
    """
    try:
        if not os.path.exists(pdb_file1):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file1}"
            }, indent=2)
        
        if not os.path.exists(pdb_file2):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file2}"
            }, indent=2)
        
        # 加载两个结构
        u1 = mda.Universe(pdb_file1)
        u2 = mda.Universe(pdb_file2)
        
        # 选择原子
        selection1 = u1.select_atoms(atom_selection)
        selection2 = u2.select_atoms(atom_selection)
        
        if len(selection1) != len(selection2):
            return json.dumps({
                "status": "error",
                "message": f"原子数量不匹配: {len(selection1)} vs {len(selection2)}"
            }, indent=2)
        
        # 计算RMSD
        rmsd_value = rms.rmsd(selection1.positions, selection2.positions, superposition=True)
        
        return json.dumps({
            "status": "success",
            "pdb_file1": pdb_file1,
            "pdb_file2": pdb_file2,
            "atom_selection": atom_selection,
            "atom_count": len(selection1),
            "rmsd": float(rmsd_value)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"RMSD计算错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def calculate_sasa(
    pdb_file: str
) -> str:
    """
    计算蛋白质的溶剂可及表面积
    
    Args:
        pdb_file: PDB文件路径
        
    Returns:
        str - SASA计算结果（JSON格式）
    """
    try:
        if not os.path.exists(pdb_file):
            return json.dumps({
                "status": "error",
                "message": f"PDB文件不存在: {pdb_file}"
            }, indent=2)
        
        # 计算SASA
        structure = freesasa.Structure(pdb_file)
        result = freesasa.calc(structure)
        area_classes = freesasa.classifyResults(result, structure)
        
        sasa_results = {
            "total_area": result.totalArea(),
            "polar_area": area_classes["Polar"],
            "apolar_area": area_classes["Apolar"],
            "main_chain_area": area_classes["MainChain"],
            "side_chain_area": area_classes["SideChain"]
        }
        
        return json.dumps({
            "status": "success",
            "pdb_file": pdb_file,
            "sasa_results": sasa_results
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"SASA计算错误: {str(e)}"
        }, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")