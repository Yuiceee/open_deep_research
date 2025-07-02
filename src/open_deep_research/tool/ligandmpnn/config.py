import json
import os
import re
import shlex
from enum import Enum
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

from macrosoft.pages.apps.utils import generate_sbatch_script, get_sif_path

page_name = Path(__file__).parent.name

class ModelTypeOptions(str, Enum):
    """
    枚举类型，多选一。
    表示用户可以选择的模型类型及其对应的高斯噪声水平
    """

    ProteinMPNN_VeryLowNoise = "ProteinMPNN - Very Low Gaussian Noise (0.05 angstrom)"
    ProteinMPNN_LowNoise = "ProteinMPNN - Low Gaussian Noise (0.10 angstrom)"
    ProteinMPNN_MediumNoise = "ProteinMPNN - Medium Gaussian Noise (0.20 angstrom)"
    ProteinMPNN_HighNoise = "ProteinMPNN - High Gaussian Noise (0.30 angstrom)"
    LigandMPNN_VeryLowNoise = "LigandMPNN - Very Low Gaussian Noise (0.05 angstrom)"
    LigandMPNN_LowNoise = "LigandMPNN - Low Gaussian Noise (0.10 angstrom)"
    LigandMPNN_MediumNoise = "LigandMPNN - Medium Gaussian Noise (0.20 angstrom)"
    LigandMPNN_HighNoise = "LigandMPNN - High Gaussian Noise (0.30 angstrom)"
    SolubleMPNN_VeryLowNoise = "SolubleMPNN - Very Low Gaussian Noise (0.02 angstrom)"
    SolubleMPNN_LowNoise = "SolubleMPNN - Low Gaussian Noise (0.10 angstrom)"
    SolubleMPNN_MediumNoise = "SolubleMPNN - Medium Gaussian Noise (0.20 angstrom)"
    SolubleMPNN_HighNoise = "SolubleMPNN - High Gaussian Noise (0.30 angstrom)"
    PerResidueLabelMembraneMPNN = "Per-Residue Label Membrane MPNN"
    GlobalLabelMembraneMPNN = "Global Label Membrane MPNN"

class SelectedResidueOptions(str, Enum):
    """
    枚举类型，多选一。
    表示用户是固定所选残基还是重新设计所选残基。
    """

    Fix = "Fix Selected Residues"
    Redesign = "Redesign Selected Residues"


class DesignSettings(BaseModel):
    """
    用于定义基础设计参数
    """

    chains_to_design: str = Field(
        default="",
        title="Design Chains (Optional)",
        description='指定要设计的链的链名（可选）。提供的链名必须与PDB文件中的链名一致，并以逗号分隔，如输入"A,B"表示设计输入文件中的A链和B链，其他链保持固定，并输出PDB文件中所有链。如果留空，将自动设计输入蛋白质中的所有链。',
    )
    chains_to_parse: str = Field(
        default="",
        title="Parse Chains (Optional)",
        description='指定要处理的链的链名（可选）。提供的链名必须与PDB文件中的链名一致，并以逗号分隔，如输入"A"表示只处理并设计输入文件中的A链，输入"A,B"表示设计输入文件中的A链和B链，不输出其他链。如果留空，将自动处理输入蛋白质中的所有链。',
    )
    selected_residues: str = Field(
        default="",
        title="Selected Residues (Optional)",
        description='指定要固定类型的氨基酸序列（可选）。提供的链名和编号必须与PDB文件一致，输入形式类似"A1, A3-8"，如输入"A5, A10, A30"，"A1-5, B1-8, B20"，"A1-10, B1-10"表示固定输入文件中相应链和编号的氨基酸。氨基酸编号与输入pdb文件保持一致。',
    )
    redesign_selection: Literal[
        SelectedResidueOptions.Redesign, SelectedResidueOptions.Fix
    ] = Field(
        default=SelectedResidueOptions.Redesign,
        title="How to Deal with Selected Residues",
        description="选择对上述指定残基进行再设计，还是固定其余残基。",
    )
    design_num: int = Field(
        default=1,
        title="Number of Output Sequences (Optional)",
        description="输出设计的序列数（可选）",
    )
    temp: float = Field(
        default=0.1,
        title="Sampling Temperature",
        ge=0.0,
        le=1.0,
        multiple_of=0.01,
        description="采样温度（可选），范围在0-1.0之间，温度越小则序列概率越大，温度越大则序列多样性越高。",
    )

    def format_fixed_position(self) -> str:
        """
        将selected_residues字段的值转换为一个连续的残基编号序列的字符串。
        例如，"A5, A10, A30, A1-5, B1-8, B20, A1-10, B1-10" 将被转换为
        "A1 A2 A3 A4 A5 A5 A10 A30 B1 B2 B3 B4 B5 B6 B7 B8 B20 A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 B1 B2 B3 B4 B5 B6 B7 B8 B9 B10"
        """
        formatted_positions = []
        # 正则表达式匹配链标识符和残基编号或编号范围
        pattern = re.compile(r"([A-Za-z]+)\s*(\d+)(?:-\s*(\d+))?")

        # 分割selected_residues字符串中的各个项
        for item in self.selected_residues.split(","):
            item = item.strip()  # 去除空白字符
            match = pattern.match(item)
            if not match:
                raise ValueError(f"无法识别的位置格式: '{item}'")
            chain_id, start, end = match.groups()
            start = int(start)
            if end:
                formatted_positions.extend(
                    f"{chain_id}{i}" for i in range(start, int(end) + 1)
                )
            else:
                # 如果不存在结束编号，则只有一个残基
                formatted_positions.append(f"{chain_id}{start}")

        # 将列表转换为以空格分隔的字符串
        return " ".join(formatted_positions)

    # 验证器，用于检查selected_residues字段的格式
    @field_validator("selected_residues")
    @classmethod
    def validate_fix_position(cls, v):
        # 验证selected_residues的格式是否正确
        if not all(len(part.split("-")) <= 2 for part in v.split(",")):
            raise ValueError("selected_residues格式错误，应为'链名+残基范围'或'链名+单个残基编号'的形式。")
        return v


