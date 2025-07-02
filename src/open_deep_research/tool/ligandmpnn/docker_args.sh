#!/bin/bash
# 改进版本的LigandMPNN Docker命令（获得多样化输出）
# 确保输出目录有正确的权限
chmod 777 /root/agent_project/agentic_workflow_for_proteindesign/tool/ligandmpnn_tool/output/

echo "运行改进的LigandMPNN测试..."

# 运行LigandMPNN (移除固定种子，提高温度)
docker run --rm -it --gpus all --dns 8.8.8.8 \
-v /root/agent_project/agentic_workflow_for_proteindesign/tool/ligandmpnn_tool/input:/opt/input \
-v /root/agent_project/agentic_workflow_for_proteindesign/tool/ligandmpnn_tool/output:/opt/output \
registry.dp.tech/dptech/prod-15874/ligandmpnn:1.4 python /root/LigandMPNN/run.py \
--model_type ligand_mpnn \
--checkpoint_ligand_mpnn /root/LigandMPNN/model_params/ligandmpnn_v_32_005_25.pt \
--pdb_path /opt/input/1BC8.pdb \
--out_folder /opt/output/1BC8_improved \
--number_of_batches 40 \
--temperature 0.5 \
#--seed 42 \ # 移除固定种子
--chains_to_design B \
--parse_these_chains_only A,B,C \
--omit_AA CX \
--ligand_mpnn_use_side_chain_context 1 \
--pack_side_chains 1 \
--checkpoint_path_sc /root/LigandMPNN/model_params/ligandmpnn_sc_v_32_002_16.pt \
--number_of_packs_per_design 3

echo "测试完成！检查输出目录："
echo "/root/agent_project/agentic_workflow_for_proteindesign/tool/ligandmpnn_tool/output/1BC8_improved/seqs/" 