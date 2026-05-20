"""
有色金属回收倒卖AI系统 - 启动脚本
"""
import subprocess
import sys
import os
from pathlib import Path


def load_env():
    """加载 .env 文件中的环境变量"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def setup_venv():
    """设置虚拟环境"""
    venv_dir = Path(__file__).parent / "venv"

    if not venv_dir.exists():
        print("🔧 正在创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # 确定pip路径
    if os.name == "nt":
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"

    print("📦 安装依赖包...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt",
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"], check=True)

    print("✅ 环境准备完成！")
    return str(python_path)


def main():
    # 🔐 加载 .env 环境变量
    load_env()

    print("=" * 60)
    print("  🔩 有色金属回收倒卖AI系统")
    print("  Metal Recycling & Trading AI System v1.0")
    print("=" * 60)
    print()

    # 检查并设置虚拟环境
    python_exe = setup_venv()

    # 启动Streamlit
    print("\n🚀 正在启动Web界面...")
    print("📱 浏览器将自动打开 http://localhost:8501")
    print("💡 按 Ctrl+C 停止服务\n")

    app_path = Path(__file__).parent / "web" / "app.py"
    subprocess.run([
        python_exe, "-m", "streamlit", "run", str(app_path),
        "--server.port", "8501",
        "--browser.serverAddress", "localhost",
    ], check=True)


if __name__ == "__main__":
    main()
