"""
UI 样式系统 v5 — 浅色金融交易主题
商业级设计: 毛玻璃卡片 + 金铜渐变 + 微动效 + Staggered 动画
"""
import streamlit as st
from typing import Optional


# ═════════════════════════════════════════════════════════
#  Palette — Dark Luxury 语义 Token 体系
# ═════════════════════════════════════════════════════════
PALETTE = {
    # ── 浅色表面层级 ──
    "bg_deep":         "#E8ECF1",   # 最深 (装饰用)
    "bg_base":         "#F3F4F8",   # 主背景
    "bg_surface":      "#FFFFFF",   # 卡片/侧边栏
    "bg_surface_hover":"#F9FAFB",   # 卡片悬停
    "bg_surface_alt":  "#F9FAFB",   # 次要表面
    "bg_overlay":      "rgba(255,255,255,0.85)",  # 毛玻璃覆盖层

    # ── 文字 ──
    "text_primary":    "#111827",
    "text_secondary":  "#4B5563",
    "text_muted":      "#9CA3AF",

    # ── 边框 ──
    "border":          "#E5E7EB",
    "border_light":    "#F3F4F6",
    "border_focus":    "#C8923A",

    # ── 品牌金铜色 ──
    "accent":          "#C8923A",
    "accent_hover":    "#B07E30",
    "accent_light":    "#FFF8F0",
    "accent_subtle":   "rgba(200,146,58,0.06)",
    "gradient":        "linear-gradient(135deg, #C8923A 0%, #D4832A 100%)",
    "gradient_glow":   "linear-gradient(135deg, #C8923A 0%, #D4832A 50%, #E8C97A 100%)",

    # ── 语义色 ──
    "success":         "#10B981",
    "success_bg":      "#ECFDF5",
    "success_text":    "#065F46",
    "danger":          "#EF4444",
    "danger_bg":       "#FEF2F2",
    "danger_text":     "#991B1B",
    "warning":         "#F59E0B",
    "warning_bg":      "#FFFBEB",
    "warning_text":    "#92400E",
    "info":            "#3B82F6",
    "info_bg":         "#EFF6FF",
    "info_text":       "#1E40AF",

    # ── 阴影 (浅色) ──
    "shadow_sm":       "0 1px 2px rgba(0,0,0,0.04)",
    "shadow_md":       "0 2px 8px rgba(0,0,0,0.06)",
    "shadow_lg":       "0 8px 24px rgba(0,0,0,0.08)",
    "shadow_glow":     "0 0 24px rgba(200,146,58,0.12)",
}

# ═════════════════════════════════════════════════════════
#  CSS — Dark Luxury 完整样式表
# ═════════════════════════════════════════════════════════
CSS = """
/* ════════ 全局基础 ════════ */
.stApp {
    background: """ + PALETTE["bg_base"] + """;
}
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
    max-width: 1400px;
}
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ════════ 排版 ════════ */
h1, h2, h3, h4, h5 {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    letter-spacing: -0.3px;
}
h1 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: """ + PALETTE["text_primary"] + """ !important;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid rgba(200,146,58,0.3) !important;
    margin-bottom: 1.2rem !important;
    letter-spacing: -0.5px;
}
h2 {
    font-size: 1.1rem !important;
    color: """ + PALETTE["text_primary"] + """ !important;
    font-weight: 600 !important;
}
h3 {
    font-size: 0.95rem !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    font-weight: 600 !important;
}
h4 {
    font-size: 0.88rem !important;
    color: """ + PALETTE["text_muted"] + """ !important;
    font-weight: 500 !important;
}

/* ════════ 侧边栏 — 毛玻璃效果 ════════ */
[data-testid="stSidebar"] {
    background: """ + PALETTE["bg_surface"] + """;
    border-right: 1px solid """ + PALETTE["border"] + """;
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: """ + PALETTE["gradient"] + """;
    opacity: 0.4;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 0.8rem;
    padding-bottom: 0.5rem;
}
.sidebar-section-title {
    font-size: 0.64rem;
    font-weight: 700;
    color: """ + PALETTE["text_muted"] + """;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid """ + PALETTE["border_light"] + """;
    margin-top: 10px;
    margin-bottom: 8px;
}

/* ════════ 导航 — 暗色金边 ════════ */
div[role="radiogroup"] > label {
    background: """ + PALETTE["bg_surface_alt"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 10px !important;
    margin-bottom: 3px !important;
    padding: 10px 14px !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    transition: all 0.2s cubic-bezier(0.16,1,0.3,1) !important;
    font-size: 0.86rem !important;
    box-shadow: none;
}
div[role="radiogroup"] > label:hover {
    background: """ + PALETTE["bg_surface_hover"] + """ !important;
    border-color: rgba(200,146,58,0.3) !important;
    color: """ + PALETTE["accent_hover"] + """ !important;
    transform: translateX(2px);
}
div[role="radiogroup"] > label[data-checked="true"] {
    background: """ + PALETTE["accent_light"] + """ !important;
    border-color: """ + PALETTE["accent"] + """ !important;
    color: """ + PALETTE["accent_hover"] + """ !important;
    font-weight: 600 !important;
    box-shadow: 0 0 20px rgba(200,146,58,0.1);
}

