"""
UI 样式系统 — 暗色专业交易主题
"""
import streamlit as st
from typing import Optional


# ═════════════════════════════════════════════════════════
#  调色板 — 暗色主题
# ═════════════════════════════════════════════════════════
PALETTE = {
    "bg_main":      "#0F1117",
    "bg_card":      "#1A1D26",
    "bg_card_hover": "#222738",
    "bg_sidebar":   "#13151E",
    "border":       "#2D3340",
    "border_focus": "#D4A460",
    "text_primary": "#E4E7EB",
    "text_secondary": "#9CA3AF",
    "text_muted":   "#6B7280",
    "accent_gold":  "#D4A460",
    "accent_copper": "#E8A840",
    "success":      "#22C55E",
    "danger":       "#EF4444",
    "warning":      "#F59E0B",
    "info":         "#60A5FA",
    "shadow":       "0 1px 3px rgba(0,0,0,0.2), 0 1px 2px rgba(0,0,0,0.15)",
    "shadow_hover": "0 4px 12px rgba(0,0,0,0.3)",
    "gradient_header": "linear-gradient(90deg, #D4A460, #E8A840)",
}

# ═════════════════════════════════════════════════════════
#  CSS 样式表
# ═════════════════════════════════════════════════════════
CSS = """
/* ── 全局基础 ── */
.stApp {
    background: #F5F6FA;
}
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

/* ── 标题 ── */
h1, h2, h3, h4 {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: -0.3px;
}
h1 {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #1A1D26 !important;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid #E2E5EE;
    margin-bottom: 1rem;
}
h2 { font-size: 1.25rem !important; color: #1A1D26 !important; font-weight: 600 !important; }
h3 { font-size: 1.05rem !important; color: #374151 !important; font-weight: 600 !important; }
h4 { font-size: 0.95rem !important; color: #6B7280 !important; font-weight: 500 !important; }

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {
    background: #FAFBFC;
    border-right: 1px solid #E2E5EE;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

/* ── 导航按钮 ── */
div[role="radiogroup"] > label {
    background: #FFFFFF !important;
    border: 1px solid #E2E5EE !important;
    border-radius: 8px !important;
    margin-bottom: 2px !important;
    padding: 10px 14px !important;
    color: #6B7280 !important;
    transition: all 0.2s !important;
    font-size: 0.9rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
div[role="radiogroup"] > label:hover {
    background: #F0F4FF !important;
    border-color: #C8923A50 !important;
    color: #374151 !important;
}
div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, #FFF8F0, #FFF3E5) !important;
    border-color: #C8923A !important;
    color: #C8923A !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(200,146,58,0.12);
}

/* ── KPI 卡片 ── */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E5EE;
    border-radius: 10px;
    padding: 16px 20px;
    transition: all 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
[data-testid="stMetric"]:hover {
    border-color: #C8923A40;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    transform: translateY(-1px);
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #1A1D26 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* ── 卡片容器 ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E5EE !important;
    border-radius: 10px !important;
    padding: 4px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ── 进度条 ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #C8923A, #D4832A) !important;
    border-radius: 4px;
    height: 6px !important;
}
.stProgress {
    background: #E5E7EB !important;
    border-radius: 4px;
    height: 6px !important;
}

/* ── 按钮 ── */
.stButton > button {
    background: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    font-size: 0.89rem !important;
}
.stButton > button:hover {
    border-color: #C8923A !important;
    color: #C8923A !important;
    box-shadow: 0 2px 8px rgba(200,146,58,0.1);
}
/* Primary 按钮 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #C8923A, #B07E30) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(200,146,58,0.3);
    transform: translateY(-1px);
}

/* ── 表格 ── */
.stDataFrame table {
    border-collapse: separate;
    border-spacing: 0;
}
.stDataFrame thead th {
    background: #F9FAFB !important;
    color: #6B7280 !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 2px solid #E2E5EE !important;
    padding: 10px 14px !important;
}
.stDataFrame tbody td {
    background: #FFFFFF !important;
    color: #374151 !important;
    font-size: 0.85rem;
    border-bottom: 1px solid #F3F4F6 !important;
    padding: 8px 14px !important;
}
.stDataFrame tbody tr:hover td {
    background: #F9FAFB !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: #F9FAFB;
    border: 1px solid #E2E5EE;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    color: #6B7280;
    font-weight: 500;
    font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF;
    color: #C8923A !important;
    border-color: #C8923A !important;
    border-bottom: 2px solid #C8923A !important;
    font-weight: 600;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #F9FAFB !important;
    border: 1px solid #E2E5EE !important;
    border-radius: 8px !important;
    color: #6B7280 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.streamlit-expanderHeader:hover {
    border-color: #C8923A50 !important;
    color: #C8923A !important;
}

/* ── Select / Input ── */
.stSelectbox [data-baseweb="select"] > div,
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
    color: #1A1D26 !important;
    font-size: 0.9rem;
}
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #C8923A !important;
    box-shadow: 0 0 0 3px rgba(200,146,58,0.1);
}

/* ── 消息框 ── */
.stSuccess {
    background: #ECFDF5 !important;
    border: 1px solid #A7F3D0 !important;
    border-radius: 8px !important;
    color: #065F46 !important;
}
.stWarning {
    background: #FFFBEB !important;
    border: 1px solid #FDE68A !important;
    border-radius: 8px !important;
    color: #92400E !important;
}
.stError {
    background: #FEF2F2 !important;
    border: 1px solid #FECACA !important;
    border-radius: 8px !important;
    color: #991B1B !important;
}
.stInfo {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    color: #1E40AF !important;
}

/* ── Divider ── */
hr {
    border-color: #E2E5EE !important;
    margin: 1.2rem 0 !important;
}

/* ── Captions ── */
.stCaption {
    color: #9CA3AF !important;
    font-size: 0.78rem !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #C8923A !important;
    border: 2px solid #FFFFFF !important;
}
.stSlider [data-baseweb="slider"] > div > div {
    background: #C8923A !important;
}

/* ── 滚动条 ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F5F6FA; }
::-webkit-scrollbar-thumb {
    background: #D1D5DB;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }

/* ── Spinner ── */
.stSpinner > div {
    border-color: #C8923A transparent transparent transparent !important;
}

/* ═══════════════════════════════════════════════════════
   响应式 — 移动端 & 平板适配
   ═══════════════════════════════════════════════════════ */

/* ── 平板 (< 768px) ── */
@media (max-width: 768px) {
    /* 全局 */
    .main .block-container {
        padding: 0.8rem 0.6rem !important;
    }

    /* 标题 */
    h1 { font-size: 1.25rem !important; padding-bottom: 0.3rem; margin-bottom: 0.6rem; }
    h2 { font-size: 1.05rem !important; }
    h3 { font-size: 0.95rem !important; }
    h4 { font-size: 0.85rem !important; }

    /* 侧边栏 */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 85vw !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 0.5rem 0.8rem !important;
    }

    /* 导航 — 加大触控区 */
    div[role="radiogroup"] > label {
        padding: 12px 14px !important;
        font-size: 0.95rem !important;
        min-height: 44px;
        display: flex !important;
        align-items: center;
    }

    /* KPI 卡片 */
    [data-testid="stMetric"] {
        padding: 10px 12px !important;
        border-radius: 8px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }

    /* 按钮 — 全宽 + 大触控区 */
    .stButton > button {
        padding: 10px 16px !important;
        min-height: 44px;
        font-size: 0.9rem !important;
        width: 100% !important;
    }

    /* 表格 — 横向滚动 */
    .stDataFrame {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }
    .stDataFrame thead th {
        font-size: 0.7rem !important;
        padding: 6px 8px !important;
        white-space: nowrap;
    }
    .stDataFrame tbody td {
        font-size: 0.78rem !important;
        padding: 6px 8px !important;
    }

    /* Tabs — 全宽 */
    .stTabs [data-baseweb="tab"] {
        padding: 10px 12px !important;
        font-size: 0.82rem !important;
        min-height: 44px;
        flex: 1;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        gap: 2px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        padding: 10px 12px !important;
        font-size: 0.82rem !important;
        min-height: 44px;
    }

    /* Select / Input */
    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput input, .stNumberInput input {
        font-size: 0.95rem !important;
        min-height: 44px;
        padding: 8px 12px !important;
    }
    .stTextArea textarea {
        font-size: 0.95rem !important;
    }

    /* Divider */
    hr {
        margin: 0.8rem 0 !important;
    }

    /* Plotly 图表 */
    .js-plotly-plot {
        max-width: 100% !important;
    }

    /* 快讯卡片 */
    .stCaption {
        font-size: 0.72rem !important;
    }
}

/* ── 手机 (< 480px) ── */
@media (max-width: 480px) {
    .main .block-container {
        padding: 0.4rem 0.3rem !important;
    }

    h1 { font-size: 1.15rem !important; }
    h2 { font-size: 0.95rem !important; }
    h3 { font-size: 0.88rem !important; }

    /* 侧边栏更窄 */
    [data-testid="stSidebar"] {
        min-width: 240px !important;
        max-width: 90vw !important;
    }

    /* KPI 进一步缩小 */
    [data-testid="stMetric"] {
        padding: 8px 10px !important;
        border-radius: 6px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1rem !important;
    }

    /* 导航 */
    div[role="radiogroup"] > label {
        padding: 12px 12px !important;
        font-size: 0.88rem !important;
    }

    /* 表格 */
    .stDataFrame thead th { font-size: 0.65rem !important; }
    .stDataFrame tbody td { font-size: 0.72rem !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        padding: 8px 8px !important;
        font-size: 0.75rem !important;
        white-space: nowrap;
    }
}
"""


