import subprocess
import os
import json
import freesasa
import numpy as np
from Bio.PDB import MMCIFParser, PDBIO, PDBParser, is_aa
import MDAnalysis as mda  
from MDAnalysis.analysis import rms 
import torch
import esm


def chai_batch_fold(target_seqs, ligand_seqs, save_dir, predict_ligand=True, use_slurm=False, chai_py_dir="/gene/home/cjn/miniconda3/envs/chai_fold/bin/chai-lab"):
    for i, ligand_seq in enumerate(ligand_seqs):
        fasta_file = os.path.join(save_dir, f"{i}_complex.fasta")
        output_dir = os.path.join(save_dir, f"{i}_complex")
        seqs = target_seqs + [ligand_seq]
        seq_to_fasta(fasta_file, seqs)
        if not os.path.exists(output_dir):
            chai_fold(fasta_file, output_dir, use_slurm, chai_py_dir)
        
    if predict_ligand:
        for i, ligand_seq in enumerate(ligand_seqs):
            fasta_file = os.path.join(save_dir, f"{i}_ligand.fasta")
            output_dir = os.path.join(save_dir, f"{i}_ligand")
            seqs = [ligand_seq]
            seq_to_fasta(fasta_file, seqs)
            if not os.path.exists(output_dir):
                chai_fold(fasta_file, output_dir, use_slurm, chai_py_dir)

                
def seq_to_fasta(fasta_file, seqs):
    with open(fasta_file, "w") as ifile:
        for i, seq in enumerate(seqs):
            ifile.write(f">protein|seq{i}\n")
            ifile.write(f"{seq}\n")

   
def chai_fold(fasta_file, output_dir, use_slurm, chai_py_dir):
    fasta_name, _ = os.path.splitext(fasta_file)
    if not use_slurm:
        with open(f"chai.out", 'w') as output_file, open(f"chai.err", 'w') as error_file:  
            subprocess.run(  
                f"{chai_py_dir} fold {fasta_file} {output_dir}",  
                shell=True,  
                stdout=output_file,  
                stderr=error_file  
            )  
    else:
        slurm_file = os.path.splitext(fasta_file)[0] + ".slurm"
        with open(slurm_file, "w") as ifile:
            ifile.write(f"""#!/bin/bash


{chai_py_dir} fold {fasta_file} {output_dir}
""")    
        env = os.environ.copy()  # 复制当前环境变量  
        env["MPLBACKEND"] = ""  # 否则用notebook提交任务，matplotlib会报错
        subprocess.run(f"sbatch {slurm_file}", shell=True, env=env, cwd=os.path.dirname(fasta_file)) 


# score
def cal_ca_rmsd(pdb1, pdb2):
    # 加载两个结构  
    u1 = mda.Universe(pdb1)  # 替换为你的第一个PDB文件  
    u2 = mda.Universe(pdb2)  # 替换为你的第二个PDB文件  

    # 选择骨架原子，通常是Cα原子  
    selection1 = u1.select_atoms('name CA')  
    selection2 = u2.select_atoms('name CA')  

    # 计算 RMSD  
    # 首先对齐两个结构  
    rmsd = rms.rmsd(selection1.positions, selection2.positions, superposition=True)  
    return rmsd


def cif_to_pdb(cif_file, out_prefix):
    out_pdbs = []
    # 读取CIF文件  
    parser = MMCIFParser(QUIET=True)  
    structure = parser.get_structure('Complex', cif_file)  
    # 保存整个复合物到PDB文件  
    io = PDBIO()  
    io.set_structure(structure)  
    io.save(f'{out_prefix}.pdb')  
    out_pdbs.append(f'{out_prefix}.pdb')
    # 将receptor和ligand分别保存为单独的PDB文件 
    u = mda.Universe(out_pdbs[0])
    chainIDs = []
    for atom in u.atoms:
        if atom.chainID not in chainIDs:
            chainIDs.append(atom.chainID)
    if len(chainIDs) > 1:
        selection = u.select_atoms(' or '.join([f'chainID {chainID}' for chainID in chainIDs[:-1]]))
        with mda.Writer(f'{out_prefix}_receptor.pdb') as writer:  
            writer.write(selection)  
        selection = u.select_atoms(f'chainID {chainIDs[-1]}')  
        with mda.Writer(f'{out_prefix}_ligand.pdb') as writer:  
            writer.write(selection)  
        out_pdbs.append(f'{out_prefix}_receptor.pdb')
        out_pdbs.append(f'{out_prefix}_ligand.pdb')
    return out_pdbs