/* ════════ KPI / Metric — 毛玻璃卡片 ════════ */
[data-testid="stMetric"] {
    background: """ + PALETTE["bg_surface"] + """;
    border: 1px solid """ + PALETTE["border_light"] + """;
    border-radius: 14px;
    padding: 18px 20px;
    transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
    box-shadow: """ + PALETTE["shadow_sm"] + """;
    backdrop-filter: blur(8px);
}
[data-testid="stMetric"]:hover {
    border-color: rgba(200,146,58,0.25);
    box-shadow: """ + PALETTE["shadow_glow"] + """;
    transform: translateY(-2px);
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    color: """ + PALETTE["text_muted"] + """ !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    color: """ + PALETTE["text_primary"] + """ !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
}

/* ════════ 区块卡片容器 ════════ */
.section-card {
    background: """ + PALETTE["bg_surface"] + """;
    border: 1px solid """ + PALETTE["border"] + """;
    border-radius: 14px;
    padding: 22px 24px;
    margin: 12px 0;
    box-shadow: """ + PALETTE["shadow_sm"] + """;
    transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
}
.section-card:hover {
    border-color: rgba(200,146,58,0.15);
    box-shadow: """ + PALETTE["shadow_md"] + """;
}

/* ════════ 进度条 — 金色发光 ════════ */
.stProgress > div > div {
    background: """ + PALETTE["gradient_glow"] + """ !important;
    border-radius: 3px;
    height: 6px !important;
    box-shadow: 0 0 8px rgba(200,146,58,0.3);
}
.stProgress {
    background: """ + PALETTE["border"] + """ !important;
    border-radius: 3px;
    height: 6px !important;
}

/* ════════ 按钮 — 金色层级 ════════ */
.stButton > button {
    background: """ + PALETTE["bg_surface_alt"] + """ !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 10px !important;
    padding: 9px 20px !important;
    font-weight: 500 !important;
    transition: all 0.2s cubic-bezier(0.16,1,0.3,1) !important;
    font-size: 0.86rem !important;
}
.stButton > button:hover {
    border-color: """ + PALETTE["accent"] + """ !important;
    color: """ + PALETTE["accent_hover"] + """ !important;
    background: """ + PALETTE["accent_light"] + """ !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(200,146,58,0.12);
}
.stButton > button:active {
    transform: scale(0.97);
}
.stButton > button[kind="primary"] {
    background: """ + PALETTE["gradient"] + """ !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 20px rgba(200,146,58,0.25);
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08);
    box-shadow: 0 6px 28px rgba(200,146,58,0.35);
    transform: translateY(-2px);
}
.stButton > button[kind="primary"]:active {
    transform: scale(0.96);
}

/* ════════ 表格 — 暗色行 ════════ */
.stDataFrame table {
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 10px;
    overflow: hidden;
}
.stDataFrame thead th {
    background: """ + PALETTE["bg_surface_alt"] + """ !important;
    color: """ + PALETTE["text_muted"] + """ !important;
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 2px solid """ + PALETTE["border"] + """ !important;
    padding: 10px 14px !important;
}
.stDataFrame tbody td {
    background: """ + PALETTE["bg_surface"] + """ !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    font-size: 0.82rem;
    border-bottom: 1px solid """ + PALETTE["border_light"] + """ !important;
    padding: 8px 14px !important;
}
.stDataFrame tbody tr:hover td {
    background: """ + PALETTE["bg_surface_hover"] + """ !important;
}