def inject_css():
    """注入全局 CSS"""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
#  UI 组件工厂
# ═════════════════════════════════════════════════════════

def kpi_card(label: str, value: str, delta: str = None, delta_color: str = "normal",
             icon: str = "", col=None):
    """统一 KPI 卡片"""
    target = col or st
    if delta and delta_color == "normal":
        if delta.startswith("-"):
            delta_color = "inverse"
    target.metric(
        f"{icon} {label}" if icon else label,
        value, delta, delta_color=delta_color,
    )


def section_header(title: str, subtitle: str = "", icon: str = ""):
    """段落标题"""
    icon_str = f"{icon} " if icon else ""
    st.markdown(f"### {icon_str}{title}")
    if subtitle:
        st.caption(subtitle)


def confidence_indicator(confidence: float):
    """信心指数展示"""
    n_filled = int(confidence * 20)
    bar = "█" * n_filled + "░" * max(0, 20 - n_filled)
    if confidence >= 0.75:
        tag = '<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        tag += 'background:#ECFDF5;color:#065F46;font-size:0.75rem;font-weight:600;">高信心</span>'
    elif confidence >= 0.5:
        tag = '<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        tag += 'background:#FFFBEB;color:#92400E;font-size:0.75rem;font-weight:600;">中信度</span>'
    else:
        tag = '<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        tag += 'background:#FEF2F2;color:#991B1B;font-size:0.75rem;font-weight:600;">低信心</span>'
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">'
        f'<span style="font-family:monospace;font-size:0.82rem;color:#374151;">{bar}</span>'
        f'{tag}</div>',
        unsafe_allow_html=True,
    )
    st.progress(confidence)


