"""
UI 样式系统 v4 — 专业金融交易主题
干净、层次分明、视觉引导强
"""
import streamlit as st
from typing import Optional


# ═════════════════════════════════════════════════════════
#  调色板 — 统一浅色金融主题
# ═════════════════════════════════════════════════════════
PALETTE = {
    # 背景
    "bg_main":       "#F3F4F8",
    "bg_card":       "#FFFFFF",
    "bg_card_alt":   "#F9FAFB",
    "bg_sidebar":    "#FAFBFC",
    "bg_section":    "#F6F7FB",
    # 文字
    "text_primary":  "#111827",
    "text_secondary":"#4B5563",
    "text_muted":    "#9CA3AF",
    # 边框
    "border":        "#E5E7EB",
    "border_light":  "#F3F4F6",
    "border_focus":  "#C8923A",
    # 主色 (金属金铜)
    "accent":        "#C8923A",
    "accent_hover":  "#B07E30",
    "accent_light":  "#FFF8F0",
    "accent_subtle": "rgba(200,146,58,0.08)",
    "gradient":      "linear-gradient(135deg, #C8923A, #D4832A)",
    # 语义色
    "success":       "#10B981",
    "success_bg":    "#ECFDF5",
    "success_text":  "#065F46",
    "danger":        "#EF4444",
    "danger_bg":     "#FEF2F2",
    "danger_text":   "#991B1B",
    "warning":       "#F59E0B",
    "warning_bg":    "#FFFBEB",
    "warning_text":  "#92400E",
    "info":          "#3B82F6",
    "info_bg":       "#EFF6FF",
    "info_text":     "#1E40AF",
    # 阴影
    "shadow_sm":     "0 1px 2px rgba(0,0,0,0.04)",
    "shadow_md":     "0 2px 8px rgba(0,0,0,0.06)",
    "shadow_lg":     "0 8px 24px rgba(0,0,0,0.08)",
}

# ═════════════════════════════════════════════════════════
#  CSS 样式表 v4
# ═════════════════════════════════════════════════════════
CSS = """
/* ══════════ 全局基础 ══════════ */
.stApp {
    background: """ + PALETTE["bg_main"] + """;
}
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
    max-width: 1400px;
}

/* ══════════ 排版 ══════════ */
h1, h2, h3, h4, h5 {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    letter-spacing: -0.3px;
}
h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: """ + PALETTE["text_primary"] + """ !important;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid """ + PALETTE["accent"] + """ !important;
    margin-bottom: 1.2rem !important;
    display: flex;
    align-items: center;
    gap: 8px;
}
h2 { font-size: 1.15rem !important; color: """ + PALETTE["text_primary"] + """ !important; font-weight: 600 !important; }
h3 { font-size: 1rem !important; color: """ + PALETTE["text_secondary"] + """ !important; font-weight: 600 !important; }
h4 { font-size: 0.9rem !important; color: """ + PALETTE["text_muted"] + """ !important; font-weight: 500 !important; }

/* ══════════ 侧边栏 ══════════ */
[data-testid="stSidebar"] {
    background: """ + PALETTE["bg_sidebar"] + """;
    border-right: 1px solid """ + PALETTE["border"] + """;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 0.8rem;
    padding-bottom: 0.5rem;
}
/* 侧边栏内section标题 */
.sidebar-section-title {
    font-size: 0.68rem;
    font-weight: 700;
    color: """ + PALETTE["text_muted"] + """;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid """ + PALETTE["border_light"] + """;
    margin-top: 8px;
    margin-bottom: 6px;
}

/* ══════════ 导航按钮 ══════════ */
div[role="radiogroup"] > label {
    background: """ + PALETTE["bg_card"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 8px !important;
    margin-bottom: 2px !important;
    padding: 9px 14px !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    transition: all 0.15s ease !important;
    font-size: 0.88rem !important;
    box-shadow: """ + PALETTE["shadow_sm"] + """;
}
div[role="radiogroup"] > label:hover {
    background: """ + PALETTE["accent_light"] + """ !important;
    border-color: rgba(200,146,58,0.3) !important;
    color: """ + PALETTE["accent"] + """ !important;
}
div[role="radiogroup"] > label[data-checked="true"] {
    background: """ + PALETTE["accent_light"] + """ !important;
    border-color: """ + PALETTE["accent"] + """ !important;
    color: """ + PALETTE["accent"] + """ !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(200,146,58,0.15);
}

