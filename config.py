"""
有色金属回收倒卖AI系统 - 配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库配置
DATABASE_URL = f"sqlite:///{BASE_DIR}/metal_trading.db"

# 支持的有色金属类型及其代号
# shfe_code: 上海期货交易所合约代码
# futures_code: akshare期货代码 (主力连续合约)
METAL_TYPES = {
    "铜":    {"symbol": "CU", "shfe_code": "CU",  "futures_code": "CU0", "unit": "元/吨",   "is_scrap": False, "base_price": 72000, "volatility": 0.012},
    "铝":    {"symbol": "AL", "shfe_code": "AL",  "futures_code": "AL0", "unit": "元/吨",   "is_scrap": False, "base_price": 19500, "volatility": 0.010},
    "锌":    {"symbol": "ZN", "shfe_code": "ZN",  "futures_code": "ZN0", "unit": "元/吨",   "is_scrap": False, "base_price": 22500, "volatility": 0.015},
    "铅":    {"symbol": "PB", "shfe_code": "PB",  "futures_code": "PB0", "unit": "元/吨",   "is_scrap": False, "base_price": 16500, "volatility": 0.008},
    "镍":    {"symbol": "NI", "shfe_code": "NI",  "futures_code": "NI0", "unit": "元/吨",   "is_scrap": False, "base_price": 135000, "volatility": 0.022},
    "锡":    {"symbol": "SN", "shfe_code": "SN",  "futures_code": "SN0", "unit": "元/吨",   "is_scrap": False, "base_price": 240000, "volatility": 0.018},
    "黄金":  {"symbol": "AU", "shfe_code": "AU",  "futures_code": "AU0", "unit": "元/克",   "is_scrap": False, "base_price": 560,   "volatility": 0.007},
    "白银":  {"symbol": "AG", "shfe_code": "AG",  "futures_code": "AG0", "unit": "元/千克", "is_scrap": False, "base_price": 7200,  "volatility": 0.014},
    "废铜":  {"symbol": "SCRAP_CU", "shfe_code": None, "futures_code": None, "unit": "元/吨",   "is_scrap": True,  "ref_metal": "铜", "ratio": 0.65, "base_price": 46800, "volatility": 0.018},
    "废铝":  {"symbol": "SCRAP_AL", "shfe_code": None, "futures_code": None, "unit": "元/吨",   "is_scrap": True,  "ref_metal": "铝", "ratio": 0.66, "base_price": 12800, "volatility": 0.012},
    "废不锈钢": {"symbol": "SCRAP_SS", "shfe_code": None, "futures_code": None, "unit": "元/吨", "is_scrap": True,  "ref_metal": "镍", "ratio": 0.08, "base_price": 9800,  "volatility": 0.010},
}

# 数据源配置
DATA_SOURCE = {
    "primary": "akshare",     # 主数据源: akshare (上海期货交易所)
    "fallback": "simulated",  # 备用数据源: simulated (模拟数据)
    "cache_minutes": 5,       # 数据缓存时间(分钟)
}

# 价格更新频率（分钟）
PRICE_UPDATE_INTERVAL = 30

# 价格告警阈值（价格变动百分比）
ALERT_THRESHOLD_PCT = 2.0

# 推荐系统参数
RECOMMENDATION = {
    "short_term_window": 7,      # 短期分析窗口（天）
    "medium_term_window": 30,    # 中期分析窗口（天）
    "long_term_window": 90,      # 长期分析窗口（天）
    "volatility_threshold": 0.03, # 波动率阈值
    "profit_margin_min": 0.05,   # 最低建议利润率5%
    "profit_margin_target": 0.10, # 目标利润率10%
    "inventory_weight": 0.20,    # 库存因子权重（组合总分中的占比）
    "macro_weight": 0.12,        # 宏观/基本面因子权重
    "operational_weight": 0.08,  # 运营效率因子权重
    "max_single_exposure_pct": 0.30,  # 单品种最大敞口30%
    "max_drawdown_pct": 0.15,    # 最大回撤容忍15%
    "storage_cost_monthly_pct": 0.003,  # 仓储月成本0.3%
    "capital_cost_annual": 0.05, # 资金年化成本5%
}

# ── 多因子评分权重 v3.2（技术面 + 基本面 + 运营面 + 背离检测） ──
FACTOR_WEIGHTS = {
    # 技术面权重（合计 46% → 趋势检测 + 反转信号）
    "trend":       0.13,   # 多周期趋势
    "momentum":    0.10,   # RSI + MACD + 随机
    "volatility":  0.06,   # ATR + 布林带
    "sr_levels":   0.06,   # 支撑阻力
    "volume":      0.05,   # 量价配合
    "regime":      0.05,   # 市场状态
    "divergence":  0.12,   # 🆕 v3.2 RSI+MACD背离检测（最强反转信号）
    # 基本面权重（合计 31%）
    "seasonal":    0.06,   # 🆕 季节性规律
    "correlation": 0.05,   # 🆕 跨品种联动/对冲
    "macro_bias":  0.07,   # 🆕 宏观环境偏差（LLM驱动）
    "timeframe":   0.07,   # 🆕 多周期趋势一致性
    "supply_demand": 0.05, # 🆕 供需基本面代理
    # 运营面权重（合计 13%）
    "operational": 0.08,   # 🆕 运营效率（周转率/资金成本/仓储）
    "risk_mgmt":   0.05,   # 🆕 风险管理（集中度/回撤/流动性）
}

# ── 金属季节性因子 (1月~12月，相对基准1.0) ──
# 基于历史统计：Q1节后复工需求、Q2淡季、Q3金九银十、Q4冬储备货
METAL_SEASONALITY = {
    "铜":   [1.02, 1.01, 1.00, 0.98, 0.97, 0.96, 0.98, 0.99, 1.01, 1.02, 1.01, 1.00],
    "铝":   [1.01, 0.99, 1.00, 1.01, 0.98, 0.97, 0.98, 0.99, 1.00, 1.01, 1.00, 0.99],
    "锌":   [1.01, 1.00, 1.02, 0.99, 0.97, 0.96, 0.97, 0.98, 1.00, 1.01, 1.01, 1.00],
    "铅":   [1.00, 1.00, 1.01, 0.99, 0.98, 1.00, 1.01, 1.00, 0.99, 0.98, 0.99, 1.00],
    "镍":   [1.02, 1.01, 0.99, 0.97, 0.96, 0.97, 0.99, 1.00, 1.01, 1.02, 1.01, 1.00],
    "锡":   [1.01, 1.00, 0.99, 0.98, 0.97, 0.98, 0.99, 1.00, 1.01, 1.02, 1.01, 1.00],
    "黄金": [1.03, 1.01, 0.99, 0.98, 0.99, 0.97, 0.99, 1.01, 1.02, 1.01, 1.00, 1.02],
    "白银": [1.02, 1.01, 1.00, 0.98, 0.99, 0.97, 0.98, 1.00, 1.01, 1.02, 1.01, 1.01],
}
# 废金属季节性跟随对应精炼金属

# ── 跨品种相关性矩阵（简化版，基于历史经验） ──
# 正值=同涨同跌，负值=对冲关系
METAL_CORRELATION = {
    "铜":   {"铜": 1.0, "铝": 0.65, "锌": 0.55, "铅": 0.35, "镍": 0.55, "锡": 0.45,
              "黄金": -0.15, "白银": 0.10},
    "铝":   {"铜": 0.65, "铝": 1.0, "锌": 0.45, "铅": 0.30, "镍": 0.40, "锡": 0.35,
              "黄金": -0.10, "白银": 0.05},
    "锌":   {"铜": 0.55, "铝": 0.45, "锌": 1.0, "铅": 0.55, "镍": 0.40, "锡": 0.30,
              "黄金": -0.10, "白银": 0.10},
    "铅":   {"铜": 0.35, "铝": 0.30, "锌": 0.55, "铅": 1.0, "镍": 0.25, "锡": 0.20,
              "黄金": -0.05, "白银": 0.05},
    "镍":   {"铜": 0.55, "铝": 0.40, "锌": 0.40, "铅": 0.25, "镍": 1.0, "锡": 0.50,
              "黄金": -0.05, "白银": 0.10},
    "锡":   {"铜": 0.45, "铝": 0.35, "锌": 0.30, "铅": 0.20, "镍": 0.50, "锡": 1.0,
              "黄金": 0.0, "白银": 0.10},
    "黄金": {"铜": -0.15, "铝": -0.10, "锌": -0.10, "铅": -0.05, "镍": -0.05, "锡": 0.0,
              "黄金": 1.0, "白银": 0.80},
    "白银": {"铜": 0.10, "铝": 0.05, "锌": 0.10, "铅": 0.05, "镍": 0.10, "锡": 0.10,
              "黄金": 0.80, "白银": 1.0},
}

# 通知配置（支持企业微信、钉钉Webhook等）
NOTIFICATION = {
    "enabled": False,
    "webhook_url": "",  # 钉钉/企业微信 Webhook地址
    "type": "dingtalk", # dingtalk / wecom / feishu
}

# 是否强制使用模拟数据
USE_MOCK_DATA = False

# ═════════════════════════════════════════════════════════
#  DeepSeek LLM配置（优先级: 环境变量 > Streamlit Secrets > 默认值）
# ═════════════════════════════════════════════════════════

def _get_llm_config():
    """
    从环境变量 / Streamlit Secrets 读取 LLM 配置
    优先级: os.environ > st.secrets > 硬编码默认值
    """
    import os

    # 尝试从 Streamlit Secrets 读取
    secrets = {}
    try:
        import streamlit as st
        secrets = st.secrets.get("llm", {})
    except Exception:
        pass

    # 环境变量优先，其次 secrets，最后默认值
    api_key = (
        os.environ.get("LLM_API_KEY") or
        os.environ.get("DEEPSEEK_API_KEY") or
        secrets.get("api_key", "")
    )

    return {
        "enabled": bool(api_key),
        "api_key": api_key,
        "base_url": (
            os.environ.get("LLM_BASE_URL") or
            secrets.get("base_url", "https://api.deepseek.com")
        ),
        "model": (
            os.environ.get("LLM_MODEL") or
            secrets.get("model", "deepseek-chat")
        ),
        "max_tokens": int(
            os.environ.get("LLM_MAX_TOKENS") or
            secrets.get("max_tokens", 1024)
        ),
        "temperature": float(
            os.environ.get("LLM_TEMPERATURE") or
            secrets.get("temperature", 0.3)
        ),
    }

LLM_CONFIG = _get_llm_config()

# 数据存储路径
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
