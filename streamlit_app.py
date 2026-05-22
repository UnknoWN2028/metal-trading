"""
Streamlit Cloud 入口文件
有色金属回收倒卖AI系统 v3.4

此文件用于 Streamlit Cloud 部署，本地开发可直接用:
    streamlit run streamlit_app.py
"""
import sys
import os
from pathlib import Path

# ── 加载 .env 文件（本地开发用，Streamlit Cloud 用 secrets.toml） ──
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _, _v = _line.partition("=")
            _k, _v = _k.strip(), _v.strip().strip('"').strip("'")
            if _k and _k not in os.environ:
                os.environ[_k] = _v

# 将项目根目录加入 import 路径
sys.path.insert(0, str(Path(__file__).parent))

# 直接执行 web/app.py 的内容（保持 __name__ == "__main__" 语义）
app_file = Path(__file__).parent / "web" / "app.py"
with open(app_file, "r", encoding="utf-8") as f:
    code = compile(f.read(), str(app_file), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(app_file)})