/* ════════ Tabs ════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: """ + PALETTE["bg_surface_alt"] + """;
    border: 1px solid """ + PALETTE["border"] + """;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    color: """ + PALETTE["text_muted"] + """;
    font-weight: 500;
    font-size: 0.86rem;
    transition: all 0.15s ease;
}
.stTabs [aria-selected="true"] {
    background: """ + PALETTE["bg_surface"] + """;
    color: """ + PALETTE["accent_hover"] + """ !important;
    border-color: """ + PALETTE["accent"] + """ !important;
    border-bottom: 2px solid """ + PALETTE["accent"] + """ !important;
    font-weight: 600;
}

/* ════════ Expander ════════ */
.streamlit-expanderHeader {
    background: """ + PALETTE["bg_surface_alt"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 10px !important;
    color: """ + PALETTE["text_secondary"] + """ !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    transition: all 0.15s ease;
}
.streamlit-expanderHeader:hover {
    border-color: rgba(200,146,58,0.3) !important;
    color: """ + PALETTE["accent_hover"] + """ !important;
}

/* ════════ Select / Input — 暗色 ════════ */
.stSelectbox [data-baseweb="select"] > div,
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: """ + PALETTE["bg_surface_alt"] + """ !important;
    border: 1px solid """ + PALETTE["border"] + """ !important;
    border-radius: 10px !important;
    color: """ + PALETTE["text_primary"] + """ !important;
    font-size: 0.88rem;
    transition: all 0.15s ease;
}
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: """ + PALETTE["accent"] + """ !important;
    box-shadow: 0 0 0 3px rgba(200,146,58,0.12);
}

/* ════════ 消息框 — 暗色语义 ════════ */
.stSuccess {
    background: """ + PALETTE["success_bg"] + """ !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    border-radius: 10px !important;
    color: """ + PALETTE["success_text"] + """ !important;
}
.stWarning {
    background: """ + PALETTE["warning_bg"] + """ !important;
    border: 1px solid rgba(245,158,11,0.2) !important;
    border-radius: 10px !important;
    color: """ + PALETTE["warning_text"] + """ !important;
}
.stError {
    background: """ + PALETTE["danger_bg"] + """ !important;
    border: 1px solid rgba(239,68,68,0.2) !important;
    border-radius: 10px !important;
    color: """ + PALETTE["danger_text"] + """ !important;
}
.stInfo {
    background: """ + PALETTE["info_bg"] + """ !important;
    border: 1px solid rgba(96,165,250,0.2) !important;
    border-radius: 10px !important;
    color: """ + PALETTE["info_text"] + """ !important;
}

/* ════════ Divider ════════ */
hr {
    border-color: """ + PALETTE["border"] + """ !important;
    margin: 0.8rem 0 !important;
}

/* ════════ Caption ════════ */
.stCaption {
    color: """ + PALETTE["text_muted"] + """ !important;
    font-size: 0.74rem !important;
}

/* ════════ Slider — 金色轨道 ════════ */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: """ + PALETTE["accent"] + """ !important;
    border: 2px solid """ + PALETTE["bg_surface"] + """ !important;
    box-shadow: 0 0 8px rgba(200,146,58,0.3);
}
.stSlider [data-baseweb="slider"] > div > div {
    background: """ + PALETTE["accent"] + """ !important;
}

/* ════════ 滚动条 — 暗色 ════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: """ + PALETTE["bg_base"] + """; }
::-webkit-scrollbar-thumb {
    background: """ + PALETTE["border_light"] + """;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: """ + PALETTE["text_muted"] + """; }

/* ════════ Spinner — 金色 ════════ */
.stSpinner > div {
    border-color: """ + PALETTE["accent"] + """ transparent transparent transparent !important;
}

/* ════════ Focus Visible — 无障碍 ════════ */
:focus-visible {
    outline: 2px solid """ + PALETTE["accent"] + """ !important;
    outline-offset: 2px;
    border-radius: 3px;
}
:focus:not(:focus-visible) { outline: none !important; }
.stButton > button:focus-visible,
.stSelectbox [data-baseweb="select"] > div:focus-visible {
    box-shadow: 0 0 0 3px rgba(200,146,58,0.25) !important;
}

/* ════════ Reduced Motion ════════ */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
    [data-testid="stMetric"]:hover { transform: none !important; }
    .stButton > button:hover { transform: none !important; }
    .stagger-reveal { animation: none !important; opacity: 1 !important; }
    .live-pulse { animation: none !important; }
    .skeleton-shimmer { animation: none !important; }
}

/* ════════ 动画: 骨架屏 ════════ */
.skeleton {
    background: linear-gradient(
        90deg,
        """ + PALETTE["border"] + """ 25%,
        """ + PALETTE["bg_surface_alt"] + """ 50%,
        """ + PALETTE["border"] + """ 75%
    );
    background-size: 200% 100%;
    animation: skeleton-shimmer 1.6s ease-in-out infinite;
    border-radius: 10px;
}
@keyframes skeleton-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* ════════ 动画: 实时脉冲 ════════ */
.live-pulse {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    background: """ + PALETTE["success"] + """;
    animation: live-pulse-anim 2s ease-in-out infinite;
    margin-right: 5px;
    vertical-align: middle;
    box-shadow: 0 0 6px rgba(16,185,129,0.4);
}
@keyframes live-pulse-anim {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.65); }
}

/* ════════ 动画: 价格闪烁 ════════ */
.price-update {
    animation: price-flash 0.8s ease-out;
}
@keyframes price-flash {
    0% { background: rgba(200,146,58,0.15); border-radius: 4px; }
    100% { background: transparent; }
}

/* ════════ 动画: Staggered FadeUp (商业级入场) ════════ */
.stagger-reveal {
    opacity: 0;
    animation: fadeUpStagger 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes fadeUpStagger {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ═══════════════════════════════════════
   自定义组件样式
   ═══════════════════════════════════════ */

/* ── 侧边栏价格行 ── */
.sidebar-price-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78rem;
    padding: 5px 8px;
    margin: 2px 0;
    border-radius: 8px;
    transition: background 0.15s ease;
}
.sidebar-price-row:hover {
    background: """ + PALETTE["accent_subtle"] + """;
}
.sidebar-price-name {
    font-weight: 500;
    color: """ + PALETTE["text_secondary"] + """;
    min-width: 44px;
}
.sidebar-price-val {
    font-weight: 700;
    color: """ + PALETTE["text_primary"] + """;
}
.sidebar-price-chg {
    font-weight: 600;
    font-size: 0.74rem;
    min-width: 58px;
    text-align: right;
}

/* ── 快讯条目 ── */
.news-item {
    display: flex;
    align-items: flex-start;
    padding: 5px 0;
    border-bottom: 1px solid """ + PALETTE["border_light"] + """;
    font-size: 0.76rem;
    line-height: 1.4;
}
.news-item:last-child { border-bottom: none; }
.news-time {
    color: """ + PALETTE["accent"] + """;
    min-width: 44px;
    font-weight: 600;
    font-size: 0.68rem;
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
    font-size: 0.7rem;
    font-weight: 600;
}

/* ── 数据源指示器 ── */
.datasource-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 10px;
    font-size: 0.76rem;
    font-weight: 500;
    margin: 4px 0;
}

/* ── 毛玻璃叠层(弹窗/模态) ── */
.glass-overlay {
    background: """ + PALETTE["bg_overlay"] + """;
    backdrop-filter: blur(16px) saturate(140%);
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
}


/* ═══════════════════════════════════════
   响应式 — 移动端 & 平板适配
   ═══════════════════════════════════════ */

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
    h2 { font-size: 0.92rem !important; }
    h3 { font-size: 0.85rem !important; }
    h4 { font-size: 0.8rem !important; }

    [data-testid="stSidebar"] { min-width: 280px !important; max-width: 88vw !important; }
    [data-testid="stSidebar"] .block-container { padding: 0.4rem 0.6rem !important; }

    div[role="radiogroup"] > label {
        padding: 11px 14px !important; font-size: 0.88rem !important;
        min-height: 48px; display: flex !important; align-items: center;
        border-radius: 10px !important; margin-bottom: 3px !important;
    }
    [data-testid="stMetric"] { padding: 10px 12px !important; border-radius: 10px; }
    [data-testid="stMetricLabel"] { font-size: 0.64rem !important; }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
    [data-testid="stMetricDelta"] { font-size: 0.68rem !important; }

    .stButton > button {
        padding: 11px 16px !important; min-height: 48px;
        font-size: 0.88rem !important; width: 100% !important;
        border-radius: 10px !important;
    }
    .stDataFrame { overflow-x: auto !important; -webkit-overflow-scrolling: touch; border-radius: 8px; }
    .stDataFrame thead th {
        font-size: 0.64rem !important; padding: 6px 8px !important;
        white-space: nowrap; position: sticky; top: 0; z-index: 2;
    }
    .stDataFrame tbody td { font-size: 0.72rem !important; padding: 6px 8px !important; }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 14px !important; font-size: 0.78rem !important;
        min-height: 48px; flex: 1; text-align: center;
        border-radius: 10px 10px 0 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        display: flex; flex-wrap: nowrap; overflow-x: auto;
        -webkit-overflow-scrolling: touch; gap: 2px; scrollbar-width: none;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }

    .streamlit-expanderHeader {
        padding: 12px 14px !important; font-size: 0.82rem !important;
        min-height: 48px; border-radius: 10px !important;
    }
    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput input, .stNumberInput input {
        font-size: 16px !important; min-height: 48px;
        padding: 10px 14px !important; border-radius: 10px !important;
    }
    .rec-card { padding: 10px 12px !important; margin: 4px 0 !important; }
    .stCheckbox label { font-size: 0.84rem !important; min-height: 44px; display: flex; align-items: center; }
}

@media (max-width: 480px) {
    .main .block-container {
        padding: 0.3rem 0.2rem 4.2rem 0.2rem !important;
    }
    h1 { font-size: 1rem !important; }
    h2 { font-size: 0.85rem !important; }
    [data-testid="stSidebar"] { min-width: 260px !important; max-width: 92vw !important; }
    [data-testid="stMetric"] { padding: 8px 10px !important; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 0.9rem !important; }
    div[role="radiogroup"] > label { padding: 10px 12px !important; font-size: 0.84rem !important; }
    .stDataFrame thead th { font-size: 0.58rem !important; }
    .stDataFrame tbody td { font-size: 0.66rem !important; }
    .rec-card { padding: 8px 10px !important; border-left-width: 3px !important; }
}
"""


def inject_css():
    """注入全局 CSS"""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
#  UI 组件工厂 v5 — Dark Luxury
# ═════════════════════════════════════════════════════════

def kpi_card(label: str, value: str, delta: str = None, delta_color: str = "normal",
             icon: str = "", col=None):
    """统一 KPI 卡片"""
    target = col or st
    if delta and delta_color == "normal":
        if delta.startswith("-"):
            delta_color = "inverse"
    target.metric(f"{icon} {label}" if icon else label, value, delta, delta_color=delta_color)


def section_header(title: str, subtitle: str = "", icon: str = ""):
    """段落标题 — 金色渐变左侧装饰条"""
    icon_str = f"{icon} " if icon else ""
    base = f"""
    <div style="display:flex;align-items:center;gap:8px;margin:6px 0 2px 0;">
        <div style="width:3px;height:18px;border-radius:2px;
                    background:{PALETTE['gradient_glow']};box-shadow:0 0 6px rgba(200,146,58,0.2);"></div>
        <span style="font-size:0.92rem;font-weight:600;color:{PALETTE['text_primary']};">
            {icon_str}{title}</span></div>"""
    if subtitle:
        base += f'<div style="font-size:0.72rem;color:{PALETTE["text_muted"]};margin-left:11px;margin-bottom:4px;">{subtitle}</div>'
    st.markdown(base, unsafe_allow_html=True)


def confidence_indicator(confidence: float):
    """信心指数 — 精品进度条 + 药丸标签"""
    pct = int(confidence * 100)
    if confidence >= 0.75:
        color = PALETTE["success"]; bg = PALETTE["success_bg"]; label = "高信心"
    elif confidence >= 0.5:
        color = PALETTE["warning"]; bg = PALETTE["warning_bg"]; label = "中信度"
    else:
        color = PALETTE["danger"]; bg = PALETTE["danger_bg"]; label = "低信心"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
        <div style="flex:1;height:5px;background:{PALETTE['border']};border-radius:3px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:3px;
                        box-shadow:0 0 6px {color}40;transition:width 0.4s;"></div></div>
        <span class="status-badge" style="background:{bg};color:{color};">{label} {pct}%</span></div>""", unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📭", cta: str = None):
    """空状态 — 虚线豪华卡片"""
    html = f"""
    <div style="text-align:center;padding:48px 24px;background:{PALETTE['bg_surface_alt']};
                border:1px dashed {PALETTE['border']};border-radius:14px;margin:12px 0;"
         role="status" aria-label="{message}">
        <div style="font-size:2.5rem;margin-bottom:12px;opacity:0.35;">{icon}</div>
        <div style="font-size:0.9rem;color:{PALETTE['text_muted']};margin-bottom:16px;">{message}</div>"""
    if cta:
        html += f"""
        <a href="#" style="display:inline-block;padding:10px 24px;
            background:{PALETTE['gradient']};color:#FFF;border-radius:8px;
            text-decoration:none;font-weight:600;font-size:0.88rem;box-shadow:{PALETTE['shadow_glow']};">{cta}</a>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def skeleton_card(height: str = "120px", width: str = "100%", count: int = 1):
    """骨架屏 — 暗色匹配"""
    cards = ""
    for _ in range(count):
        cards += f'<div class="skeleton" style="height:{height};width:{width};margin:8px 0;"></div>'
    st.markdown(f'<div role="status" aria-label="加载中" aria-busy="true">{cards}</div>', unsafe_allow_html=True)


def live_indicator(label: str = "实时"):
    """实时数据脉冲指示器"""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:4px;font-size:0.7rem;'
        f'color:{PALETTE["success_text"]};font-weight:600;margin:2px 0;">'
        f'<span class="live-pulse"></span>{label}</div>',
        unsafe_allow_html=True,
    )