/* ══════════ KPI / Metric 卡片 ══════════ */
[data-testid="stMetric"] {
    background: """ + PALETTE["bg_card"] + """;
    border: 1px solid """ + PALETTE["border"] + """;
    border-radius: 12px;
    padding: 16px 18px;
    transition: all 0.2s ease;
    box-shadow: """ + PALETTE["shadow_sm"] + """;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(200,146,58,0.25);
    box-shadow: """ + PALETTE["shadow_md"] + """;
    transform: translateY(-1px);
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    color: """ + PALETTE["text_muted"] + """ !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: """ + PALETTE["text_primary"] + """ !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* ══════════ Section Card 容器 ══════════ */
.section-card {
    background: """ + PALETTE["bg_card"] + """;
    border: 1px solid """ + PALETTE["border"] + """;
    border-radius: 12px;
    padding: 20px 22px;
    margin: 12px 0;
    box-shadow: """ + PALETTE["shadow_sm"] + """;
    transition: all 0.2s ease;
}
.section-card:hover {
    box-shadow: """ + PALETTE["shadow_md"] + """;
}

/* ══════════ 进度条 ══════════ */
.stProgress > div > div {
    background: """ + PALETTE["gradient"] + """ !important;
    border-radius: 4px;
    height: 6px !important;
}
.stProgress {
    background: """ + PALETTE["border"] + """ !important;
    border-radius: 4px;
    height: 6px !important;
}

/* ══════════ 按钮 ══════════ */
.stButton > button {
    background: """ + PALETTE["bg_card"] + """ !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    font-size: 0.88rem !important;
}
.stButton > button:hover {
    border-color: """ + PALETTE["accent"] + """ !important;
    color: """ + PALETTE["accent"] + """ !important;
    box-shadow: 0 2px 8px rgba(200,146,58,0.12);
}
.stButton > button[kind="primary"] {
    background: """ + PALETTE["gradient"] + """ !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.05);
    box-shadow: 0 4px 14px rgba(200,146,58,0.3);
    transform: translateY(-1px);
}

/* ══════════ 表格 ══════════ */
.stDataFrame table {
    border-collapse: separate;
    border-spacing: 0;
}
.stDataFrame thead th {
    background: """ + PALETTE["bg_card_alt"] + """ !important;
    color: """ + PALETTE["text_muted"] + """ !important;
    font-weight: 600 !important;
    font-size: 0.76rem !important;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 2px solid """ + PALETTE["border"] + """ !important;
    padding: 10px 14px !important;
}
.stDataFrame tbody td {
    background: """ + PALETTE["bg_card"] + """ !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    font-size: 0.84rem;
    border-bottom: 1px solid """ + PALETTE["border_light"] + """ !important;
    padding: 8px 14px !important;
}
.stDataFrame tbody tr:hover td {
    background: """ + PALETTE["accent_light"] + """ !important;
}

/* ══════════ Tabs ══════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: """ + PALETTE["bg_card_alt"] + """;
    border: 1px solid """ + PALETTE["border"] + """;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    color: """ + PALETTE["text_muted"] + """;
    font-weight: 500;
    font-size: 0.88rem;
}
.stTabs [aria-selected="true"] {
    background: """ + PALETTE["bg_card"] + """;
    color: """ + PALETTE["accent"] + """ !important;
    border-color: """ + PALETTE["accent"] + """ !important;
    border-bottom: 2px solid """ + PALETTE["accent"] + """ !important;
    font-weight: 600;
}

/* ══════════ Expander ══════════ */
.streamlit-expanderHeader {
    background: """ + PALETTE["bg_card_alt"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 8px !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.streamlit-expanderHeader:hover {
    border-color: rgba(200,146,58,0.3) !important;
    color: """ + PALETTE["accent"] + """ !important;
}

/* ══════════ Select / Input ══════════ */
.stSelectbox [data-baseweb="select"] > div,
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: """ + PALETTE["bg_card"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 8px !important;
    color: """ + PALETTE["text_primary"] + """ !important;
    font-size: 0.9rem;
}
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: """ + PALETTE["accent"] + """ !important;
    box-shadow: 0 0 0 3px rgba(200,146,58,0.1);
}

