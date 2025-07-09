#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import subprocess
from mcp.server.fastmcp import FastMCP

# 初始化MCP服务器
mcp = FastMCP("chaifold_prediction")

@mcp.tool()
async def run_chaifold(
    fasta_file: str,
    output_folder: str
) -> str:
    """
    运行ChAI-fold结构预测
    
    简单调用chai-lab fold命令进行结构预测
    
    Args:
        fasta_file: 输入FASTA文件路径
        output_folder: 输出文件夹路径
        
    Returns:
        str - 执行结果（JSON格式）
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(fasta_file):
            return json.dumps({
                "status": "error",
                "message": f"FASTA文件不存在: {fasta_file}"
            }, indent=2)
        
        # 确保输出目录存在 - 使用异步方式避免阻塞
        import asyncio
        await asyncio.to_thread(os.makedirs, os.path.dirname(output_folder), exist_ok=True)
        
        # 构建命令
        command = f"chai-lab fold {fasta_file} {output_folder}"
        
        # 在pixi环境中执行命令
        env = os.environ.copy()
        env['PATH'] = '/root/agent_project/open_deep_research/.pixi/envs/default/bin:' + env.get('PATH', '')
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd='/root/agent_project/open_deep_research',
            env=env
        )
        
        if result.returncode == 0:
            return json.dumps({
                "status": "success",
                "message": "ChAI-fold预测完成",
                "command": command,
                "output_folder": output_folder,
                "stdout": result.stdout,
                "stderr": result.stderr
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "ChAI-fold预测失败",
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"执行错误: {str(e)}"
        }, indent=2)

@mcp.tool()
async def check_output_files(
    output_folder: str
) -> str:
    """
    检查输出文件夹中的预测结果
    
    Args:
        output_folder: 输出文件夹路径
        
    Returns:
        str - 文件列表（JSON格式）
    """
    try:
        if not os.path.exists(output_folder):
            return json.dumps({
                "status": "error", 
                "message": f"输出文件夹不存在: {output_folder}"
            }, indent=2)
        
        files = os.listdir(output_folder)
        cif_files = [f for f in files if f.endswith('.cif')]
        npz_files = [f for f in files if f.endswith('.npz')]
        
        return json.dumps({
            "status": "success",
            "output_folder": output_folder,
            "all_files": files,
            "cif_files": cif_files,
            "npz_files": npz_files,
            "file_count": len(files)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"检查文件错误: {str(e)}"
        }, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")