def mobile_kpi_row(items: list, cols_per_row: int = 2):
    """移动端友好的 KPI 行"""
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
    pass


def sidebar_section_title(title: str):
    """侧边栏分区标题"""
    st.markdown(f'<div class="sidebar-section-title">{title}</div>', unsafe_allow_html=True)


def sidebar_price_row(metal_type: str, price: float, change_pct: float):
    """侧边栏价格行"""
    sign = "+" if change_pct >= 0 else ""
    color = PALETTE["success_text"] if change_pct >= 0 else PALETTE["danger_text"]
    st.markdown(
        f'<div class="sidebar-price-row">'
        f'<span class="sidebar-price-name">{metal_type}</span>'
        f'<span class="sidebar-price-val">¥{price:,.0f}</span>'
        f'<span class="sidebar-price-chg" style="color:{color};">{sign}{change_pct:.2f}%</span>'
        f'</div>', unsafe_allow_html=True)


def sidebar_news_item(content: str, time_str: str = ""):
    """侧边栏快讯条目"""
    if len(content) > 46:
        content = content[:44] + ".."
    st.markdown(
        f'<div class="news-item">'
        f'<span class="news-time">{time_str}</span>'
        f'<span class="news-content">{content}</span></div>',
        unsafe_allow_html=True)