/* ══════════ 消息框 ══════════ */
.stSuccess {
    background: """ + PALETTE["success_bg"] + """ !important;
    border: 1px solid #A7F3D0 !important;
    border-radius: 8px !important;
    color: """ + PALETTE["success_text"] + """ !important;
}
.stWarning {
    background: """ + PALETTE["warning_bg"] + """ !important;
    border: 1px solid #FDE68A !important;
    border-radius: 8px !important;
    color: """ + PALETTE["warning_text"] + """ !important;
}
.stError {
    background: """ + PALETTE["danger_bg"] + """ !important;
    border: 1px solid #FECACA !important;
    border-radius: 8px !important;
    color: """ + PALETTE["danger_text"] + """ !important;
}
.stInfo {
    background: """ + PALETTE["info_bg"] + """ !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 8px !important;
    color: """ + PALETTE["info_text"] + """ !important;
}

/* ══════════ Divider ══════════ */
hr {
    border-color: """ + PALETTE["border"] + """ !important;
    margin: 0.8rem 0 !important;
}

/* ══════════ Caption ══════════ */
.stCaption {
    color: """ + PALETTE["text_muted"] + """ !important;
    font-size: 0.76rem !important;
}

/* ══════════ Slider ══════════ */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: """ + PALETTE["accent"] + """ !important;
    border: 2px solid """ + PALETTE["bg_card"] + """ !important;
}
.stSlider [data-baseweb="slider"] > div > div {
    background: """ + PALETTE["accent"] + """ !important;
}

/* ══════════ 滚动条 ══════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: """ + PALETTE["bg_main"] + """; }
::-webkit-scrollbar-thumb {
    background: #D1D5DB;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }

/* ══════════ Spinner ══════════ */
.stSpinner > div {
    border-color: """ + PALETTE["accent"] + """ transparent transparent transparent !important;
}

/* ═══════════════════════════════════════
   自定义组件样式
   ═══════════════════════════════════════ */

/* ── 侧边栏快速行情条 ── */
.sidebar-price-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    padding: 5px 8px;
    margin: 2px 0;
    border-radius: 6px;
    transition: background 0.15s;
}
.sidebar-price-row:hover {
    background: """ + PALETTE["accent_subtle"] + """;
}
.sidebar-price-name {
    font-weight: 500;
    color: """ + PALETTE["text_secondary"] + """;
    min-width: 50px;
}
.sidebar-price-val {
    font-weight: 700;
    color: """ + PALETTE["text_primary"] + """;
}
.sidebar-price-chg {
    font-weight: 600;
    font-size: 0.76rem;
    min-width: 60px;
    text-align: right;
}

/* ── 快讯条目 ── */
.news-item {
    display: flex;
    align-items: flex-start;
    padding: 6px 0;
    border-bottom: 1px solid """ + PALETTE["border_light"] + """;
    font-size: 0.8rem;
    line-height: 1.4;
}
.news-item:last-child {
    border-bottom: none;
}
.news-time {
    color: """ + PALETTE["accent"] + """;
    min-width: 48px;
    font-weight: 600;
    font-size: 0.7rem;
    flex-shrink: 0;
    padding-top: 1px;
}
.news-content {
    color: """ + PALETTE["text_secondary"] + """;
    flex: 1;
}

/* ── 状态徽章 ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
}

/* ── 数据源指示器 ── */
.datasource-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 4px 0;
}

/* ═══════════════════════════════════════
   响应式 — 移动端 & 平板适配
   ═══════════════════════════════════════ */

