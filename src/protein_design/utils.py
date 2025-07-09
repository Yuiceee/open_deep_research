"""
蛋白质设计工具辅助函数
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from protein_design.state import ProteinDesignInput

def create_single_sequence_input(
    sequence: str,
    work_dir: Optional[str] = None,
    optimization_target: str = "enzyme_activity",
    max_iterations: int = 3,
    convergence_threshold: float = 0.01
) -> ProteinDesignInput:
    """
    创建单序列优化输入
    
    Args:
        sequence: 蛋白质序列
        work_dir: 工作目录
        optimization_target: 优化目标
        max_iterations: 最大迭代次数
        convergence_threshold: 收敛阈值
    
    Returns:
        ProteinDesignInput: 输入配置
    """
    return ProteinDesignInput(
        single_sequence=sequence,
        receptor_sequence=None,
        ligand_sequence=None,
        work_dir=work_dir,
        optimization_target=optimization_target,
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold
    )

def create_ligand_optimization_input(
    receptor_sequence: str,
    ligand_sequence: str,
    work_dir: Optional[str] = None,
    optimization_target: str = "binding_affinity",
    max_iterations: int = 5,
    convergence_threshold: float = 0.01
) -> ProteinDesignInput:
    """
    创建配体优化输入
    
    Args:
        receptor_sequence: 受体序列
        ligand_sequence: 配体序列
        work_dir: 工作目录
        optimization_target: 优化目标
        max_iterations: 最大迭代次数
        convergence_threshold: 收敛阈值
    
    Returns:
        ProteinDesignInput: 输入配置
    """
    return ProteinDesignInput(
        single_sequence=None,
        receptor_sequence=receptor_sequence,
        ligand_sequence=ligand_sequence,
        work_dir=work_dir,
        optimization_target=optimization_target,
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold
    )

def validate_protein_sequence(sequence: str) -> bool:
    """
    验证蛋白质序列的有效性
    
    Args:
        sequence: 蛋白质序列
        
    Returns:
        bool: 是否有效
    """
    if not sequence:
        return False
    
    # 标准氨基酸单字母代码
    valid_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")
    
    # 检查序列是否只包含有效的氨基酸
    return all(aa.upper() in valid_amino_acids for aa in sequence)

def format_iteration_results(iteration_history: List[Dict[str, Any]]) -> str:
    """
    格式化迭代结果为可读的字符串
    
    Args:
        iteration_history: 迭代历史记录
        
    Returns:
        str: 格式化的结果
    """
    if not iteration_history:
        return "无迭代历史记录"
    
    result = "迭代优化历史:\n"
    result += "=" * 50 + "\n"
    
    for record in iteration_history:
        iteration = record.get("iteration", 0)
        score = record.get("score", 0.0)
        improvement = record.get("improvement", 0.0)
        sequence = record.get("sequence", "")
        
        result += f"迭代 {iteration}:\n"
        result += f"  分数: {score:.4f}\n"
        result += f"  改进: {improvement:+.4f}\n"
        result += f"  序列: {sequence[:50]}{'...' if len(sequence) > 50 else ''}\n"
        result += "-" * 30 + "\n"
    
    return result

async def save_results_to_file(results: Dict[str, Any], filepath: str) -> None:
    """
    保存结果到文件
    
    Args:
        results: 结果字典
        filepath: 文件路径
    """
    import asyncio
    
    # 使用异步方式创建目录，避免阻塞调用
    await asyncio.to_thread(os.makedirs, os.path.dirname(filepath), exist_ok=True)
    
    # 使用异步方式写入文件
    def _write_file():
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    await asyncio.to_thread(_write_file)

def load_results_from_file(filepath: str) -> Dict[str, Any]:
    """
    从文件加载结果
    
    Args:
        filepath: 文件路径
        
    Returns:
        Dict[str, Any]: 结果字典
    """
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_example_sequences() -> Dict[str, str]:
    """
    获取示例序列
    
    Returns:
        Dict[str, str]: 示例序列字典
    """
    return {
        "short_enzyme": "MKLLNVTLVVDSGNGTGKTTFVKRLTGVGQFGNVGIFLDVGGQKSTVAMVRRLTVGGSAVGCGKS",
        "receptor_example": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQF",
        "ligand_example": "ACDKKRCPKDCCGFGYCNNGFKCRCTSGFCGGGCDCQCRF",
        "long_enzyme": "MKLLNVTLVVDSGNGTGKTTFVKRLTGVGQFGNVGIFLDVGGQKSTVAMVRRLTVGGSAVGCGKSVREAREAKNKMDVILKYPEGRKFRVVLVDDQVGHGDVEIKKPLVEVDRSEVDLKLQKDVKKGKKMKDVLLGFKGQHGQGTMAGLMAVGFQPQFQGKFGQVPPTVAVGQGKAQVDIQDIGLQEQKFGKVLVGDTGQGQGTMAGLMAVGFQPQFQGKFGQVPPTVAVGQGKAQVDIQDIGLQEQKFGKVLVGDTGQGQGTMAGLMAVGFQPQFQGKFGQVPPTVAVGQGKAQVDIQDIGLQEQKFGKVLVGDTGQGQGTMAGLMAVGFQPQFQGKFGQVPPTVAVGQGKAQVDIQDIGLQEQKFGKVLVGDTGQGQGTMAGLMAVGFQPQFQGKFGQVPPTVAVGQGKAQVDIQDIGLQEQKFGKVLVGDTG"
    }

# ===== 工作目录管理工具函数 =====

def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    # 从当前文件位置向上查找项目根目录
    current_file = Path(__file__).resolve()
    # 向上查找包含 pyproject.toml 的目录
    for parent in current_file.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # 如果没有找到，返回当前文件的三级父目录
    return current_file.parents[2]

def get_workspace_root() -> Path:
    """
    获取工作空间根目录
    
    Returns:
        Path: 工作空间根目录路径
    """
    project_root = get_project_root()
    workspace_root = project_root / "workspace"
    workspace_root.mkdir(exist_ok=True)
    return workspace_root

def create_session_directory(session_id: Optional[str] = None) -> str:
    """
    创建新的会话目录
    
    Args:
        session_id: 可选的会话ID，如果不提供则自动生成
    
    Returns:
        str: 会话目录的完整路径
    """
    if session_id is None:
        session_id = f"session_{datetime.now().strftime('%H%M%S')}"
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_dir_name = f"{timestamp}_protein_design_{session_id}"
    
    workspace_root = get_workspace_root()
    session_dir = workspace_root / session_dir_name
    session_dir.mkdir(exist_ok=True)
    
    return str(session_dir)

def create_iteration_directory(session_dir: str, iteration: int) -> str:
    """
    创建迭代目录及其子目录
    
    Args:
        session_dir: 会话目录路径
        iteration: 迭代次数
    
    Returns:
        str: 迭代目录的完整路径
    """
    session_path = Path(session_dir)
    iteration_dir = session_path / f"iteration_{iteration}"
    
    # 创建迭代目录和子目录
    iteration_dir.mkdir(exist_ok=True)
    (iteration_dir / "input_files").mkdir(exist_ok=True)
    (iteration_dir / "chaifold_output").mkdir(exist_ok=True)
    (iteration_dir / "ligandmpnn_output").mkdir(exist_ok=True)
    (iteration_dir / "scoring_results").mkdir(exist_ok=True)
    
    return str(iteration_dir)

def get_tool_output_dir(iteration_dir: str, tool_name: str) -> str:
    """
    获取工具输出目录
    
    Args:
        iteration_dir: 迭代目录路径
        tool_name: 工具名称 ('chaifold', 'ligandmpnn', 'scoring')
    
    Returns:
        str: 工具输出目录的完整路径
    """
    iteration_path = Path(iteration_dir)
    tool_output_dir = iteration_path / f"{tool_name}_output"
    tool_output_dir.mkdir(exist_ok=True)
    return str(tool_output_dir)

def get_input_files_dir(iteration_dir: str) -> str:
    """
    获取输入文件目录
    
    Args:
        iteration_dir: 迭代目录路径
    
    Returns:
        str: 输入文件目录的完整路径
    """
    iteration_path = Path(iteration_dir)
    input_files_dir = iteration_path / "input_files"
    input_files_dir.mkdir(exist_ok=True)
    return str(input_files_dir)

async def create_directories_async(session_dir: str, iteration: int) -> Dict[str, str]:
    """
    异步创建目录结构
    
    Args:
        session_dir: 会话目录路径
        iteration: 迭代次数
    
    Returns:
        Dict[str, str]: 包含各种目录路径的字典
    """
    import asyncio
    
    # 异步创建目录
    def _create_dirs():
        iteration_dir = create_iteration_directory(session_dir, iteration)
        return {
            "session_dir": session_dir,
            "iteration_dir": iteration_dir,
            "input_files_dir": get_input_files_dir(iteration_dir),
            "chaifold_output_dir": get_tool_output_dir(iteration_dir, "chaifold"),
            "ligandmpnn_output_dir": get_tool_output_dir(iteration_dir, "ligandmpnn"),
            "scoring_results_dir": get_tool_output_dir(iteration_dir, "scoring")
        }
    
    return await asyncio.to_thread(_create_dirs)

def cleanup_old_sessions(keep_days: int = 7) -> None:
    """
    清理旧的会话目录
    
    Args:
        keep_days: 保留天数，默认7天
    """
    import shutil
    from datetime import timedelta
    
    workspace_root = get_workspace_root()
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    for session_dir in workspace_root.iterdir():
        if session_dir.is_dir() and session_dir.name.startswith("20"):
            try:
                # 从目录名解析日期
                date_str = session_dir.name.split("_")[0]
                session_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if session_date < cutoff_date:
                    shutil.rmtree(session_dir)
                    print(f"已删除旧会话目录: {session_dir}")
            except (ValueError, IndexError):
                # 如果解析失败，跳过
                continue

def get_session_info(session_dir: str) -> Dict[str, Any]:
    """
    获取会话信息
    
    Args:
        session_dir: 会话目录路径
    
    Returns:
        Dict[str, Any]: 会话信息
    """
    session_path = Path(session_dir)
    
    # 统计迭代次数
    iteration_dirs = [d for d in session_path.iterdir() if d.is_dir() and d.name.startswith("iteration_")]
    iteration_count = len(iteration_dirs)
    
    # 统计文件数量
    total_files = sum(1 for _ in session_path.rglob("*") if _.is_file())
    
    # 计算目录大小
    total_size = sum(f.stat().st_size for f in session_path.rglob("*") if f.is_file())
    
    return {
        "session_dir": str(session_path),
        "session_name": session_path.name,
        "iteration_count": iteration_count,
        "total_files": total_files,
        "total_size_mb": total_size / (1024 * 1024),
        "created_time": session_path.stat().st_ctime
    }