def datasource_badge(is_real: bool, label: str = ""):
    """数据源状态徽章"""
    if is_real:
        color = PALETTE["success_text"]; bg = PALETTE["success_bg"]
        text = label or "SHFE 实时"
        live_dot = '<span class="live-pulse" style="display:inline-block;margin-right:3px;vertical-align:middle;"></span>'
    else:
        color = PALETTE["warning_text"]; bg = PALETTE["warning_bg"]
        text = label or "本地模拟"
        live_dot = "📀 "
    st.markdown(
        f'<div class="datasource-indicator" style="background:{bg};color:{color};"'
        f' role="status" aria-label="数据源: {text}">{live_dot}{text}</div>',
        unsafe_allow_html=True)


def news_item_card(content: str, time_str: str = ""):
    """主内容区快讯 — 金色左侧色条"""
    st.markdown(
        f'<div style="display:flex;align-items:flex-start;padding:6px 0;'
        f'border-bottom:1px solid {PALETTE["border_light"]};font-size:0.8rem;line-height:1.4;">'
        f'<div style="width:3px;min-height:16px;background:{PALETTE["gradient_glow"]};'
        f'border-radius:2px;margin-right:8px;margin-top:2px;flex-shrink:0;'
        f'box-shadow:0 0 4px rgba(200,146,58,0.15);"></div>'
        f'<span style="color:{PALETTE["accent"]};min-width:44px;font-weight:600;'
        f'font-size:0.68rem;flex-shrink:0;padding-top:1px;">{time_str}</span>'
        f'<span style="color:{PALETTE["text_secondary"]};flex:1;">{content}</span></div>',
        unsafe_allow_html=True)