def get_ptm_iptm_aggregate_score(npz_file):
    data = np.load(npz_file)  
    ptm = data['ptm'][0]
    iptm = data['iptm'][0]
    aggregate_score = data['aggregate_score'][0]
    return ptm, iptm, aggregate_score


def cal_sasa(pdb_files):
    polar_areas = []
    apopar_areas = []
    for pdb_file in pdb_files:
        structure = freesasa.Structure(pdb_file)
        result = freesasa.calc(structure)
        area_classes = freesasa.classifyResults(result, structure)
        polar_areas.append(area_classes["Polar"])
        apopar_areas.append(area_classes["Apolar"])
    return polar_areas, apopar_areas


def get_best_pred(result_dir, model_num=5):
    # 基于aggregate_score排序
    highest_score = 0
    for i in range(model_num):
        npz_file = os.path.join(result_dir, f"scores.model_idx_{i}.npz")
        cif_file = os.path.join(result_dir, f"pred.model_idx_{i}.cif")
        ptm, iptm, aggregate_score = get_ptm_iptm_aggregate_score(npz_file)
        if aggregate_score > highest_score:
            best_npz = npz_file
            best_cif = cif_file
            highest_score = aggregate_score
    return best_cif, best_npz


def get_sequences(pdb_file):
    # 定义三字母到单字母的映射  
    aa_dict = {  
        'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F',  
        'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L',  
        'MET': 'M', 'ASN': 'N', 'PRO': 'P', 'GLN': 'Q', 'ARG': 'R',  
        'SER': 'S', 'THR': 'T', 'VAL': 'V', 'TRP': 'W', 'TYR': 'Y'  
    }  
    parser = PDBParser(QUIET=True)  
    structure = parser.get_structure('Protein', pdb_file)  

    # 提取序列  
    sequences = []  
    for model in structure:  
        for chain in model:  
            # 获取当前链的氨基酸序列  
            seq = ''  
            for residue in chain:  
                if is_aa(residue):  # 检查是否是氨基酸  
                    res_name = residue.get_resname()  # 获取氨基酸的三字母代码  
                    seq += aa_dict.get(res_name, 'X')  # 转换为单字母代码  
            sequences.append(seq)  
    return sequences

# cluster
def cal_TMscore(pdb1_pwd, pdb2_pwd, tmscore_pwd, usalign_pwd="/personal/software/USalign/USalign"):
    if not os.path.exists(tmscore_pwd):
        subprocess.run(
            f"{usalign_pwd} {pdb1_pwd} {pdb2_pwd} -mol prot -mm 1 -ter 0 -outfmt 2 -fast > {tmscore_pwd}", shell=True
            )
    with open(tmscore_pwd, "r") as ifile:
        for line in ifile:
            if not line.startswith("#PDBchain1"):
                words = line.split()
                TM1 = float(words[2])
                TM2 = float(words[3])
                RMSD = float(words[4])
                ID2 = float(words[6])
                L1 = int(words[-3])
                Lali = int(words[-1])
                return TM1, TM2

def remove_similar_structure(similarity_matrix, similarity_cutoff=0.2):
    out_ids = []
    for i in range(len(similarity_matrix)):
        similar_check = True
        for j in out_ids:
            if similarity_matrix[i, j] < similarity_cutoff:
                similar_check = False
                break
        if similar_check:
            out_ids.append(i)
    return np.array(out_ids)

# # mpnn
# def run_mpnn(pdb_file, save_pwd, design_chain="B", mpnn_dir="/personal/software/LigandMPNN", mpnn_python="/opt/mamba/envs/ligandmpnn_env/bin/python", mode="all", use_slurm=False, temperature=0.3, number_of_batches=40):
#     pdb_name, _ = os.path.splitext(pdb_file)
    
