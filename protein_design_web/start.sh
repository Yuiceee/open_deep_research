#!/bin/bash

# 蛋白质设计工作流 Web 应用启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示横幅
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                     🧬 蛋白质设计工作流 Web 应用                              ║"
    echo "║                    完整前后端集成版本                                        ║"
    echo "║                                                                              ║"
    echo "║  FastAPI + WebSocket + LogicFlow + LangGraph + MCP                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    PYTHON_CMD="/root/agent_project/open_deep_research/.venv/bin/python"
    export PYTHON_CMD

    if ! [ -x "$PYTHON_CMD" ]; then
        log_error "Python 未在 $PYTHON_CMD 找到或没有执行权限，请检查路径"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    log_info "Python版本: $PYTHON_VERSION"
    log_info "使用Python: $PYTHON_CMD"
}

# 检查依赖
check_dependencies() {
    log_info "检查项目依赖..."
    
    # 检查 protein_design 模块
    PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
    PROTEIN_DESIGN_PATH="$PROJECT_ROOT/src/protein_design"
    
    if [ ! -d "$PROTEIN_DESIGN_PATH" ]; then
        log_error "未找到 protein_design 模块路径: $PROTEIN_DESIGN_PATH"
        log_error "请确保在正确的项目根目录中运行此脚本"
        exit 1
    fi
    
    log_success "找到 protein_design 模块: $PROTEIN_DESIGN_PATH"
    
    # 检查关键的Python包
    "$PYTHON_CMD" -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from src.protein_design.graph import create_protein_design_graph" || {
        log_error "protein_design 模块导入失败，请检查环境配置"
        exit 1
    }
    
    log_success "protein_design 模块导入测试通过"
}

# 同步 Pixi 环境
# sync_pixi_env() {
#     log_info "同步 Pixi 环境..."
#     PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
#     (cd "$PROJECT_ROOT" && pixi install)
#     log_success "Pixi 环境已同步"
# }


# 设置环境变量
setup_environment() {
    log_info "设置环境变量..."
    
    # 设置OpenAI API Key（如果需要）
    if [[ -z "$OPENAI_API_KEY" ]]; then
        log_warning "未设置OPENAI_API_KEY环境变量"
        log_info "可以在运行前设置: export OPENAI_API_KEY=your-api-key"
    fi
    
    # 设置项目根目录
    export PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "Python路径已设置"
}

# 启动开发服务器
start_development_server() {
    log_info "启动开发服务器..."
    
    cd backend
    
    log_info "后端服务器启动中..."
    log_info "访问地址: http://localhost:8000"
    log_info "API文档: http://localhost:8000/docs"
    log_info "按 Ctrl+C 停止服务器"
    
    "$PYTHON_CMD" main.py
}

# 启动生产服务器
start_production_server() {
    log_info "启动生产服务器..."
    
    cd backend
    
    log_info "生产服务器启动中..."
    log_info "访问地址: http://localhost:8000"
    
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    # 测试后端API
    log_info "测试后端API连接..."
    "$PYTHON_CMD" -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from src.protein_design.utils import get_example_sequences
examples = get_example_sequences()
print('示例序列测试通过:', len(examples), '个序列')
"
    
    log_success "测试完成"
}

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  dev       启动开发服务器 (默认)"
    echo "  prod      启动生产服务器"
    echo "  test      运行测试"
    echo "  check     检查环境"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev      # 启动开发服务器"
    echo "  $0 prod     # 启动生产服务器"
    echo "  $0 test     # 运行测试"
    echo ""
    echo "环境变量:"
    echo "  OPENAI_API_KEY    OpenAI API密钥"
    echo "  PORT              服务器端口 (默认: 8000)"
    echo ""
}

# 清理函数
cleanup() {
    log_info "正在清理..."
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    show_banner
    
    case "${1:-dev}" in
        "dev")
            check_python
            # sync_pixi_env
            setup_environment
            check_dependencies
            start_development_server
            ;;
        "prod")
            check_python
            # sync_pixi_env
            setup_environment
            check_dependencies
            start_production_server
            ;;
        "test")
            check_python
            # sync_pixi_env
            setup_environment
            check_dependencies
            run_tests
            ;;
        "install")
            check_python
            # sync_pixi_env
            log_success "依赖安装完成"
            ;;
        "check")
            check_python
            # sync_pixi_env
            setup_environment
            check_dependencies
            log_success "环境检查通过"
            ;;
        "help")
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"