def backtest_outcome_card(outcome: dict):
    """回测结果卡片"""
    correct = outcome.get("was_correct")
    if correct is True:
        bg = PALETTE["success_bg"]; border = PALETTE["success"]; tag = "✓"
    elif correct is False:
        bg = PALETTE["danger_bg"]; border = PALETTE["danger"]; tag = "✗"
    else:
        bg = PALETTE["bg_surface_alt"]; border = PALETTE["border"]; tag = "—"
    st.markdown(
        f'<div style="background:{bg};border-left:3px solid {border};'
        f'padding:10px 14px;margin:4px 0;border-radius:10px;'
        f'font-size:0.8rem;display:flex;justify-content:space-between;align-items:center;'
        f'flex-wrap:wrap;gap:6px;">'
        f'<span style="font-weight:500;color:{PALETTE["text_primary"]};">'
        f'{outcome["date"]} <b>{outcome["metal_type"]}</b> '
        f'{outcome["action"]}({outcome["confidence"]:.0%})</span>'
        f'<span style="white-space:nowrap;color:{PALETTE["text_secondary"]};">'
        f'{tag} 3d:{outcome.get("outcome_3d","?")}% '
        f'7d:{outcome.get("outcome_7d","?")}% '
        f'30d:{outcome.get("outcome_30d","?")}%</span></div>',
        unsafe_allow_html=True)