class AdvancedSettings(BaseModel):
    """
    用于定义额外设计参数
    """

    model_type: Literal[
        ModelTypeOptions.ProteinMPNN_VeryLowNoise,
        ModelTypeOptions.ProteinMPNN_LowNoise,
        ModelTypeOptions.ProteinMPNN_MediumNoise,
        ModelTypeOptions.ProteinMPNN_HighNoise,
        ModelTypeOptions.LigandMPNN_VeryLowNoise,
        ModelTypeOptions.LigandMPNN_LowNoise,
        ModelTypeOptions.LigandMPNN_MediumNoise,
        ModelTypeOptions.LigandMPNN_HighNoise,
        ModelTypeOptions.SolubleMPNN_VeryLowNoise,
        ModelTypeOptions.SolubleMPNN_LowNoise,
        ModelTypeOptions.SolubleMPNN_MediumNoise,
        ModelTypeOptions.SolubleMPNN_HighNoise,
        ModelTypeOptions.PerResidueLabelMembraneMPNN,
        ModelTypeOptions.GlobalLabelMembraneMPNN,
    ] = Field(
        default=ModelTypeOptions.LigandMPNN_VeryLowNoise,
        title="Model Type",
        description="""
    **选择用于序列设计的模型：**  
    **1. ProteinMPNN :**  
- 基于图神经网络的蛋白质序列设计模型，能够用于单体蛋白、多聚体蛋白、目标结合蛋白等的设计。对于输入结构只包含蛋白质的结构，用户可以选择该模型。

    **2. LigandMPNN :**  
- 在ProteinMPNN的基础上，能够显式建模小分子、核苷酸、金属等配体，在设计序列时考虑到蛋白质与这些非蛋白质分子的相互作用。对于输入结构中包含配体的结构，用户需选择该模型。

    **3. SolubleMPNN :**  
- 与ProteinMPNN类似，唯一区别是使用的训练集去除了膜蛋白，只包含可溶蛋白质。对于可溶蛋白质的设计，用户可以选择该模型。

- 高斯噪声的大小代表训练过程中添加到蛋白质主链坐标上的随机扰动的程度，性能最好的模型通常是0.3 angstrom或0.2 angstrom（参考[ProteinMPNN论文](https://www.science.org/doi/10.1126/science.add2187 "ProteinMPNN")）。
""",
        description_type="markdown",
    )
    seed: int = Field(
        default=42,
        title="Seed",
        description="设置随机种子（可选）。相同的随机种子会在相同的指令上产生相同的结果，不同的种子则可以改变设计结果，不设置则随机产生结果。",
    )
    omit_AA: str = Field(
        default="",
        title="Excluded Amino Acids (Optional)",
        description='设置设计中排除的氨基酸类型（可选）。如"ACEY"表示设计结果中不会出现"A, C, E, Y"这四种氨基酸类型。',
    )
    omit_AA_per_residue: str = Field(
        default="",
        title="Design Scheme (Optional)",
        format="multi-line",
        description='详细设置指定残基的设计方案（可选）。如"A5: EKA, A10: EK, A30: K", "A1-5: EKA, B1-8: EK, B20: K",表示指定残基可选择的设计类型。氨基酸编号与输入pdb文件保持一致。',
    )
    lm_use_sc_context: bool = Field(
        default=False,
        title="Use Side Chain Context for Fixed Residues",
        description="是否将固定残基的侧链原子作为额外的配体原子，即考虑固定残基的侧链原子对序列设计的影响，更加准确但会增加计算量",
    )

    @field_validator("omit_AA")
    @classmethod
    def validate_omit_AA(cls, v):
        """
        验证 'omit_AA' 字段的值是否为有效的氨基酸类型组合。
        """
        if not isinstance(v, str) or not all(c.isalpha() and c.isupper() for c in v):
            raise ValueError("omit_AA 字段必须是一个只包含大写字母的字符串，代表一个或多个氨基酸类型。例如：ACEY")
        if not set(v).issubset("ACDEFGHIKLMNPQRSTVWY"):
            raise ValueError(
                "omit_AA 字段中的氨基酸类型必须是有效的氨基酸类型。目前只支持20种标准氨基酸：ACDEFGHIKLMNPQRSTVWY"
            )
        return v

    @field_validator("omit_AA_per_residue")
    @classmethod
    def validate_omit_AA_per_residue(cls, v):
        """
        验证 'omit_AA_per_residue' 字段的值是否符合 '位置: 氨基酸类型' 的格式。
        """
        if not v:  # 如果字段为空字符串或None，则不需要验证
            return v

        # 使用正则表达式来验证每个方案的格式
        scheme_pattern = re.compile(r"^([A-Za-z]\d+-\d+|[A-Za-z]\d+):\s*([A-Z]+)$")
        position_pattern = re.compile(r"^([A-Za-z])\d+(?:-\d+)?$")
        schemes = v.split(",")
        # print(schemes)

        for scheme in schemes:
            scheme = scheme.strip()  # 去除可能的前后空格
            # print(scheme)
            match = scheme_pattern.match(scheme)
            if not match:
                raise ValueError(f"方案 '{scheme}' 的格式错误，应为 '链名+位置或范围: 氨基酸类型'。")

            position, aa_types = match.groups()
            if not position_pattern.match(position):
                raise ValueError(f"位置 '{position}' 的格式错误，应为 '链名残基编号' 或 '链名起始残基-结束残基'。")
            if aa_types is None or not aa_types:
                raise ValueError(f"在 '{scheme}' 中，氨基酸类型不能为空。")

            # 检查氨基酸类型是否全部为大写字母
            if not all(aa.isupper() for aa in aa_types):
                raise ValueError("每个方案中的氨基酸类型必须是大写字母。")
        return v

    def process_omit_AA_per_residue(self, out_folder: str) -> None:
        amino_acids = "ACDEFGHIKLMNPQRSTVWY"
        design_scheme = {}

        # 解析omit_AA_per_residue输入
        for scheme in self.omit_AA_per_residue.split(","):
            position, aa_types = scheme.split(":")
            position = position.strip()  # 去除可能的前后空格
            aa_types = aa_types.strip()
            aa_types = aa_types.upper()  # 确保氨基酸类型为大写

            if "-" in position:
                # 如果位置是一个范围
                chain_start, pos_range_end = position.split("-")
                # print(chain_start, pos_range_end)
                chain_id = chain_start[0]
                # print(chain_start[1:])
                pos_range_end = int(pos_range_end)
                pos_range_start = int(chain_start[1:])

                # start, end = int(pos_range.split()[0]), int(pos_range.split()[1])
                for pos in range(pos_range_start, pos_range_end + 1):
                    excluded_aa = set(a for a in aa_types if a in amino_acids)
                    remaining_aa = "".join(
                        sorted(a for a in amino_acids if a not in excluded_aa)
                    )
                    design_scheme[f"{chain_id}{pos}"] = remaining_aa
            else:
                # 如果位置是单个残基
                # print(position)
                excluded_aa = set(a for a in aa_types if a in amino_acids)
                remaining_aa = "".join(
                    sorted(a for a in amino_acids if a not in excluded_aa)
                )
                design_scheme[f"{position}"] = remaining_aa
        # 保存到JSON文件
        with open(f"{out_folder}/omit_AA_per_residue.json", "w") as json_file:
            json.dump(design_scheme, json_file, indent=0, ensure_ascii=False)