/* ── 平板 (< 768px) ── */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem 0.4rem 4.5rem 0.4rem !important;
    }
    @supports (padding: env(safe-area-inset-bottom)) {
        .main .block-container {
            padding-bottom: calc(4.5rem + env(safe-area-inset-bottom)) !important;
        }
    }

    h1 { font-size: 1.1rem !important; padding-bottom: 0.3rem; margin-bottom: 0.6rem !important; }
    h2 { font-size: 0.95rem !important; }
    h3 { font-size: 0.88rem !important; }
    h4 { font-size: 0.82rem !important; }

    [data-testid="stSidebar"] {
        min-width: 280px !important;
        max-width: 88vw !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 0.4rem 0.6rem !important;
    }

    div[role="radiogroup"] > label {
        padding: 11px 14px !important;
        font-size: 0.9rem !important;
        min-height: 48px;
        display: flex !important;
        align-items: center;
        border-radius: 10px !important;
        margin-bottom: 3px !important;
    }

    [data-testid="stMetric"] {
        padding: 10px 12px !important;
        border-radius: 8px;
    }
    [data-testid="stMetricLabel"] { font-size: 0.66rem !important; }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
    [data-testid="stMetricDelta"] { font-size: 0.7rem !important; }

    .stButton > button {
        padding: 11px 16px !important;
        min-height: 48px;
        font-size: 0.9rem !important;
        width: 100% !important;
        border-radius: 10px !important;
    }

    .stDataFrame { overflow-x: auto !important; -webkit-overflow-scrolling: touch; border-radius: 8px; }
    .stDataFrame thead th {
        font-size: 0.66rem !important; padding: 6px 8px !important;
        white-space: nowrap; position: sticky; top: 0; z-index: 2;
    }
    .stDataFrame thead th:first-child { position: sticky; left: 0; z-index: 3; }
    .stDataFrame tbody td { font-size: 0.74rem !important; padding: 6px 8px !important; }
    .stDataFrame tbody td:first-child {
        position: sticky; left: 0; background: """ + PALETTE["bg_card"] + """ !important;
        z-index: 1; font-weight: 600;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 14px !important; font-size: 0.8rem !important;
        min-height: 48px; flex: 1; text-align: center;
        border-radius: 10px 10px 0 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        display: flex; flex-wrap: nowrap; overflow-x: auto;
        -webkit-overflow-scrolling: touch; gap: 2px; scrollbar-width: none;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }

    .streamlit-expanderHeader {
        padding: 12px 14px !important; font-size: 0.84rem !important;
        min-height: 48px; border-radius: 10px !important;
    }

    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput input, .stNumberInput input {
        font-size: 16px !important; min-height: 48px; padding: 10px 14px !important;
        border-radius: 10px !important;
    }
    .stTextArea textarea { font-size: 16px !important; border-radius: 10px !important; }
    .stMultiSelect [data-baseweb="select"] > div { font-size: 16px !important; min-height: 48px; }

    hr { margin: 0.5rem 0 !important; }

    .js-plotly-plot { max-width: 100% !important; overflow-x: auto !important; }
    .js-plotly-plot .plotly .modebar { opacity: 1 !important; }

    .rec-card { padding: 10px 12px !important; margin: 4px 0 !important; }

    .stSlider { padding-top: 6px !important; }
    .stSlider [role="slider"] { width: 22px !important; height: 22px !important; }
    .stCheckbox label { font-size: 0.86rem !important; min-height: 44px; display: flex; align-items: center; }
    .stRadio label { min-height: 44px; }

    [data-testid="stToast"] {
        top: 10px !important; right: 10px !important; left: 10px !important;
        max-width: calc(100vw - 20px) !important;
    }
}