def empty_state(message: str, icon: str = "📭"):
    """空状态占位（移动端自适应）"""
    st.markdown(
        f'<div style="text-align:center;padding:30px 16px;color:#9CA3AF;">'
        f'<div style="font-size:2rem;margin-bottom:8px;">{icon}</div>'
        f'<div style="font-size:0.88rem;">{message}</div></div>',
        unsafe_allow_html=True,
    )


def mobile_kpi_row(items: list, cols_per_row: int = 2):
    """移动端友好的 KPI 行：自动按 cols_per_row 分组渲染
    items: [(label, value, delta, delta_color, icon), ...]
    """
    for i in range(0, len(items), cols_per_row):
        chunk = items[i:i+cols_per_row]
        cols = st.columns(len(chunk))
        for j, item in enumerate(chunk):
            label, value = item[0], item[1]
            delta = item[2] if len(item) > 2 else None
            delta_color = item[3] if len(item) > 3 else "normal"
            icon = item[4] if len(item) > 4 else ""
            kpi_card(label, value, delta, delta_color, icon, col=cols[j])


def mobile_bottom_nav():
    """移动端底部导航提示（通过 JS 检测并显示）"""
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {
            .mobile-nav-hint {
                display: flex !important;
            }
        }
        .mobile-nav-hint {
            display: none;
            position: fixed;
            bottom: 0; left: 0; right: 0;
            background: #FFFFFF;
            border-top: 1px solid #E2E5EE;
            padding: 6px 12px;
            z-index: 999;
            font-size: 0.68rem;
            color: #9CA3AF;
            text-align: center;
            pointer-events: none;
        }
        </style>
        <div class="mobile-nav-hint">
            ☰ 左上角菜单切换页面 · 下拉刷新行情
        </div>
        """,
        unsafe_allow_html=True,
    )


def factor_scores_card(ta: dict):
    """多因子评分卡片（移动端自适应紧凑版）"""
    rows = [
        ("📊", "技术面", [
            ("趋势", ta.get('trend_score', '-')),
            ("动量", ta.get('momentum_score', '-')),
            ("波动", ta.get('volatility_score', '-')),
            ("支撑", ta.get('sr_score', '-')),
            ("量价", ta.get('volume_score', '-')),
            ("状态", ta.get('regime_score', '-')),
        ]),
        ("🌍", "基本面", [
            ("季节性", ta.get('seasonal_score', '-')),
            ("联动性", ta.get('correlation_score', '-')),
            ("宏观", ta.get('macro_score', '-')),
        ]),
        ("🏭", "运营面", [
            ("运营", ta.get('operational_score', '-')),
            ("风控", ta.get('risk_score', '-')),
        ]),
    ]
    composite = ta.get('composite_score', 0)
    if isinstance(composite, (int, float)):
        if composite >= 70:
            comp_color = "#10B981"; comp_bg = "#ECFDF5"
        elif composite >= 45:
            comp_color = "#F59E0B"; comp_bg = "#FFFBEB"
        else:
            comp_color = "#EF4444"; comp_bg = "#FEF2F2"
    else:
        comp_color = "#6B7280"; comp_bg = "#F9FAFB"

    html_parts = [
        '<div style="background:#F9FAFB;border:1px solid #E2E5EE;border-radius:10px;padding:12px 14px;margin:6px 0;">',
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">'
        f'<span style="background:{comp_bg};color:{comp_color};padding:3px 10px;border-radius:6px;'
        f'font-size:0.88rem;font-weight:700;">综合 {composite}/100</span>'
        f'</div>',
    ]
    for icon, title, items in rows:
        badges = " ".join(
            f'<span style="background:#FFFFFF;color:#374151;border:1px solid #E2E5EE;'
            f'padding:1px 6px;border-radius:4px;font-size:0.7rem;margin:1px;'
            f'white-space:nowrap;display:inline-block;">{k}:{v}</span>'
            for k, v in items
        )
        html_parts.append(
            f'<div style="display:flex;align-items:flex-start;gap:4px;margin:4px 0;flex-wrap:wrap;">'
            f'<span style="font-size:0.75rem;flex-shrink:0;color:#C8923A;min-width:40px;font-weight:500;">'
            f'{icon} {title}</span>'
            f'<span style="flex:1;min-width:0;">{badges}</span></div>'
        )
    html_parts.append('</div>')
    st.markdown("\n".join(html_parts), unsafe_allow_html=True)


def recommendation_card(rec: dict, index: int, action_type: str):
    """推荐卡片（移动端自适应）"""
    ta = rec.get('trend_analysis', {})
    confidence = rec.get('confidence', 0)
    is_buy = action_type == "buy"

    accent = "#10B981" if is_buy else "#EF4444"
    accent_bg = "#ECFDF5" if is_buy else "#FEF2F2"
    emoji = "🟢" if is_buy else "🔴"

    price = rec.get('current_price', 0)
    sl = rec.get('stop_loss', 0)
    tp = rec.get('take_profit', 0)
    qty = rec.get('suggested_quantity_kg', 0)
    profit = rec.get('expected_profit_pct', 0)

    profit_line = f'<span>💰 预期利润: <b style="color:{accent};">{profit:+.1f}%</b></span>' if not is_buy else ''

    html = f"""
    <div class="rec-card" style="
        background:#FFFFFF;
        border:1px solid #E2E5EE;
        border-left:4px solid {accent};
        border-radius:10px;
        padding:14px 14px;
        margin:8px 0;
        transition:all 0.2s;
        box-shadow:0 1px 3px rgba(0,0,0,0.04);
    ">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                <span style="font-size:0.72rem;color:#9CA3AF;">#{index}</span>
                <span style="font-size:1rem;font-weight:700;color:#1A1D26;">
                    {rec['metal_type']}
                </span>
                <span style="background:{accent_bg};color:{accent};padding:2px 8px;
                             border-radius:10px;font-size:0.72rem;font-weight:600;white-space:nowrap;">
                    {emoji} {'买入' if is_buy else '卖出'}
                </span>
            </div>
            <span style="font-size:1.1rem;font-weight:700;color:#1A1D26;">
                ¥{price:,.0f}
            </span>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:0.78rem;color:#6B7280;">
            <span>🎯 止损: <b style="color:#EF4444;">¥{sl:,.0f}</b></span>
            <span>🏁 止盈: <b style="color:#10B981;">¥{tp:,.0f}</b></span>
            <span>📦 建议量: <b style="color:#C8923A;">{qty:,.0f}kg</b></span>
            {profit_line}
        </div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)
    confidence_indicator(confidence)


def plotly_theme() -> dict:
    """统一的 Plotly 图表主题（浅色）"""
    return dict(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F9FAFB",
        font=dict(color="#6B7280", size=12),
        title_font=dict(color="#1A1D26", size=14),
        legend=dict(font=dict(color="#6B7280")),
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(
            gridcolor="#E5E7EB", zerolinecolor="#E5E7EB",
            linecolor="#D1D5DB", tickfont=dict(color="#9CA3AF"),
        ),
        yaxis=dict(
            gridcolor="#E5E7EB", zerolinecolor="#E5E7EB",
            linecolor="#D1D5DB", tickfont=dict(color="#9CA3AF"),
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(color="#6B7280"),
            title_font=dict(color="#6B7280"),
        ),
    )


def styled_plotly(fig):
    """给 plotly figure 应用统一浅色主题"""
    theme = plotly_theme()
    fig.update_layout(**theme)
    return fig