class PackingSettings(BaseModel):
    """
    用于定义repack的参数
    """

    pack_side_chains: bool = Field(
        default=False,
        title="Pack Side Chains",
        description="选择是否对设计残基的侧链进行预测，使输出结果中包含侧链结构。",
    )
    number_of_packs_per_design: int = Field(
        default=0,
        title="Number of Packs Per Design",
        description="对每个序列设计进行侧链结构预测的输出数（可选）",
    )  # condition = ui.Visible(PackingSettings, ("pack_side_chains"), Equal, (True))
    repack_everything: bool = Field(
        default=False,
        title="Repack Everything",
        description="选择是否对包括固定残基的所有侧链进行repack，不选择则固定残基的侧链输出与输入结构相同。",
    )


class Config(BaseModel):
    input_file: str = Field(
        default="input.pdb", title="Input File", description="输入结构文件路径"
    )
    design_setting: DesignSettings = Field(
        default_factory=DesignSettings,
        title="Design Settings",
        description="蛋白质序列设计基础参数",
    )
    advanced_setting: AdvancedSettings = Field(
        default_factory=AdvancedSettings,
        title="Advanced Settings",
        description="蛋白质序列设计进阶参数",
    )
    packing_setting: PackingSettings = Field(
        default_factory=PackingSettings,
        title="Packing Settings",
        description="蛋白质侧链设计参数",
    )


