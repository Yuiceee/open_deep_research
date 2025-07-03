#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LigandMPNN MCP服务器测试脚本

测试MCP服务器的基本功能：
1. 服务器初始化
2. 工具注册
3. 参数验证
4. 预设配置
"""

import asyncio
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# 导入我们的MCP服务器
from mcp_server_ligand import (
    mcp, 
    LIGAND_DESIGN_PRESETS,
    LigandDesignComplexity,
    ligand_design_basic,
    ligand_design_intermediate, 
    ligand_design_advanced,
    get_ligand_design_presets
)

class TestMCPServerConstruction(unittest.TestCase):
    """测试MCP服务器构造和基本功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdb = os.path.join(self.test_dir, "test_complex.pdb")
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # 创建模拟PDB文件
        with open(self.test_pdb, 'w') as f:
            f.write("""HEADER    TEST PDB                               01-JAN-24   TEST
ATOM      1  N   ALA A   1      20.154  16.967  10.000  1.00 20.00           N
ATOM      2  CA  ALA A   1      21.618  16.967  10.000  1.00 20.00           C
HETATM    3  C1  LIG B   1      25.000  15.000  12.000  1.00 30.00           C
END
""")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_server_initialization(self):
        """测试MCP服务器初始化"""
        self.assertIsNotNone(mcp)
        self.assertEqual(mcp.name, "ligandmpnn_ligand_design")
    
    def test_preset_configurations(self):
        """测试预设配置完整性"""
        # 检查所有预设是否存在
        expected_presets = {
            LigandDesignComplexity.BASIC,
            LigandDesignComplexity.INTERMEDIATE, 
            LigandDesignComplexity.ADVANCED
        }
        self.assertEqual(set(LIGAND_DESIGN_PRESETS.keys()), expected_presets)
        
        # 检查每个预设的必需参数
        required_params = {
            "model_type", "temperature", "number_of_batches", 
            "seed", "omit_AA", "use_side_chain_context",
            "pack_side_chains", "number_of_packs_per_design", "description"
        }
        
        for preset_name, config in LIGAND_DESIGN_PRESETS.items():
            with self.subTest(preset=preset_name):
                self.assertTrue(required_params.issubset(set(config.keys())))
                self.assertIsInstance(config["temperature"], float)
                self.assertIsInstance(config["number_of_batches"], int)
                self.assertIsInstance(config["description"], str)
    
    def test_preset_progression(self):
        """测试预设配置的复杂度递增"""
        basic = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.BASIC]
        intermediate = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.INTERMEDIATE]
        advanced = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.ADVANCED]
        
        # 温度递增
        self.assertLess(basic["temperature"], intermediate["temperature"])
        self.assertLess(intermediate["temperature"], advanced["temperature"])
        
        # 批次数递增
        self.assertLess(basic["number_of_batches"], intermediate["number_of_batches"])
        self.assertLess(intermediate["number_of_batches"], advanced["number_of_batches"])
        
        # 侧链预测数递增
        self.assertLessEqual(
            basic["number_of_packs_per_design"],
            intermediate["number_of_packs_per_design"]
        )
        self.assertLessEqual(
            intermediate["number_of_packs_per_design"],
            advanced["number_of_packs_per_design"]
        )