/* ── 手机 (< 480px) ── */
@media (max-width: 480px) {
    .main .block-container {
        padding: 0.3rem 0.2rem 4.2rem 0.2rem !important;
    }
    @supports (padding: env(safe-area-inset-bottom)) {
        .main .block-container {
            padding-bottom: calc(4.2rem + env(safe-area-inset-bottom)) !important;
        }
    }

    h1 { font-size: 1.05rem !important; }
    h2 { font-size: 0.88rem !important; }
    h3 { font-size: 0.82rem !important; }

    [data-testid="stSidebar"] { min-width: 260px !important; max-width: 92vw !important; }
    [data-testid="stMetric"] { padding: 8px 10px !important; border-radius: 6px; }
    [data-testid="stMetricValue"] { font-size: 0.92rem !important; }
    div[role="radiogroup"] > label { padding: 10px 12px !important; font-size: 0.86rem !important; min-height: 46px; }
    .stDataFrame thead th { font-size: 0.6rem !important; }
    .stDataFrame tbody td { font-size: 0.68rem !important; }
    .stTabs [data-baseweb="tab"] { padding: 8px 10px !important; font-size: 0.74rem !important; min-height: 44px; white-space: nowrap; }
    .rec-card { padding: 8px 10px !important; border-left-width: 3px !important; }
}
"""


def inject_css():
    """注入全局 CSS"""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
#  UI 组件工厂 v4
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
    """段落标题 — 带渐变左侧装饰条"""
    icon_str = f"{icon} " if icon else ""
    html = f"""
    <div style="display:flex;align-items:center;gap:8px;margin:4px 0 2px 0;">
        <div style="width:3px;height:18px;border-radius:2px;background:{PALETTE['gradient']};"></div>
        <span style="font-size:0.95rem;font-weight:600;color:{PALETTE['text_primary']};">
            {icon_str}{title}
        </span>
    </div>"""
    if subtitle:
        html += f'<div style="font-size:0.74rem;color:{PALETTE["text_muted"]};margin-left:11px;margin-bottom:4px;">{subtitle}</div>'
    st.markdown(html, unsafe_allow_html=True)


def section_card(title: str = "", subtitle: str = "", icon: str = ""):
    """返回一个 section card 容器的开头 HTML（需配合 st.markdown 使用）"""
    header = ""
    if title:
        icon_str = f"{icon} " if icon else ""
        header = f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <div style="width:3px;height:18px;border-radius:2px;background:{PALETTE['gradient']};"></div>
            <span style="font-size:0.95rem;font-weight:600;color:{PALETTE['text_primary']};">
                {icon_str}{title}
            </span>
        </div>"""
        if subtitle:
            header += f'<div style="font-size:0.74rem;color:{PALETTE["text_muted"]};margin-left:11px;margin-top:-8px;margin-bottom:8px;">{subtitle}</div>'
    return f'<div class="section-card">{header}'


def section_card_end():
    """关闭 section card 容器"""
    return '</div>'