PARENT_DIR = "/root/LigandMPNN"
MODEL_DIR = Path(PARENT_DIR) / "model_params"

MODEL_CHECKPOINTS = {
    ModelTypeOptions.LigandMPNN_VeryLowNoise: (
        "ligand_mpnn",
        f"{MODEL_DIR}/ligandmpnn_v_32_005_25.pt",
    ),
    ModelTypeOptions.LigandMPNN_LowNoise: (
        "ligand_mpnn",
        f"{MODEL_DIR}/ligandmpnn_v_32_010_25.pt",
    ),
    ModelTypeOptions.LigandMPNN_MediumNoise: (
        "ligand_mpnn",
        f"{MODEL_DIR}/ligandmpnn_v_32_020_25.pt",
    ),
    ModelTypeOptions.LigandMPNN_HighNoise: (
        "ligand_mpnn",
        f"{MODEL_DIR}/ligandmpnn_v_32_030_25.pt",
    ),
    ModelTypeOptions.ProteinMPNN_VeryLowNoise: (
        "protein_mpnn",
        f"{MODEL_DIR}/proteinmpnn_v_48_002.pt",
    ),
    ModelTypeOptions.ProteinMPNN_LowNoise: (
        "protein_mpnn",
        f"{MODEL_DIR}/proteinmpnn_v_48_010.pt",
    ),
    ModelTypeOptions.ProteinMPNN_MediumNoise: (
        "protein_mpnn",
        f"{MODEL_DIR}/proteinmpnn_v_48_020.pt",
    ),
    ModelTypeOptions.ProteinMPNN_HighNoise: (
        "protein_mpnn",
        f"{MODEL_DIR}/proteinmpnn_v_48_030.pt",
    ),
    ModelTypeOptions.SolubleMPNN_VeryLowNoise: (
        "soluble_mpnn",
        f"{MODEL_DIR}/solublempnn_v_48_002.pt",
    ),
    ModelTypeOptions.SolubleMPNN_LowNoise: (
        "soluble_mpnn",
        f"{MODEL_DIR}/solublempnn_v_48_010.pt",
    ),
    ModelTypeOptions.SolubleMPNN_MediumNoise: (
        "soluble_mpnn",
        f"{MODEL_DIR}/solublempnn_v_48_020.pt",
    ),
    ModelTypeOptions.SolubleMPNN_HighNoise: (
        "soluble_mpnn",
        f"{MODEL_DIR}/solublempnn_v_48_030.pt",
    ),
    ModelTypeOptions.PerResidueLabelMembraneMPNN: (
        "per_residue_label_membrane_mpnn",
        f"{MODEL_DIR}/per_residue_label_membrane_mpnn_v_48_020.pt",
    ),
    ModelTypeOptions.GlobalLabelMembraneMPNN: (
        "global_label_membrane_mpnn",
        f"{MODEL_DIR}/global_label_membrane_mpnn_v_48_020.pt",
    ),
}