def roi_display(roi_pct: float, target: float = 30.0):
    """ROI 展示 — 暗色豪华版"""
    color = PALETTE["success_text"] if roi_pct >= 0 else PALETTE["danger_text"]
    bg = PALETTE["success_bg"] if roi_pct >= 0 else PALETTE["danger_bg"]
    progress = min(abs(roi_pct) / target, 1.0)
    st.markdown(f"""
    <div style="text-align:center;padding:28px 20px;background:{PALETTE['bg_surface_alt']};
                border:1px solid {PALETTE['border']};border-radius:14px;margin:8px 0;">
        <div style="font-size:0.78rem;color:{PALETTE['text_muted']};margin-bottom:10px;
                    text-transform:uppercase;letter-spacing:0.8px;">总投资回报率</div>
        <div style="font-size:2.6rem;font-weight:800;color:{color};line-height:1;"
        >{roi_pct:+.2f}%</div>
        <div style="margin-top:12px;height:6px;background:{PALETTE['border']};
                    border-radius:3px;overflow:hidden;max-width:280px;margin-left:auto;margin-right:auto;">
            <div style="width:{progress*100}%;height:100%;background:{color};
                        border-radius:3px;box-shadow:0 0 8px {color}40;"></div></div>
        <div style="color:{PALETTE['text_muted']};font-size:0.72rem;margin-top:8px;">
            目标: {target:.0f}% | 当前: {roi_pct:.2f}%</div></div>""", unsafe_allow_html=True)


def factor_scores_card(ta: dict):
    """多因子评分 — 暗色标签式"""
    rows = [
        ("📊", "技术面", [
            ("趋势", ta.get('trend_score', '-')), ("动量", ta.get('momentum_score', '-')),
            ("波动", ta.get('volatility_score', '-')), ("支撑", ta.get('sr_score', '-')),
            ("量价", ta.get('volume_score', '-')), ("状态", ta.get('regime_score', '-')),
            ("背离", ta.get('divergence_score', '-')),
        ]),
        ("🌍", "基本面", [
            ("季节性", ta.get('seasonal_score', '-')), ("联动性", ta.get('correlation_score', '-')),
            ("宏观", ta.get('macro_score', '-')), ("多周期", ta.get('timeframe_score', '-')),
            ("供需", ta.get('supply_demand_score', '-')),
        ]),
        ("🏭", "运营面", [
            ("运营", ta.get('operational_score', '-')), ("风控", ta.get('risk_score', '-')),
        ]),
    ]
    composite = ta.get('composite_score', 0)
    if isinstance(composite, (int, float)):
        if composite >= 70: comp_color = PALETTE["success_text"]; comp_bg = PALETTE["success_bg"]
        elif composite >= 45: comp_color = PALETTE["warning_text"]; comp_bg = PALETTE["warning_bg"]
        else: comp_color = PALETTE["danger_text"]; comp_bg = PALETTE["danger_bg"]
    else: comp_color = PALETTE["text_muted"]; comp_bg = PALETTE["bg_surface_alt"]

    html = [
        f'<div style="background:{PALETTE["bg_surface_alt"]};border:1px solid {PALETTE["border"]};'
        f'border-radius:12px;padding:14px 16px;margin:6px 0;">',
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">'
        f'<span style="background:{comp_bg};color:{comp_color};padding:3px 12px;border-radius:6px;'
        f'font-size:0.85rem;font-weight:700;">综合 {composite}/100</span></div>',
    ]
    for icon, title, items in rows:
        badges = " ".join(
            f'<span style="background:{PALETTE["bg_surface"]};color:{PALETTE["text_secondary"]};'
            f'border:1px solid {PALETTE["border"]};padding:1px 7px;border-radius:4px;'
            f'font-size:0.68rem;margin:1px;white-space:nowrap;display:inline-block;">{k}:{v}</span>'
            for k, v in items)
        html.append(
            f'<div style="display:flex;align-items:flex-start;gap:4px;margin:3px 0;flex-wrap:wrap;">'
            f'<span style="font-size:0.7rem;flex-shrink:0;color:{PALETTE["accent"]};min-width:38px;font-weight:500;">'
            f'{icon} {title}</span><span style="flex:1;min-width:0;">{badges}</span></div>')
    html.append('</div>')
    st.markdown("\n".join(html), unsafe_allow_html=True)