def confidence_indicator(confidence: float):
    """信心指数展示 — 改用百分比条 + 标签"""
    pct = int(confidence * 100)
    if confidence >= 0.75:
        color = PALETTE["success"]
        bg = PALETTE["success_bg"]
        label = "高信心"
    elif confidence >= 0.5:
        color = PALETTE["warning"]
        bg = PALETTE["warning_bg"]
        label = "中信度"
    else:
        color = PALETTE["danger"]
        bg = PALETTE["danger_bg"]
        label = "低信心"

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
        <div style="flex:1;height:6px;background:{PALETTE['border']};border-radius:3px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:3px;transition:width 0.3s;"></div>
        </div>
        <span class="status-badge" style="background:{bg};color:{color};">{label} {pct}%</span>
    </div>""", unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📭"):
    """空状态占位 — 更精致的卡片式"""
    st.markdown(f"""
    <div style="text-align:center;padding:40px 20px;background:{PALETTE['bg_card_alt']};
                border:1px dashed {PALETTE['border']};border-radius:12px;margin:12px 0;">
        <div style="font-size:2.2rem;margin-bottom:10px;opacity:0.6;">{icon}</div>
        <div style="font-size:0.88rem;color:{PALETTE['text_muted']};">{message}</div>
    </div>""", unsafe_allow_html=True)


def mobile_kpi_row(items: list, cols_per_row: int = 2):
    """移动端友好的 KPI 行：自动按 cols_per_row 分组渲染"""
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
    """移动端底部导航栏 — 已移除"""
    pass


def sidebar_section_title(title: str):
    """侧边栏小节标题"""
    st.markdown(f'<div class="sidebar-section-title">{title}</div>', unsafe_allow_html=True)


def sidebar_price_row(metal_type: str, price: float, change_pct: float):
    """侧边栏价格行 — 修复后的版本"""
    sign = "+" if change_pct >= 0 else ""
    color = PALETTE["success"] if change_pct >= 0 else PALETTE["danger"]
    st.markdown(
        f'<div class="sidebar-price-row">'
        f'<span class="sidebar-price-name">{metal_type}</span>'
        f'<span class="sidebar-price-val">¥{price:,.0f}</span>'
        f'<span class="sidebar-price-chg" style="color:{color};">{sign}{change_pct:.2f}%</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def sidebar_news_item(content: str, time_str: str = ""):
    """侧边栏快讯条目"""
    if len(content) > 48:
        content = content[:46] + ".."
    st.markdown(
        f'<div class="news-item">'
        f'<span class="news-time">{time_str}</span>'
        f'<span class="news-content">{content}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def datasource_badge(is_real: bool, label: str = ""):
    """数据源状态徽章"""
    if is_real:
        color = PALETTE["success"]
        bg = PALETTE["success_bg"]
        icon = "⚡"
        text = label or "SHFE 实时"
    else:
        color = PALETTE["warning"]
        bg = PALETTE["warning_bg"]
        icon = "📀"
        text = label or "本地模拟"
    st.markdown(
        f'<div class="datasource-indicator" style="background:{bg};color:{color};">'
        f'{icon} {text}</div>',
        unsafe_allow_html=True,
    )


def news_item_card(content: str, time_str: str = ""):
    """主内容区快讯条目 — 带左侧色条"""
    st.markdown(
        f'<div style="display:flex;align-items:flex-start;padding:8px 0;'
        f'border-bottom:1px solid {PALETTE["border_light"]};font-size:0.82rem;line-height:1.4;">'
        f'<div style="width:3px;min-height:16px;background:{PALETTE["gradient"]};'
        f'border-radius:2px;margin-right:8px;margin-top:3px;flex-shrink:0;"></div>'
        f'<span style="color:{PALETTE["accent"]};min-width:48px;font-weight:600;'
        f'font-size:0.7rem;flex-shrink:0;padding-top:1px;">{time_str}</span>'
        f'<span style="color:{PALETTE["text_secondary"]};flex:1;">{content}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def backtest_outcome_card(outcome: dict):
    """回测结果卡片"""
    correct = outcome.get("was_correct")
    if correct is True:
        bg = PALETTE["success_bg"]; border = PALETTE["success"]; tag = "✅"
    elif correct is False:
        bg = PALETTE["danger_bg"]; border = PALETTE["danger"]; tag = "❌"
    else:
        bg = PALETTE["bg_card_alt"]; border = PALETTE["border"]; tag = "⏳"
    st.markdown(
        f'<div style="background:{bg};border-left:3px solid {border};'
        f'padding:10px 14px;margin:4px 0;border-radius:8px;'
        f'font-size:0.82rem;display:flex;justify-content:space-between;align-items:center;'
        f'flex-wrap:wrap;gap:6px;">'
        f'<span style="font-weight:500;">{outcome["date"]} <b>{outcome["metal_type"]}</b> '
        f'{outcome["action"]}({outcome["confidence"]:.0%})</span>'
        f'<span style="white-space:nowrap;">{tag} 3d:{outcome.get("outcome_3d","?")}% '
        f'7d:{outcome.get("outcome_7d","?")}% '
        f'30d:{outcome.get("outcome_30d","?")}%</span></div>',
        unsafe_allow_html=True,
    )


def roi_display(roi_pct: float, target: float = 30.0):
    """ROI 展示 — 更精美的圆环式"""
    color = PALETTE["success"] if roi_pct >= 0 else PALETTE["danger"]
    bg = PALETTE["success_bg"] if roi_pct >= 0 else PALETTE["danger_bg"]
    progress = min(abs(roi_pct) / target, 1.0)
    st.markdown(f"""
    <div style="text-align:center;padding:24px 16px;background:{PALETTE['bg_card_alt']};
                border:1px solid {PALETTE['border']};border-radius:12px;margin:8px 0;">
        <div style="font-size:0.8rem;color:{PALETTE['text_muted']};margin-bottom:8px;
                    text-transform:uppercase;letter-spacing:0.5px;">总投资回报率</div>
        <div style="font-size:2.4rem;font-weight:800;color:{color};line-height:1;">{roi_pct:+.2f}%</div>
        <div style="margin-top:10px;height:6px;background:{PALETTE['border']};
                    border-radius:3px;overflow:hidden;max-width:280px;margin-left:auto;margin-right:auto;">
            <div style="width:{progress*100}%;height:100%;background:{color};
                        border-radius:3px;transition:width 0.5s;"></div>
        </div>
        <div style="color:{PALETTE['text_muted']};font-size:0.74rem;margin-top:6px;">
            目标: {target:.0f}% | 当前: {roi_pct:.2f}%</div>
    </div>""", unsafe_allow_html=True)


def factor_scores_card(ta: dict):
    """多因子评分卡片 v4 — 更紧凑的标签式"""
    rows = [
        ("📊", "技术面", [
            ("趋势", ta.get('trend_score', '-')),
            ("动量", ta.get('momentum_score', '-')),
            ("波动", ta.get('volatility_score', '-')),
            ("支撑", ta.get('sr_score', '-')),
            ("量价", ta.get('volume_score', '-')),
            ("状态", ta.get('regime_score', '-')),
            ("背离", ta.get('divergence_score', '-')),
        ]),
        ("🌍", "基本面", [
            ("季节性", ta.get('seasonal_score', '-')),
            ("联动性", ta.get('correlation_score', '-')),
            ("宏观", ta.get('macro_score', '-')),
            ("多周期", ta.get('timeframe_score', '-')),
            ("供需", ta.get('supply_demand_score', '-')),
        ]),
        ("🏭", "运营面", [
            ("运营", ta.get('operational_score', '-')),
            ("风控", ta.get('risk_score', '-')),
        ]),
    ]
    composite = ta.get('composite_score', 0)
    if isinstance(composite, (int, float)):
        if composite >= 70:
            comp_color = PALETTE["success"]; comp_bg = PALETTE["success_bg"]
        elif composite >= 45:
            comp_color = PALETTE["warning"]; comp_bg = PALETTE["warning_bg"]
        else:
            comp_color = PALETTE["danger"]; comp_bg = PALETTE["danger_bg"]
    else:
        comp_color = PALETTE["text_muted"]; comp_bg = PALETTE["bg_card_alt"]

    html_parts = [
        f'<div style="background:{PALETTE["bg_card_alt"]};border:1px solid {PALETTE["border"]};'
        f'border-radius:10px;padding:12px 14px;margin:6px 0;">',
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">'
        f'<span style="background:{comp_bg};color:{comp_color};padding:3px 12px;border-radius:6px;'
        f'font-size:0.88rem;font-weight:700;">综合 {composite}/100</span>'
        f'</div>',
    ]
    for icon, title, items in rows:
        badges = " ".join(
            f'<span style="background:{PALETTE["bg_card"]};color:{PALETTE["text_secondary"]};'
            f'border:1px solid {PALETTE["border"]};'
            f'padding:1px 7px;border-radius:4px;font-size:0.7rem;margin:1px;'
            f'white-space:nowrap;display:inline-block;">{k}:{v}</span>'
            for k, v in items
        )
        html_parts.append(
            f'<div style="display:flex;align-items:flex-start;gap:4px;margin:4px 0;flex-wrap:wrap;">'
            f'<span style="font-size:0.72rem;flex-shrink:0;color:{PALETTE["accent"]};min-width:40px;font-weight:500;">'
            f'{icon} {title}</span>'
            f'<span style="flex:1;min-width:0;">{badges}</span></div>'
        )
    html_parts.append('</div>')
    st.markdown("\n".join(html_parts), unsafe_allow_html=True)


def recommendation_card(rec: dict, index: int, action_type: str):
    """推荐卡片 v4 — 更精致的卡片式"""
    ta = rec.get('trend_analysis', {})
    confidence = rec.get('confidence', 0)
    is_buy = action_type == "buy"
    actual_action = rec.get('action', '买入' if is_buy else '卖出')

    # 根据实际操作类型选择颜色
    if actual_action in ("买入", "加仓"):
        accent = PALETTE["success"]; accent_bg = PALETTE["success_bg"]
        emoji = "🟢" if actual_action == "买入" else "📈"
    elif actual_action in ("卖出", "减仓"):
        accent = PALETTE["danger"]; accent_bg = PALETTE["danger_bg"]
        emoji = "🔴" if actual_action == "卖出" else "📉"
    elif actual_action == "止损":
        accent = "#DC2626"; accent_bg = "#FEE2E2"; emoji = "🚨"
    elif actual_action == "观望":
        accent = PALETTE["warning"]; accent_bg = PALETTE["warning_bg"]; emoji = "⏸️"
    else:
        accent = PALETTE["success"] if is_buy else PALETTE["danger"]
        accent_bg = PALETTE["success_bg"] if is_buy else PALETTE["danger_bg"]
        emoji = "🟢" if is_buy else "🔴"

    price = rec.get('current_price', 0)
    sl = rec.get('stop_loss', 0)
    tp = rec.get('take_profit', 0)
    qty = rec.get('suggested_quantity_kg', 0)
    profit = rec.get('expected_profit_pct', 0)
    risk = rec.get('risk_level', '中')

    profit_line = f'<span>💰 预期: <b style="color:{accent};">{profit:+.1f}%</b></span>' if profit != 0 else ''
    factor_agree = ta.get('factor_agreement', None)
    agree_line = f'<span>📊 一致: <b>{factor_agree:.0%}</b></span>' if factor_agree is not None else ''

    # 风险色
    risk_colors = {"低": (PALETTE["success"], PALETTE["success_bg"]),
                   "中": (PALETTE["warning"], PALETTE["warning_bg"]),
                   "高": (PALETTE["danger"], PALETTE["danger_bg"])}
    risk_c, risk_bg = risk_colors.get(risk, (PALETTE["text_muted"], PALETTE["bg_card_alt"]))

    html = f"""
    <div class="rec-card" style="
        background:{PALETTE['bg_card']};
        border:1px solid {PALETTE['border']};
        border-left:4px solid {accent};
        border-radius:10px;
        padding:14px 16px;
        margin:8px 0;
        transition:all 0.15s ease;
        box-shadow:{PALETTE['shadow_sm']};
    ">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                <span style="font-size:0.7rem;color:{PALETTE['text_muted']};">#{index}</span>
                <span style="font-size:1rem;font-weight:700;color:{PALETTE['text_primary']};">
                    {rec['metal_type']}
                </span>
                <span style="background:{accent_bg};color:{accent};padding:2px 8px;
                             border-radius:10px;font-size:0.72rem;font-weight:600;white-space:nowrap;">
                    {emoji} {actual_action}
                </span>
                <span style="background:{risk_bg};color:{risk_c};padding:2px 6px;
                             border-radius:6px;font-size:0.68rem;font-weight:600;">
                    风险:{risk}
                </span>
            </div>
            <span style="font-size:1.1rem;font-weight:700;color:{PALETTE['text_primary']};">
                ¥{price:,.0f}
            </span>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:0.78rem;color:{PALETTE['text_muted']};">
            <span>🎯 止损: <b style="color:{PALETTE['danger']};">¥{sl:,.0f}</b></span>
            <span>🏁 止盈: <b style="color:{PALETTE['success']};">¥{tp:,.0f}</b></span>
            <span>📦 仓位: <b style="color:{PALETTE['accent']};">{qty:.0f}%</b></span>
            {profit_line}
            {agree_line}
        </div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)
    confidence_indicator(confidence)


def plotly_theme() -> dict:
    """统一的 Plotly 图表主题"""
    return dict(
        template="plotly_white",
        paper_bgcolor=PALETTE["bg_card"],
        plot_bgcolor=PALETTE["bg_card_alt"],
        font=dict(color=PALETTE["text_muted"], size=12),
        title_font=dict(color=PALETTE["text_primary"], size=14),
        legend=dict(font=dict(color=PALETTE["text_muted"])),
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(
            gridcolor=PALETTE["border"], zerolinecolor=PALETTE["border"],
            linecolor=PALETTE["border"], tickfont=dict(color=PALETTE["text_muted"]),
        ),
        yaxis=dict(
            gridcolor=PALETTE["border"], zerolinecolor=PALETTE["border"],
            linecolor=PALETTE["border"], tickfont=dict(color=PALETTE["text_muted"]),
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(color=PALETTE["text_muted"]),
            title_font=dict(color=PALETTE["text_muted"]),
        ),
    )


def styled_plotly(fig):
    """给 plotly figure 应用统一主题"""
    theme = plotly_theme()
    fig.update_layout(**theme)
    return fig


# Plotly 快速渲染配置
PLOTLY_FAST_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "displaylogo": False,
}