class LigandMPNNRunConfig(BaseModel):
    sif_path: str = Field(default="", description="SIF镜像路径，留空则自动使用系统配置的路径")
    entrypoint: str = Field(
        default="python /root/LigandMPNN/ligandMPNN_app/core/main.py ",
        description="执行入口点",
    )
    input_dir_host: str = Field(
        default="/gene/home/dsz/enzyme_apptainer/ligandmpnn/input", description="主机输入目录"
    )
    output_dir_host: str = Field(
        default="/gene/home/dsz/enzyme_apptainer/ligandmpnn/output",
        description="主机输出目录",
    )
    input_dir_container: str = Field(default="/opt/input", description="容器内输入目录")
    output_dir_container: str = Field(default="/opt/output", description="容器内输出目录")
    use_gpu: bool = Field(default=True, description="是否使用GPU")


class RunConfig(BaseModel):
    ligandmpnn: LigandMPNNRunConfig = Field(default_factory=LigandMPNNRunConfig)


def get_input_pdb_files(input_dir: str) -> List[str]:
    """
    获取输入目录中的所有PDB文件名称列表

    Args:
        input_dir: 输入目录路径

    Returns:
        List[str]: PDB文件名列表
    """
    pdb_files = []
    if os.path.exists(input_dir):
        for file in os.listdir(input_dir):
            if file.lower().endswith(".pdb"):
                pdb_files.append(file)
    return pdb_files