class TestMCPTools(unittest.TestCase):
    """测试MCP工具函数"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdb = os.path.join(self.test_dir, "test_complex.pdb")
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # 创建模拟PDB文件
        with open(self.test_pdb, 'w') as f:
            f.write("HEADER TEST PDB\nATOM 1 N ALA A 1 20.0 16.0 10.0 1.0 20.0 N\nEND\n")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    async def test_get_presets_info(self):
        """测试获取预设信息工具"""
        result = await get_ligand_design_presets()
        result_data = json.loads(result)
        
        self.assertIn("ligand_design_presets", result_data)
        self.assertIn("design_guidelines", result_data)
        self.assertIn("parameter_explanations", result_data)
        
        presets = result_data["ligand_design_presets"]
        self.assertIn("basic", presets)
        self.assertIn("intermediate", presets)
        self.assertIn("advanced", presets)
        
        # 检查每个预设的信息完整性
        for preset_name, preset_info in presets.items():
            with self.subTest(preset=preset_name):
                self.assertIn("description", preset_info)
                self.assertIn("parameters", preset_info)
                self.assertIn("use_cases", preset_info)
                self.assertIn("recommendations", preset_info)
    
    @patch('mcp_server_ligand.run_ligandmpnn_docker')
    async def test_basic_design_tool(self, mock_docker):
        """测试基础设计工具"""
        # 模拟Docker执行结果
        mock_docker.return_value = {
            "status": "success",
            "stdout": "Design completed successfully",
            "stderr": "",
            "returncode": 0,
            "command": "docker run ...",
            "output_path": f"{self.output_dir}/test_complex"
        }
        
        result = await ligand_design_basic(
            pdb_file=self.test_pdb,
            output_dir=self.output_dir,
            design_chain="B"
        )
        
        result_data = json.loads(result)
        self.assertEqual(result_data["status"], "success")
        self.assertEqual(result_data["design_level"], "basic")
        self.assertIn("description", result_data)
        self.assertIn("parameters", result_data)
        self.assertIn("execution_result", result_data)
        
        # 验证Docker函数被正确调用
        mock_docker.assert_called_once()
        call_args = mock_docker.call_args[1]
        self.assertEqual(call_args["temperature"], 0.1)  # 基础设计的温度
        self.assertEqual(call_args["number_of_batches"], 20)  # 基础设计的批次数
    
    @patch('mcp_server_ligand.run_ligandmpnn_docker')
    async def test_intermediate_design_tool(self, mock_docker):
        """测试中级设计工具"""
        mock_docker.return_value = {
            "status": "success",
            "stdout": "Design completed",
            "stderr": "",
            "returncode": 0,
            "command": "docker run ...",
            "output_path": f"{self.output_dir}/test_complex"
        }
        
        # 测试默认参数
        result = await ligand_design_intermediate(
            pdb_file=self.test_pdb,
            output_dir=self.output_dir
        )
        
        result_data = json.loads(result)
        self.assertEqual(result_data["status"], "success")
        self.assertEqual(result_data["design_level"], "intermediate")
        
        # 测试自定义温度
        result_custom = await ligand_design_intermediate(
            pdb_file=self.test_pdb,
            output_dir=self.output_dir,
            custom_temperature=0.25
        )
        
        result_custom_data = json.loads(result_custom)
        self.assertEqual(result_custom_data["parameters"]["temperature"], 0.25)
        self.assertTrue(result_custom_data["parameters"]["custom_temperature_used"])
    
    @patch('mcp_server_ligand.run_ligandmpnn_docker')
    async def test_advanced_design_tool(self, mock_docker):
        """测试高级设计工具"""
        mock_docker.return_value = {
            "status": "success",
            "stdout": "Advanced design completed",
            "stderr": "",
            "returncode": 0,
            "command": "docker run ...",
            "output_path": f"{self.output_dir}/test_complex"
        }
        
        result = await ligand_design_advanced(
            pdb_file=self.test_pdb,
            output_dir=self.output_dir,
            design_chain="A,B",
            max_batches=150,
            include_rare_aa=True
        )
        
        result_data = json.loads(result)
        self.assertEqual(result_data["status"], "success")
        self.assertEqual(result_data["design_level"], "advanced")
        self.assertEqual(result_data["parameters"]["number_of_batches"], 150)
        self.assertTrue(result_data["parameters"]["include_rare_aa"])
        self.assertTrue(result_data["parameters"]["random_seed"])
    
    async def test_error_handling_missing_file(self):
        """测试文件不存在的错误处理"""
        nonexistent_file = "/path/to/nonexistent.pdb"
        
        result = await ligand_design_basic(
            pdb_file=nonexistent_file,
            output_dir=self.output_dir
        )
        
        result_data = json.loads(result)
        self.assertEqual(result_data["status"], "error")
        self.assertIn("PDB文件不存在", result_data["message"])
    
    async def test_parameter_validation(self):
        """测试参数验证"""
        # 测试无效温度
        result = await ligand_design_intermediate(
            pdb_file=self.test_pdb,
            output_dir=self.output_dir,
            custom_temperature=1.5  # 超出范围
        )
        
        result_data = json.loads(result)
        self.assertEqual(result_data["status"], "error")
        self.assertIn("温度必须在", result_data["message"])
        
        # 测试过大的批次数
        result = await ligand_design_advanced(
            pdb_file=self.test_pdb,
            output_dir=self.output_dir,
            max_batches=250  # 超出限制
        )
        
        result_data = json.loads(result)
        self.assertEqual(result_data["status"], "error")
        self.assertIn("最大批次数不能超过", result_data["message"])

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_mcp_server_tools_registration(self):
        """测试MCP服务器工具注册"""
        # 这里我们需要检查工具是否正确注册到MCP服务器
        # 由于FastMCP的内部实现，我们主要验证函数存在并可调用
        
        # 验证所有工具函数都存在
        tools = [
            ligand_design_basic,
            ligand_design_intermediate, 
            ligand_design_advanced,
            get_ligand_design_presets
        ]
        
        for tool in tools:
            self.assertTrue(callable(tool))
            self.assertTrue(asyncio.iscoroutinefunction(tool))

def run_basic_test():
    """运行基本功能测试"""
    print("🧪 MCP服务器基本测试...")
    
    # 测试服务器初始化
    assert mcp is not None and mcp.name == "ligandmpnn_ligand_design"
    print("✅ 服务器初始化")
    
    # 测试预设配置
    assert len(LIGAND_DESIGN_PRESETS) == 3
    basic = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.BASIC]
    intermediate = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.INTERMEDIATE] 
    advanced = LIGAND_DESIGN_PRESETS[LigandDesignComplexity.ADVANCED]
    
    # 验证复杂度递增
    assert basic["temperature"] < intermediate["temperature"] < advanced["temperature"]
    assert basic["number_of_batches"] < intermediate["number_of_batches"] < advanced["number_of_batches"]
    print("✅ 预设配置正确")
    
    # 测试工具函数
    tools = [ligand_design_basic, ligand_design_intermediate, ligand_design_advanced, get_ligand_design_presets]
    for tool in tools:
        assert callable(tool) and asyncio.iscoroutinefunction(tool)
    print("✅ 工具函数注册")
    
    print("\n📋 配体设计预设:")
    for level, config in LIGAND_DESIGN_PRESETS.items():
        print(f"  {level.value}: 温度{config['temperature']}, 批次{config['number_of_batches']}")

async def test_async_functions():
    """测试异步功能"""
    try:
        result = await get_ligand_design_presets()
        result_data = json.loads(result)
        assert "ligand_design_presets" in result_data
        print("✅ 异步工具调用")
        return True
    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LigandMPNN MCP服务器测试")
    print("=" * 50)
    
    try:
        run_basic_test()
        success = asyncio.run(test_async_functions())
        
        if success:
            print("\n🎉 MCP服务器构造成功！")
            print("\n📝 三种配体设计预设:")
            print("1. basic - 保守策略，高稳定性")
            print("2. intermediate - 平衡策略，推荐使用") 
            print("3. advanced - 探索策略，最大多样性")
            print("\n🐳 启动: python mcp_server_ligand.py")
        else:
            exit(1)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        exit(1)