#     if mode == "soluble":
#         model_type = "soluble_mpnn"
#         checkpoint_mpnn = "./model_params/solublempnn_v_48_020.pt"
#     elif mode == "membrane":
#         model_type = "global_label_membrane_mpnn"
#         checkpoint_mpnn = "./model_params/global_label_membrane_mpnn_v_48_020.pt"
#     elif mode == "all":
#         model_type = "protein_mpnn"
#         checkpoint_mpnn = "./model_params/proteinmpnn_v_48_020.pt"   
#     else:
#         raise
#     if not use_slurm: 
#         with open(f"{pdb_name}_mpnn_output.txt", 'w') as output_file, open(f"{pdb_name}_mpnn_error.txt", 'w') as error_file:  
#             result = subprocess.run(  
#                 f'{mpnn_python} run.py \
#             --model_type "{model_type}" \
#             --checkpoint_soluble_mpnn "{checkpoint_mpnn}" \
#             --seed 111 \
#             --pdb_path "{pdb_file}" \
#             --out_folder "{save_pwd}" \
#             --chains_to_design "{design_chain}" \
#             --batch_size 50 \
#             --number_of_batches {number_of_batches} \
#             --omit_AA "CX" \
#             --temperature {temperature}',  
#                 shell=True,  
#                 cwd=mpnn_dir,
#                 stdout=output_file,  
#                 stderr=error_file  
#             )
#     else:
#         with open(f"{pdb_name}_mpnn.slurm", "w") as ifile:
#             ifile.write(f"""#!/bin/bash
# #SBATCH --job-name=mpnn
# #SBATCH --output=mpnn.out
# #SBATCH --error=mpnn.err
# #SBATCH --nodes=1
# #SBATCH --cpus-per-task=8
# #SBATCH --gres=gpu:1
# #SBATCH --time=24:00:00
# #SBATCH --partition=4090

# source /mnt/beegfs/opt/module/tools/modules/init/bash
# module load cuda/12.4

# {mpnn_python} run.py \
#             --model_type "{model_type}" \
#             --checkpoint_soluble_mpnn "{checkpoint_mpnn}" \
#             --seed 111 \
#             --pdb_path "{pdb_file}" \
#             --out_folder "{save_pwd}" \
#             --chains_to_design "{design_chain}" \
#             --batch_size 50 \
#             --number_of_batches {number_of_batches} \
#             --omit_AA "CX" \
#             --temperature {temperature}
# """)    
#         subprocess.run(f"sbatch {pdb_name}_mpnn.slurm", shell=True, cwd=mpnn_dir) 


def diff_aa_num(seq1, seq2):
    seq1 = np.array(list(seq1))
    seq2 = np.array(list(seq2))
    return np.sum(seq1 != seq2)


def seq_repeat_segment_len(seq):
    count = 0
    rep2_count = 0
    rep3_count = 0
    rep3more_count = 0
    pre_aa = ""
    for aa in seq:
        if aa != pre_aa:
            count = 1
        else:
            count += 1
            if count == 2:
                rep2_count +=1
            elif count == 3:
                rep3_count += 1
            elif count > 3:
                rep3more_count += 1
        pre_aa = aa
    return rep2_count, rep3_count, rep3more_count


def cal_seq_charge(seq):
    charge = 0
    for aa in seq:
        if aa in ["D", "E"]:
            charge -= 1
        elif aa in ["R", "K"]:
            charge += 1
    return charge


def cal_seq_aa_percent(seq, count_aa=""):
    count = 0
    for aa in seq:
        if aa in count_aa:
            count += 1
    return count/len(seq)