def adapter(model: Config, run_config: RunConfig) -> dict:
    """
    将LigandMPNNModel对象转换为apptainer命令行字符串和sbatch脚本

    Args:
        model: Config配置对象
        run_config: RunConfig配置对象

    Returns:
        dict: 包含命令行和脚本路径的字典
    """
    # 提取配置信息
    ligandmpnn_run_config = run_config.ligandmpnn

    # 处理SIF路径 - 如果未指定，则使用get_sif_path获取
    if not ligandmpnn_run_config.sif_path:
        ligandmpnn_run_config.sif_path = get_sif_path("ligandmpnn")
        if not ligandmpnn_run_config.sif_path:
            raise ValueError("未找到LigandMPNN的SIF文件路径，请在配置中指定或确保SIF_PATHS中包含该应用")

    # 构建挂载参数
    input_mount = f"--mount type=bind,source={shlex.quote(ligandmpnn_run_config.input_dir_host)},destination={shlex.quote(ligandmpnn_run_config.input_dir_container)}"
    output_mount = f"--mount type=bind,source={shlex.quote(ligandmpnn_run_config.output_dir_host)},destination={shlex.quote(ligandmpnn_run_config.output_dir_container)}"

    # 检测输入目录中的PDB文件
    input_pdbs = get_input_pdb_files(ligandmpnn_run_config.input_dir_host)
    input_file = model.input_file

    # 如果未指定输入文件但目录中有PDB文件，则使用第一个PDB文件
    if (input_file == "input.pdb") and (input_pdbs):
        input_file = input_pdbs[0]

    # 获取PDB文件名（无扩展名）用于创建输出目录
    pdb_name = Path(input_file).stem
    output_folder = f"{pdb_name}"

    # 获取模型类型和检查点
    try:
        model_type, model_ckpt = MODEL_CHECKPOINTS[model.advanced_setting.model_type]
    except KeyError:
        raise ValueError(f"不支持的模型类型: {model.advanced_setting.model_type}")

    # 构建命令行参数列表
    cmd_args = []
    cmd_args.append(f"--model_type {shlex.quote(model_type)}")
    cmd_args.append(f"--checkpoint_{model_type} {shlex.quote(model_ckpt)}")
    cmd_args.append(
        f"--pdb_path {shlex.quote(f'{ligandmpnn_run_config.input_dir_container}/{input_file}')}"
    )
    cmd_args.append(
        f"--out_folder {shlex.quote(f'{ligandmpnn_run_config.output_dir_container}/{output_folder}')}"
    )
    cmd_args.append(f"--number_of_batches {model.design_setting.design_num}")
    cmd_args.append(f"--temperature {model.design_setting.temp}")
    cmd_args.append(f"--seed {model.advanced_setting.seed}")

    # 创建输出目录
    os.makedirs(
        f"{ligandmpnn_run_config.output_dir_host}/{output_folder}", exist_ok=True
    )

    # 添加可选参数
    if model.design_setting.chains_to_design:
        cmd_args.append(
            f"--chains_to_design {shlex.quote(model.design_setting.chains_to_design)}"
        )

    if model.design_setting.chains_to_parse:
        cmd_args.append(
            f"--parse_these_chains_only {shlex.quote(model.design_setting.chains_to_parse)}"
        )

    if model.design_setting.selected_residues:
        formatted_positions = model.design_setting.format_fixed_position()
        if model.design_setting.redesign_selection == SelectedResidueOptions.Fix:
            cmd_args.append(f"--fixed_residues {shlex.quote(formatted_positions)}")
        else:
            cmd_args.append(f"--redesigned_residues {shlex.quote(formatted_positions)}")

    if model.advanced_setting.omit_AA:
        cmd_args.append(f"--omit_AA {shlex.quote(model.advanced_setting.omit_AA)}")

    if model.advanced_setting.omit_AA_per_residue:
        # 在容器内处理omit_AA_per_residue.json文件
        json_path = f"{ligandmpnn_run_config.output_dir_container}/{output_folder}/omit_AA_per_residue.json"
        cmd_args.append(f"--omit_AA_per_residue {shlex.quote(json_path)}")

    if model.advanced_setting.lm_use_sc_context:
        cmd_args.append("--ligand_mpnn_use_side_chain_context 1")

    if model.packing_setting.pack_side_chains:
        cmd_args.append("--pack_side_chains 1")
        cmd_args.append(
            "--checkpoint_path_sc /root/LigandMPNN/model_params/ligandmpnn_sc_v_32_002_16.pt"
        )

        if model.packing_setting.number_of_packs_per_design != 0:
            cmd_args.append(
                f"--number_of_packs_per_design {model.packing_setting.number_of_packs_per_design}"
            )

        if model.packing_setting.repack_everything:
            cmd_args.append("--repack_everything 1")

    # 构建完整命令
    gpu_flag = "--nv" if ligandmpnn_run_config.use_gpu else ""
    run_args = [
        f"apptainer exec --writable-tmpfs {gpu_flag} --dns 8.8.8.8",
        input_mount,
        output_mount,
        shlex.quote(ligandmpnn_run_config.sif_path),
        ligandmpnn_run_config.entrypoint,
    ]

    all_args = " ".join(run_args) + " " + " ".join(cmd_args)

    # 使用通用工具生成sbatch脚本
    script_path = generate_sbatch_script(
        cmd=all_args,
        workspace_path=ligandmpnn_run_config.output_dir_host,
        job_name=f"ligandmpnn_{pdb_name}",
        use_gpu=ligandmpnn_run_config.use_gpu,
    )

    return {"cmd": all_args, "script_path": script_path, "output_folder": output_folder}


if __name__ == "__main__":

    # 创建测试配置
    design_setting = DesignSettings(
        chains_to_design="A,B",
        chains_to_parse="A,B,C",
        design_num=5,
        temp=0.1,
    )

    advanced_setting = AdvancedSettings(
        model_type=ModelTypeOptions.LigandMPNN_VeryLowNoise,
        seed=42,
        omit_AA="CW",
        lm_use_sc_context=True,
    )

    packing_setting = PackingSettings(
        pack_side_chains=True,
        number_of_packs_per_design=3,
        repack_everything=False,
    )

    # 创建LigandMPNNModel实例
    model = Config(
        design_setting=design_setting,
        advanced_setting=advanced_setting,
        packing_setting=packing_setting,
    )

    # 创建RunConfig实例
    run_config = RunConfig()

    # 生成命令
    result = adapter(model, run_config)

    # 输出命令和脚本路径
    with open("apptainer_args.txt", "w", encoding="utf-8") as f:
        f.write(result["cmd"])

    print(f"命令行: {result['cmd']}")
    print(f"脚本路径: {result['script_path']}")
    print(f"输出文件夹: {result['output_folder']}")