def recommendation_card(rec: dict, index: int, action_type: str):
    """推荐卡片 v5 — Dark Luxury 精品"""
    ta = rec.get('trend_analysis', {})
    confidence = rec.get('confidence', 0)
    is_buy = action_type == "buy"
    actual_action = rec.get('action', '买入' if is_buy else '卖出')

    if actual_action in ("买入", "加仓"):
        accent = PALETTE["success_text"]; accent_bg = PALETTE["success_bg"]
        emoji = "🟢" if actual_action == "买入" else "📈"
    elif actual_action in ("卖出", "减仓"):
        accent = PALETTE["danger_text"]; accent_bg = PALETTE["danger_bg"]
        emoji = "🔴" if actual_action == "卖出" else "📉"
    elif actual_action == "止损":
        accent = "#F87171"; accent_bg = "rgba(239,68,68,0.12)"; emoji = "🚨"
    elif actual_action == "观望":
        accent = PALETTE["warning_text"]; accent_bg = PALETTE["warning_bg"]; emoji = "⏸️"
    else:
        accent = PALETTE["success_text"] if is_buy else PALETTE["danger_text"]
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
    risk_map = {"低": (PALETTE["success_text"], PALETTE["success_bg"]),
                "中": (PALETTE["warning_text"], PALETTE["warning_bg"]),
                "高": (PALETTE["danger_text"], PALETTE["danger_bg"])}
    risk_c, risk_bg = risk_map.get(risk, (PALETTE["text_muted"], PALETTE["bg_surface_alt"]))

    html = f"""
    <div class="rec-card" style="background:{PALETTE['bg_surface']};
        border:1px solid {PALETTE['border']};border-left:4px solid {accent};
        border-radius:12px;padding:16px 18px;margin:8px 0;
        transition:all 0.25s cubic-bezier(0.16,1,0.3,1);box-shadow:{PALETTE['shadow_sm']};">
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:10px;flex-wrap:wrap;gap:6px;">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                <span style="font-size:0.68rem;color:{PALETTE['text_muted']};">#{index}</span>
                <span style="font-size:1rem;font-weight:700;color:{PALETTE['text_primary']};">
                    {rec['metal_type']}</span>
                <span style="background:{accent_bg};color:{accent};padding:2px 8px;
                             border-radius:10px;font-size:0.7rem;font-weight:600;white-space:nowrap;">
                    {emoji} {actual_action}</span>
                <span style="background:{risk_bg};color:{risk_c};padding:2px 6px;
                             border-radius:6px;font-size:0.66rem;font-weight:600;">风险:{risk}</span></div>
            <span style="font-size:1.1rem;font-weight:700;color:{PALETTE['text_primary']};">
                ¥{price:,.0f}</span></div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:0.76rem;color:{PALETTE['text_muted']};">
            <span>🎯 止损: <b style="color:{PALETTE['danger_text']};">¥{sl:,.0f}</b></span>
            <span>🏁 止盈: <b style="color:{PALETTE['success_text']};">¥{tp:,.0f}</b></span>
            <span>📦 仓位: <b style="color:{PALETTE['accent_hover']};">{qty:.0f}%</b></span>
            {profit_line}{agree_line}</div></div>"""
    st.markdown(html, unsafe_allow_html=True)
    confidence_indicator(confidence)


def plotly_theme() -> dict:
    """Plotly 浅色主题"""
    return dict(
        template="plotly_white",
        paper_bgcolor=PALETTE["bg_surface"],
        plot_bgcolor=PALETTE["bg_surface_alt"],
        font=dict(color=PALETTE["text_muted"], size=12),
        title_font=dict(color=PALETTE["text_primary"], size=14),
        legend=dict(font=dict(color=PALETTE["text_muted"])),
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(gridcolor=PALETTE["border"], zerolinecolor=PALETTE["border"],
                   linecolor=PALETTE["border"], tickfont=dict(color=PALETTE["text_muted"])),
        yaxis=dict(gridcolor=PALETTE["border"], zerolinecolor=PALETTE["border"],
                   linecolor=PALETTE["border"], tickfont=dict(color=PALETTE["text_muted"])),
        coloraxis_colorbar=dict(tickfont=dict(color=PALETTE["text_muted"]),
                                title_font=dict(color=PALETTE["text_muted"])),
    )


def styled_plotly(fig):
    """应用深色主题"""
    fig.update_layout(**plotly_theme())
    return fig


PLOTLY_FAST_CONFIG = {"displayModeBar": False, "responsive": True, "displaylogo": False}