def filter_seqs(fasta_pwd, out_seq_num, min_diff_aa_percent=0.2, max_abs_charge=10, esm_score_pwd=None, esm_score_percentile=50):
    lig_seqs = []
    scores = []
    if esm_score_pwd != None:
        with open(esm_score_pwd, 'r') as json_file:  
            esm_scores = json.load(json_file)
        esm_score_cutoff = np.percentile(list(esm_scores.values()), esm_score_percentile) 
    with open(fasta_pwd, "r") as ifile:
        lines = ifile.readlines()
        for line in lines[2:]:
            if line.startswith(">"):
                words = line.split()
                for word in words:
                    if word.startswith("overall_confidence"):
                        score = float(word.split("=")[-1][:-1])
            else:
                lig_seq = line.strip().split(":")[-1]
                if lig_seq not in lig_seqs:
                    scores.append(score)
                    lig_seqs.append(lig_seq)
    ids = np.argsort(scores)[::-1]
    out_seqs = []
    for id in ids:
        cur_seq = lig_seqs[id]
        similar_check = True
        rep2_count, rep3_count, rep3more_count = seq_repeat_segment_len(cur_seq)
        if esm_score_pwd != None and esm_scores[cur_seq] < esm_score_cutoff:
            print("ESM score too low!", cur_seq)
            continue
        if rep2_count > 5 or rep3_count > 1 or rep3more_count > 0:
            print("Too many repeat!", cur_seq)
            continue
        if abs(cal_seq_charge(cur_seq)) > max_abs_charge:
            print("Too many charge!", cur_seq)
            continue
        if cur_seq[0] == "M":
            print("No first M!", cur_seq)
            continue            
        for out_seq in out_seqs:
            if diff_aa_num(cur_seq, out_seq) < min_diff_aa_percent * len(out_seqs[0]):
                print("Too similar!", cur_seq, out_seq)
                similar_check = False
                break
        if similar_check:
            out_seqs.append(cur_seq)
            if len(out_seqs) == out_seq_num:
                break
    return out_seqs


def filter_tm_seqs(fasta_pwd, out_seq_num, min_diff_aa_percent=0.2, min_abs_charge=1, max_abs_charge=10):
    lig_seqs = []
    scores = []
    with open(fasta_pwd, "r") as ifile:
        lines = ifile.readlines()
        for line in lines[2:]:
            if line.startswith(">"):
                words = line.split()
                for word in words:
                    if word.startswith("overall_confidence"):
                        score = float(word.split("=")[-1][:-1])
            else:
                lig_seq = line.strip().split(":")[-1]
                if lig_seq not in lig_seqs:
                    scores.append(score)
                    lig_seqs.append(lig_seq)
    ids = np.argsort(scores)[::-1]
    out_seqs = []
    for id in ids:
        cur_seq = lig_seqs[id]
        similar_check = True
        rep2_count, rep3_count, rep3more_count = seq_repeat_segment_len(cur_seq)
        if rep3_count > 1 or rep3more_count > 0:
            print("Too many repeat!", cur_seq)  # LL, LLL, LLLLLL
            continue
        abs_charge = abs(cal_seq_charge(cur_seq))
        if abs_charge > max_abs_charge or abs_charge < min_abs_charge:
            print("Too many or low charge!", cur_seq)
            continue
        if cur_seq[0] == "M":
            print("No first M!", cur_seq)
            continue 
        polar_percent = cal_seq_aa_percent(cur_seq, count_aa="KRDEQNSTH")
        if polar_percent < 0.1 or polar_percent > 0.4:
            print("Too polar or apolar!", cur_seq)
            continue                
        for out_seq in out_seqs:
            if diff_aa_num(cur_seq, out_seq) < min_diff_aa_percent * len(out_seqs[0]):
                print("Too similar!", cur_seq, out_seq)
                similar_check = False
                break
        if similar_check:
            out_seqs.append(cur_seq)
            if len(out_seqs) == out_seq_num:
                break
    if len(out_seqs) == 0:
        out_seqs = [lig_seqs[id] for id in ids[:out_seq_num]]
    return out_seqs


def cal_distance(pdb, select1, select2):
    # 初始化 Universe，这里以 PSF/DCD 为例  
    u = mda.Universe(pdb)  

    # 选择氨基酸范围，注意需确认是否使用 'chain'/'segid' 等选择器  
    selA = u.select_atoms(select1)  
    selB = u.select_atoms(select2)  

    comA = selA.center_of_mass()  
    comB = selB.center_of_mass()  
    dist = np.linalg.norm(comA - comB)  # 质心欧几里得距离  
    return dist


def cal_esm_score(fa_pwd, esm_score_pwd, py_pwd, esm_script_pwd):
    slurm_file = os.path.splitext(fa_pwd)[0] + ".slurm"
    with open(slurm_file, "w") as ifile:
        ifile.write(f"""#!/bin/bash

{py_pwd} {esm_script_pwd} {fa_pwd} {esm_score_pwd}
""")    
    subprocess.run(f"sbatch {slurm_file}", shell=True, cwd=os.path.dirname(fa_pwd))