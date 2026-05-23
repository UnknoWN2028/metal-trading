"""
有色金属回收倒卖AI系统 v3 — 专业版UI
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, SessionLocal
from services.price_service import MetalPriceService
from services.inventory_service import InventoryService
from services.recommendation_service import RecommendationService
from services.alert_service import AlertService
from services.llm_service import LLMService
from services.news_service import NewsService
from services.feedback_service import FeedbackService
from web.styles import (
    inject_css, kpi_card, section_header,
    confidence_indicator, empty_state, factor_scores_card,
    recommendation_card, styled_plotly, plotly_theme,
    mobile_kpi_row, mobile_bottom_nav,
    PLOTLY_FAST_CONFIG,
)
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ═══════════════════════════════════════════════════════════
#  页面配置 & 样式注入
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="有色金属回收AI系统",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── 移动端检测 JS ──
st.markdown("""
<script>
(function() {
    var w = window.innerWidth;
    var div = document.createElement('div');
    div.setAttribute('data-mobile-detected', w < 768 ? '1' : '0');
    div.id = 'mobile-detector';
    div.style.display = 'none';
    document.body.appendChild(div);
})();
</script>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  服务初始化
# ═══════════════════════════════════════════════════════════
@st.cache_resource
def init_services():
    init_db()
    sf = SessionLocal
    price_svc = MetalPriceService(sf)
    llm_svc = LLMService()
    return {
        "price": price_svc,
        "inventory": InventoryService(sf),
        "recommendation": RecommendationService(sf, price_service=price_svc, llm_service=llm_svc),
        "alert": AlertService(sf),
        "session": sf,
        "llm": llm_svc,
        "news": NewsService(),
        "feedback": FeedbackService(sf, price_svc),
    }

services = init_services()

def _safe_toast(msg, icon=None):
    """安全 toast（兼容旧版 Streamlit）"""
    try:
        st.toast(msg, icon=icon)
    except AttributeError:
        pass  # 旧版无 toast，静默跳过

def _invalidate_sidebar():
    """标脏侧边栏缓存，下次渲染时自动刷新"""
    st.session_state["_price_ver"] = st.session_state.get("_price_ver", 0) + 1

# ═══════════════════════════════════════════════════════════
#  启动时自动连接实时数据源
# ═══════════════════════════════════════════════════════════
if "_auto_connected" not in st.session_state:
    st.session_state["_auto_connected"] = True
    if not services["price"].is_using_real_data:
        result = services["price"].auto_connect()
        if result["success"]:
            _safe_toast(f"✅ {result['message']}")
        else:
            _safe_toast(f"⚠️ {result.get('message', 'SHFE连接失败')}")
        _invalidate_sidebar()
        st.rerun()

# 🆕 启动时检查推荐回测结果
if "_feedback_checked" not in st.session_state:
    st.session_state["_feedback_checked"] = True
    fb = services["feedback"].check_outcomes()
    if fb.get("checked", 0) > 0:
        _safe_toast(f"🧪 已回测{fb['checked']}条历史推荐")


# ═══════════════════════════════════════════════════════
#  静默后台刷新（仅在数据过期时触发一次 rerun，防抖 45s）
# ═══════════════════════════════════════════════════════
_real_enabled = services["price"].is_using_real_data
if _real_enabled:
    last_up = services["price"].last_update_time
    now_ts = datetime.now()
    last_rerun_ts = st.session_state.get("_last_data_rerun")
    if last_up:
        data_age = (now_ts - last_up).total_seconds()
    else:
        data_age = 999
    need_rerun = data_age > 30
    can_rerun = (last_rerun_ts is None or (now_ts - last_rerun_ts).total_seconds() > 45)
    if need_rerun and can_rerun:
        services["price"].refresh_spot_only()
        st.session_state["_last_data_rerun"] = now_ts
        st.cache_data.clear()
        st.rerun()


# ═══════════════════════════════════════════════════════════
#  缓存装饰器 — v3.3 优化TTL + 批量预取
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)  # 🆕 60s→300s，侧边栏不需要秒级刷新
def get_cached_prices():
    return services["price"].fetch_all_current_prices()

@st.cache_data(ttl=300, show_spinner=False)  # 🆕 60s→300s
def get_cached_summaries():
    return services["price"].get_all_price_summaries()

@st.cache_data(ttl=600, show_spinner="🧠 多因子引擎分析中...")  # 🆕 300s→600s，仪表盘不需要实时推荐
def get_cached_recommendations():
    return services["recommendation"].get_top_opportunities(top_n=5)

@st.cache_data(ttl=120, show_spinner=False)  # 🆕 60s→120s
def get_inventory_summary():
    return services["inventory"].get_inventory_summary()

@st.cache_data(ttl=120, show_spinner=False)  # 🆕 60s→120s
def get_profit_summary(days=30):
    return services["inventory"].get_profit_summary(days=days)

@st.cache_data(ttl=120, show_spinner=False)  # 🆕 60s→120s
def get_all_inventory():
    return services["inventory"].get_all_inventory()

@st.cache_data(ttl=120, show_spinner=False)  # 🆕 60s→120s
def get_transactions(limit=100):
    return services["inventory"].get_transaction_history(limit=limit)

@st.cache_data(ttl=600, show_spinner=False)  # 🆕 300s→600s
def get_history_cached(metal, days):
    df, _src = services["price"].get_historical_prices(metal, days=days)
    return df

@st.cache_data(ttl=600, show_spinner=False)  # 🆕 300s→600s，新闻不需要频繁刷新
def get_news_headlines(limit=8):
    return services["news"].get_market_headlines(limit=limit)


# ═══════════════════════════════════════════════════════════
#  侧边栏数据缓存（版本号驱动，避免时间TTL盲区）
# ═══════════════════════════════════════════════════════════
def _sidebar_fetch():
    """统一获取侧边栏价格+快讯，结果存入session_state"""
    # 价格和快讯分开取，一个挂了不影响另一个
    try:
        st.session_state["_sidebar_prices"] = get_cached_prices()
    except Exception:
        st.session_state.setdefault("_sidebar_prices", [])
    try:
        st.session_state["_sidebar_news"] = get_news_headlines(5)
    except Exception:
        st.session_state.setdefault("_sidebar_news", [])
    st.session_state["_sidebar_ver"] = st.session_state.get("_price_ver", 0)

# 首次或版本过期时刷新
_cur_ver = st.session_state.get("_price_ver", 0)
_cached_ver = st.session_state.get("_sidebar_ver", -1)
if "_sidebar_prices" not in st.session_state or _cur_ver != _cached_ver:
    _sidebar_fetch()

_sidebar_prices = st.session_state.get("_sidebar_prices", [])
_sidebar_news = st.session_state.get("_sidebar_news", [])


# ═══════════════════════════════════════════════════════════
#  侧边栏
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:8px 0 12px 0;">'
        '<span style="font-size:1.3rem;font-weight:800;'
        'background:linear-gradient(90deg,#C8923A,#D4832A);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        'background-clip:text;">🔩 Metal AI Trading</span>'
        '<div style="font-size:0.72rem;color:#9CA3AF;margin-top:2px;">v3.4 统计增强版</div></div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "📋 导航",
        ["📊 仪表盘", "💰 实时行情", "📦 库存管理", "🤖 AI推荐",
         "📈 走势分析", "🔔 价格预警", "📋 交易记录", "👥 客户供应商", "📊 利润分析", "🧪 回测"],
        label_visibility="collapsed",
        key="nav_page",
    )

    st.markdown("---")

    # 数据源
    st.caption("📡 数据源")
    real_enabled = services["price"].is_using_real_data
    if real_enabled:
        st.success("⚡ SHFE 实时行情")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("🔄 刷新价格", width='stretch',
                         help="获取最新SHFE报价+5分钟K线"):
                with st.spinner("刷新中..."):
                    refresh_r = services["price"].refresh_realtime_prices()
                    if refresh_r["success"]:
                        _safe_toast(f"✅ {refresh_r['message']}")
                    else:
                        _safe_toast(f"⚠️ {refresh_r['message']}")
                    st.cache_data.clear()
                    _invalidate_sidebar()
                    st.rerun()
        with col_r2:
            if st.button("📴 模拟", width='stretch'):
                services["price"].use_simulated()
                st.cache_data.clear()
                _invalidate_sidebar()
                st.rerun()
    else:
        st.warning("📀 本地模拟数据")
        if st.button("📡 连接实时行情", width='stretch',
                     help="从上海期货交易所获取实时数据"):
            with st.spinner("连接SHFE..."):
                result = services["price"].try_fetch_real()
                if result["success"]:
                    _safe_toast(f"✅ {result['message']}")
                else:
                    _safe_toast(f"⚠️ {result.get('message', '连接失败')}")
                st.cache_data.clear()
                _invalidate_sidebar()
                st.rerun()

    # LLM
    st.caption("🧠 AI 状态")
    if services.get("llm") and services["llm"].available:
        st.success("DeepSeek 已连接")
    else:
        st.warning("未配置 API Key")

    st.markdown("---")
    st.caption("⚡ 快速行情")
    try:
        shown = 0
        for p in _sidebar_prices[:6]:
            if not p or not p.get("price"):
                continue
            shown += 1
            chg = p.get('change_pct', 0)
            sign = "+" if chg >= 0 else ""
            color = "#10B981" if chg >= 0 else "#EF4444"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:0.82rem;margin:3px 0;">'
                f'<span style="color:#6B7280;">'
                f'{p["metal_type"]}</span>'
                f'<span style="color:#1A1D26;font-weight:600;">¥{p["price"]:,.0f}</span>'
                f'<span style="color:{color};font-weight:600;">{sign}{chg:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
        if shown == 0:
            st.caption("（数据加载中...）")
    except Exception:
        st.caption("（行情暂不可用）")

    st.markdown("---")
    st.caption("📰 金属快讯")
    try:
        if _sidebar_news:
            for h in _sidebar_news[:5]:
                content = h['content']
                if len(content) > 50:
                    content = content[:48] + ".."
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#1A1D26;padding:1px 0;'
                    f'border-left:2px solid #C8923A;padding-left:6px;margin:2px 0;'
                    f'line-height:1.3;">{content}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("（暂无快讯）")
    except Exception:
        pass

    st.markdown("---")
    # 数据更新时间 & 自动刷新（仅展示，不触发 rerun）
    if real_enabled:
        last_up = services["price"].last_update_time
        if last_up:
            elapsed = (datetime.now() - last_up).total_seconds()
            age_str = f"{elapsed:.0f}秒前" if elapsed < 120 else f"{elapsed/60:.0f}分钟前"
            st.caption(f"📡 上海期货交易所")
            st.caption(f"⏱️ 更新: {last_up.strftime('%H:%M:%S')} ({age_str})")
        else:
            st.caption(f"📡 数据源: SHFE")

        # 自动刷新开关（控制 JS 轮询）
        auto_key = "_auto_refresh"
        if auto_key not in st.session_state:
            st.session_state[auto_key] = True
        auto_refresh = st.checkbox("⏱️ 每120秒自动刷新", value=st.session_state[auto_key],
                                   key="auto_refresh_cb")
        st.session_state[auto_key] = auto_refresh
    else:
        st.caption(f"📀 数据源: 本地模拟")

    col_r, col_v = st.columns([3, 2])
    with col_r:
        if st.button("🔄 强制刷新", width='stretch'):
            st.cache_data.clear()
            _invalidate_sidebar()
            st.rerun()
        # 🆕 轻量刷新按钮（仅刷新价格+快讯，不重算AI，不跳页）
        lite_clicked = st.button("LITE", width='stretch',
                                 key="_lite_refresh",
                                 help="轻量刷新（仅更新侧边栏数据）")
        if lite_clicked:
            _invalidate_sidebar()
            st.rerun()
    with col_v:
        st.caption(datetime.now().strftime("%H:%M"))


# ── 自动刷新注入（每120秒仅更新侧边栏数据，不清缓存不重算AI） ──
if real_enabled and st.session_state.get("_auto_refresh", True):
    st.markdown(
        """
        <script>
        if (!window._metalAutoRefresh) {
            window._metalAutoRefresh = setInterval(function() {
                var btns = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.indexOf('LITE') >= 0) {
                        btns[i].click(); break;
                    }
                }
            }, 120000);
        }
        </script>
        """,
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════
#  📊 仪表盘
# ═══════════════════════════════════════════════════════════
if page == "📊 仪表盘":
    st.title("📊 仪表盘总览")

    inv_s = get_inventory_summary()
    prof = get_profit_summary(30)
    mobile_kpi_row([
        ("库存总价值", f"¥{inv_s['total_value']:,.0f}", f"{inv_s['profit_pct']:+.1f}%", "normal", "💎"),
        ("浮动盈亏", f"¥{inv_s['total_profit']:,.0f}", None, "normal", "📈"),
        ("30天利润", f"¥{prof['total_profit']:,.0f}", f"{prof['total_sell_transactions']}笔交易", "normal", "🏆"),
        ("库存品类", str(inv_s['total_items']), f"{len(inv_s.get('by_metal', {}))}种金属", "normal", "📦"),
    ], cols_per_row=2)

    st.markdown("---")

    left, right = st.columns(2)
    with left:
        section_header("🔥 行情热力", "各金属日涨跌幅一览")
        summaries = get_cached_summaries()
        if summaries:
            df_s = pd.DataFrame(summaries)
            fig = px.bar(
                df_s, x='metal_type', y='change_day',
                color='change_day',
                color_continuous_scale=[
                    (0, '#EF4444'), (0.45, '#9CA3AF'), (0.5, '#6B7280'),
                    (0.55, '#9CA3AF'), (1, '#10B981')
                ],
                labels={'change_day': '涨跌%', 'metal_type': ''},
            )
            fig.update_traces(marker=dict(line=dict(width=0)))
            styled_plotly(fig)
            fig.update_layout(height=320, showlegend=False)
            st.plotly_chart(fig, width='stretch', config=PLOTLY_FAST_CONFIG)

    with right:
        section_header("📦 库存分布", "持仓市值构成")
        bm = inv_s.get("by_metal", {})
        if bm:
            df_pie = pd.DataFrame([
                {"金属": k, "市值": v["total_value"]}
                for k, v in bm.items()
            ])
            colors_pie = [
                '#C8923A', '#D4832A', '#B07E30', '#9C6E28',
                '#F59E0B', '#D4832A', '#A07030', '#CD853F',
            ]
            fig = px.pie(
                df_pie, values='市值', names='金属',
                color_discrete_sequence=colors_pie,
            )
            fig.update_traces(
                textposition='inside', textinfo='percent+label',
                textfont=dict(size=12, color='#FFFFFF'),
                marker=dict(line=dict(color='#FFFFFF', width=2)),
            )
            styled_plotly(fig)
            fig.update_layout(height=320, showlegend=False)
            st.plotly_chart(fig, width='stretch', config=PLOTLY_FAST_CONFIG)
        else:
            empty_state("暂无库存数据", "📦")

    st.markdown("---")

    section_header("🤖 AI 智能推荐", "v3.4 多因子分析 · 点击「AI推荐」页面查看详情")
    # 🆕 仪表盘不再触发全量分析，仅显示最近缓存结果或跳转提示
    try:
        # 尝试从 session_state 读取最近一次AI分析结果（由AI推荐页写入）
        latest_recs = st.session_state.get("_latest_recs")
        if latest_recs:
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown("#### 🟢 推荐买入")
                for i, rec in enumerate(latest_recs.get("top_buy", [])[:2], 1):
                    recommendation_card(rec, i, "buy")
                if not latest_recs.get("top_buy"):
                    st.caption("暂无强烈买入信号")
            with rc2:
                st.markdown("#### 🔴 推荐卖出")
                for i, rec in enumerate(latest_recs.get("top_sell", [])[:2], 1):
                    recommendation_card(rec, i, "sell")
                if not latest_recs.get("top_sell"):
                    st.caption("暂无强烈卖出信号")
        else:
            st.info("💡 切换到「🤖 AI推荐」页面运行多因子分析引擎", icon="🧠")
    except Exception:
        st.info("💡 切换到「🤖 AI推荐」页面运行多因子分析引擎", icon="🧠")

    st.markdown("---")
    section_header("📋 最近交易", "")
    txns = get_transactions(5)
    if txns:
        df_txn = pd.DataFrame(txns)[[
            'date', 'type', 'metal', 'quantity_kg',
            'price_per_kg', 'total', 'profit',
        ]]
        df_txn.columns = ['日期', '类型', '金属', '数量kg', '单价', '总额', '利润']
        st.dataframe(df_txn, width='stretch', hide_index=True)
    else:
        empty_state("暂无交易记录", "📝")

    st.markdown("---")
    section_header("📰 金属快讯", "上海金属网 · 最新行情动态")
    headlines = get_news_headlines(10)
    if headlines:
        for h in headlines:
            content = h['content']
            time_str = h.get('time', '')
            if time_str:
                time_str = time_str[-8:] if len(time_str) > 8 else time_str
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;padding:4px 0;'
                f'border-bottom:1px solid #1F2937;font-size:0.82rem;">'
                f'<span style="color:#C8923A;min-width:52px;font-weight:600;'
                f'font-size:0.72rem;">{time_str}</span>'
                f'<span style="color:#1A1D26;flex:1;">{content}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("暂无快讯数据", "📰")

    # 🆕 v3.4 诊断面板（定位全"观望"根因）
    with st.expander("🔧 引擎诊断", expanded=False):
        st.caption("数据源检查 & 指标抽样")
        try:
            from config import METAL_TYPES
            for mt in list(METAL_TYPES.keys())[:4]:
                df, src = services["price"].get_historical_prices(mt, 120)
                ind = services["recommendation"]._compute_indicators(df['price'].values)
                # 🆕 跑一遍完整分析拿综合分和背离分
                result = services["recommendation"].analyze_and_recommend(mt, save_to_db=False)
                ta = result.get('trend_analysis', {})
                st.markdown(
                    f"**{mt}** | 数据源:`{src}` | 数据点:`{ind['n']}` | "
                    f"综合分:`{ta.get('composite_score','?')}` | "
                    f"背离分:`{ta.get('divergence_score','?')}` | "
                    f"决策:`{result['action']}`({result['confidence']}) | "
                    f"RSI:`{ind['rsi']:.1f}` | ADX:`{ind.get('adx',15):.0f}`"
                )
        except Exception as e:
            st.error(f"诊断异常: {e}")


# ═══════════════════════════════════════════════════════════
#  💰 实时行情
# ═══════════════════════════════════════════════════════════
elif page == "💰 实时行情":
    st.title("💰 实时行情")

    summaries = get_cached_summaries()
    if summaries:
        df = pd.DataFrame(summaries).rename(columns={
            'metal_type': '金属', 'current_price': '现价',
            'change_day': '日涨跌%', 'change_week': '周涨跌%',
            'change_month': '月涨跌%', 'ma7': 'MA7', 'ma30': 'MA30',
            'trend': '趋势', 'support': '支撑', 'resistance': '阻力',
            'volatility': '波动率%',
        })
        st.dataframe(df, width='stretch', hide_index=True)

    st.markdown("---")
    section_header("🔍 金属详情", "选择金属查看完整技术指标")
    metals = [s['metal_type'] for s in summaries] if summaries else []
    sel = st.selectbox("选择金属", metals, label_visibility="collapsed")

    if sel:
        s = services["price"].get_price_summary(sel)
        if s:
            chg_day = s['change_day']
            chg_color = "normal" if chg_day >= 0 else "inverse"
            # 统一使用 mobile_kpi_row：桌面端5列，移动端2列
            mobile_kpi_row([
                ("💰 当前价格", f"¥{s['current_price']:,.0f}", f"{s['change_day']:+.2f}%", chg_color, sel),
                ("周涨跌", f"{s['change_week']:+.2f}%", None, "normal", "📅"),
                ("月涨跌", f"{s['change_month']:+.2f}%", None, "normal", "📆"),
                ("波动率", f"{s['volatility']:.2f}%", None, "normal", "📊"),
                ("趋势", s['trend'], None, "normal", "📈" if s['trend'] == "上涨" else "📉"),
            ], cols_per_row=2)
            st.caption(f"MA7: ¥{s['ma7']:,.0f} | MA30: ¥{s['ma30']:,.0f} | 支撑: ¥{s['support']:,.0f} | 阻力: ¥{s['resistance']:,.0f}")

            st.caption(f"数据源: {s['source']} | 更新: {s.get('timestamp', '')}")


# ═══════════════════════════════════════════════════════════
#  📦 库存管理
# ═══════════════════════════════════════════════════════════
elif page == "📦 库存管理":
    st.title("📦 库存管理")

    inv_s = get_inventory_summary()
    mobile_kpi_row([
        ("总成本", f"¥{inv_s['total_cost']:,.0f}", None, "normal", "💰"),
        ("总市值", f"¥{inv_s['total_value']:,.0f}", None, "normal", "💎"),
        ("浮动盈亏", f"¥{inv_s['total_profit']:,.0f}", f"{inv_s['profit_pct']:+.1f}%", "normal", "📊"),
        ("持仓条目", str(inv_s['total_items']), None, "normal", "📋"),
    ], cols_per_row=2)

    tab1, tab2 = st.tabs(["📋 查看库存", "➕ 入库"])

    with tab1:
        inv = get_all_inventory()
        if inv:
            df_inv = pd.DataFrame(inv).rename(columns={
                'metal_type': '金属', 'quantity_kg': '数量kg',
                'avg_cost_price': '成本价', 'current_market_price': '市场价',
                'total_cost': '总成本', 'current_value': '市值',
                'profit_loss': '盈亏', 'profit_loss_pct': '盈亏%',
                'storage_location': '仓库', 'quality_grade': '品质',
            })
            st.dataframe(df_inv, width='stretch', hide_index=True)

            st.markdown("---")
            section_header("💰 卖出库存", "")

            inv_map = {
                f"#{i['id']} {i['metal_type']} {i['quantity_kg']}kg | 成本¥{i['avg_cost_price']}"
                : i['id'] for i in inv
            }
            sel_inv = st.selectbox("选择库存条目", list(inv_map.keys()),
                                   label_visibility="collapsed")

            c1, c2, c3 = st.columns(3)
            qty = c1.number_input("卖出数量(kg)", min_value=0.1, step=100.0, value=100.0)
            price = c2.number_input("卖出单价(元/kg)", min_value=0.01, step=1.0, value=100.0)
            buyer = c3.text_input("买家名称")

            note = st.text_area("备注", key="inv_sell_notes", placeholder="交易备注...")

            if st.button("✅ 确认卖出", type="primary", width='stretch'):
                r = services["inventory"].sell_inventory(
                    inv_map[sel_inv], qty, price, buyer, note
                )
                if r["success"]:
                    st.success(r["message"])
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(r["message"])
        else:
            empty_state("暂无库存", "📭")

    with tab2:
        section_header("➕ 新增入库", "")
        from config import METAL_TYPES
        metals = list(METAL_TYPES.keys())
        c1, c2, c3 = st.columns(3)
        m = c1.selectbox("金属类型", metals)
        q = c2.number_input("数量(kg)", min_value=1.0, step=100.0, value=1000.0)
        cost = c3.number_input("购入单价(元/kg)", min_value=0.01, step=1.0, value=100.0)
        c4, c5 = st.columns(2)
        loc = c4.selectbox("仓库", ["主仓库", "A仓库", "B仓库"])
        qual = c5.selectbox("品质", ["一级", "二级", "三级"])
        notes = st.text_area("备注", key="inv_add_notes", placeholder="入库备注...")
        if st.button("📥 确认入库", type="primary", width='stretch'):
            r = services["inventory"].add_inventory(m, q, cost, loc, qual, notes)
            if r["success"]:
                st.success(r["message"])
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(r["message"])


# ═══════════════════════════════════════════════════════════
#  🤖 AI推荐
# ═══════════════════════════════════════════════════════════
elif page == "🤖 AI推荐":
    st.title("🤖 AI 智能交易推荐")

    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        if st.button("🔄 刷新 AI 分析", width='stretch', type="primary"):
            st.cache_data.clear()
            st.rerun()
    with col_info:
        st.caption("v3.4 14因子引擎 · Hurst指数 + 三峰背离 + Half-Kelly + DeepSeek AI")

    try:
        with st.spinner("🧠 多因子引擎分析中..."):
            opps = get_cached_recommendations()
        # 🆕 保存到session_state，仪表盘可直接读取
        st.session_state["_latest_recs"] = opps
        bc, sc = st.columns(2)

        with bc:
            st.markdown("#### 🟢 买入推荐")
            for i, rec in enumerate(opps.get("top_buy", [])[:5], 1):
                recommendation_card(rec, i, "buy")
                with st.expander("📊 评分明细 & 理由"):
                    factor_scores_card(rec.get('trend_analysis', {}))
                    st.caption(rec.get('reason', ''))
                if rec.get('llm_available') and rec.get('llm_analysis'):
                    with st.expander("🧠 DeepSeek AI 分析"):
                        st.markdown(rec['llm_analysis'])
            if not opps.get("top_buy"):
                empty_state("暂无买入信号", "📈")

        with sc:
            st.markdown("#### 🔴 卖出推荐")
            for i, rec in enumerate(opps.get("top_sell", [])[:5], 1):
                recommendation_card(rec, i, "sell")
                with st.expander("📊 评分明细 & 理由"):
                    factor_scores_card(rec.get('trend_analysis', {}))
                    st.caption(rec.get('reason', ''))
                if rec.get('llm_available') and rec.get('llm_analysis'):
                    with st.expander("🧠 DeepSeek AI 分析"):
                        st.markdown(rec['llm_analysis'])
            if not opps.get("top_sell"):
                empty_state("暂无卖出信号", "📉")

        st.markdown("---")
        section_header("📋 全部推荐概览", "")
        all_r = opps.get("all", [])
        if all_r:
            df_r = pd.DataFrame(all_r)
            df_r['操作'] = df_r['action'].map({
                '买入': '🟢买入', '加仓': '📈加仓',
                '卖出': '🔴卖出', '减仓': '📉减仓', '止损': '🚨止损',
                '持有': '⏸️持有', '观望': '👀观望',
            })
            st.dataframe(
                df_r[['metal_type', '操作', 'confidence', 'current_price',
                      'expected_profit_pct', 'risk_level']],
                width='stretch', hide_index=True,
            )

        if services.get("llm") and services["llm"].available:
            st.markdown("---")
            section_header("🧠 DeepSeek AI 深度分析", "单金属专家级分析（约3-8秒）")
            from config import METAL_TYPES
            col_sel, col_go = st.columns([3, 1])
            with col_sel:
                llm_metal = st.selectbox(
                    "选择分析金属", list(METAL_TYPES.keys()),
                    key="llm_metal", label_visibility="collapsed",
                )
            with col_go:
                if st.button("🚀 启动深度分析", type="primary", width='stretch'):
                    with st.spinner(f"DeepSeek 正在分析 {llm_metal} ..."):
                        llm_r = services["recommendation"].enrich_single_with_llm(llm_metal)
                        if llm_r["success"]:
                            res = llm_r["result"]
                            st.success(f"**{res['action']}** | 信心 {res['confidence']:.0%}")
                            st.markdown(res.get('llm_analysis', ''))
                        else:
                            st.error(f"分析失败: {llm_r['message']}")
    except Exception as e:
        st.warning(f"AI 分析引擎启动中，请稍后刷新...")


# ═══════════════════════════════════════════════════════════
#  📈 走势分析
# ═══════════════════════════════════════════════════════════
elif page == "📈 走势分析":
    st.title("📈 价格走势分析")

    from config import METAL_TYPES
    c1, c2 = st.columns([2, 3])
    with c1:
        sel = st.selectbox("选择金属", list(METAL_TYPES.keys()),
                           label_visibility="collapsed")
    with c2:
        days = st.slider("分析周期（天）", 7, 180, 90, label_visibility="collapsed")

    df = get_history_cached(sel, days)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['price'], mode='lines',
        name=sel, line=dict(color='#C8923A', width=2.5),
        fill='tozeroy', fillcolor='rgba(200,146,58,0.08)',
    ))
    if len(df) >= 7:
        ma7 = df['price'].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=df['date'], y=ma7, mode='lines',
            name='MA7', line=dict(color='#3B82F6', width=1.2, dash='dot'),
        ))
    if len(df) >= 30:
        ma30 = df['price'].rolling(30).mean()
        fig.add_trace(go.Scatter(
            x=df['date'], y=ma30, mode='lines',
            name='MA30', line=dict(color='#EF4444', width=1.2, dash='dash'),
        ))
    styled_plotly(fig)
    fig.update_layout(
        title=f"{sel} 价格走势",
        height=420, hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    st.plotly_chart(fig, width='stretch', config=PLOTLY_FAST_CONFIG)

    # 走势统计：使用 mobile_kpi_row 统一布局
    chg = (df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0] * 100
    mobile_kpi_row([
        ("现价", f"¥{df['price'].iloc[-1]:,.0f}", None, "normal", "💵"),
        ("最高", f"¥{df['price'].max():,.0f}", None, "normal", "🔺"),
        ("最低", f"¥{df['price'].min():,.0f}", None, "normal", "🔻"),
        ("均价", f"¥{df['price'].mean():,.0f}", None, "normal", "📊"),
        ("标准差", f"¥{df['price'].std():,.0f}", None, "normal", "📐"),
        ("区间涨跌", f"{chg:+.2f}%", None, "normal", "📈"),
    ], cols_per_row=3)

    st.markdown("---")
    section_header("📊 多金属归一化对比", "")
    cmps = st.multiselect(
        "选择对比金属", list(METAL_TYPES.keys()),
        default=['铜', '铝', '锌'], label_visibility="collapsed",
    )
    if cmps:
        fig2 = go.Figure()
        colors = ['#C8923A', '#3B82F6', '#10B981', '#EF4444',
                  '#F59E0B', '#8B5CF6', '#D4832A', '#6B7280']
        for i, m in enumerate(cmps):
            dm = get_history_cached(m, days)
            norm = dm['price'] / dm['price'].iloc[0] * 100
            fig2.add_trace(go.Scatter(
                x=dm['date'], y=norm, mode='lines',
                name=m, line=dict(color=colors[i % len(colors)], width=1.8),
            ))
        styled_plotly(fig2)
        fig2.update_layout(
            title="归一化对比 (%)",
            height=350, hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            yaxis=dict(ticksuffix='%'),
        )
        st.plotly_chart(fig2, width='stretch', config=PLOTLY_FAST_CONFIG)


# ═══════════════════════════════════════════════════════════
#  🔔 价格预警
# ═══════════════════════════════════════════════════════════
elif page == "🔔 价格预警":
    st.title("🔔 价格预警")

    from config import METAL_TYPES
    metals = list(METAL_TYPES.keys())

    tab1, tab2 = st.tabs(["➕ 新建预警", "📋 活跃预警"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        am = c1.selectbox("金属", metals, key="am")
        at = c2.selectbox("触发条件", ["高于", "低于"])
        ap = c3.number_input("触发价格", min_value=0.01, step=100.0, value=50000.0)
        amsg = st.text_input("备注", placeholder="预警备注...")
        if st.button("✅ 创建预警", type="primary", width='stretch'):
            r = services["alert"].create_alert(am, at, ap, amsg)
            if r["success"]:
                st.success(r["message"])
            else:
                st.error(r["message"])

    with tab2:
        alerts = services["alert"].get_active_alerts()
        if alerts:
            st.dataframe(pd.DataFrame(alerts), width='stretch', hide_index=True)
            al_map = {
                f"#{a['id']} {a['metal_type']} {a['alert_type']} ¥{a['trigger_price']}"
                : a['id'] for a in alerts
            }
            sel_a = st.selectbox("选择要删除的预警", list(al_map.keys()),
                                 label_visibility="collapsed")
            if st.button("🗑️ 删除预警", width='stretch'):
                r = services["alert"].delete_alert(al_map[sel_a])
                if r["success"]:
                    st.success(r["message"])
                else:
                    st.error(r["message"])
        else:
            empty_state("暂无活跃预警", "🔔")


# ═══════════════════════════════════════════════════════════
#  📋 交易记录
# ═══════════════════════════════════════════════════════════
elif page == "📋 交易记录":
    st.title("📋 交易记录")

    txns = get_transactions(100)
    if txns:
        df = pd.DataFrame(txns)
        df['date'] = pd.to_datetime(df['date'])
        buy = df[df['type'] == '买入']
        sell = df[df['type'] == '卖出']

        mobile_kpi_row([
            ("总交易数", str(len(df)), None, "normal", "📊"),
            ("买入笔数", str(len(buy)), None, "normal", "📥"),
            ("卖出笔数", str(len(sell)), None, "normal", "📤"),
            ("总利润", f"¥{sell['profit'].sum():,.0f}", None, "normal", "💎"),
        ], cols_per_row=2)

        st.dataframe(
            df[['date', 'type', 'metal', 'quantity_kg', 'price_per_kg',
                'total', 'profit', 'counterparty']],
            width='stretch', hide_index=True,
        )
    else:
        empty_state("暂无交易记录", "📝")


# ═══════════════════════════════════════════════════════════
#  👥 客户供应商
# ═══════════════════════════════════════════════════════════
elif page == "👥 客户供应商":
    st.title("👥 客户与供应商")

    from database import Supplier, Customer
    from config import METAL_TYPES
    metals = list(METAL_TYPES.keys())

    tab1, tab2 = st.tabs(["🏭 供应商", "🏪 客户"])

    with tab1:
        with st.expander("➕ 添加供应商"):
            c1, c2 = st.columns(2)
            sn = c1.text_input("公司名称", key="sn")
            sc_contact = c1.text_input("联系人", key="sc")
            sp = c2.text_input("电话", key="sp")
            sa = c2.text_input("地址", key="sa")
            sm = st.multiselect("供应金属品类", metals, key="sm")
            sr = st.slider("信誉评级", 1, 5, 3, key="sr")
            sno = st.text_area("备注", key="sno", placeholder="供应商备注...")
            if st.button("✅ 添加供应商", width='stretch'):
                session = services["session"]()
                try:
                    session.add(Supplier(
                        name=sn, contact=sc_contact, phone=sp, address=sa,
                        metal_types=",".join(sm), reliability=sr, notes=sno,
                    ))
                    session.commit()
                    st.success(f"已添加供应商: {sn}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
                finally:
                    session.close()

        session = services["session"]()
        try:
            sups = session.query(Supplier).all()
            if sups:
                st.dataframe(pd.DataFrame([{
                    "ID": s.id, "名称": s.name, "联系人": s.contact,
                    "电话": s.phone, "主营金属": s.metal_types,
                    "信誉": "⭐" * s.reliability,
                } for s in sups]), width='stretch', hide_index=True)
            else:
                empty_state("暂无供应商数据", "🏭")
        finally:
            session.close()

    with tab2:
        with st.expander("➕ 添加客户"):
            c1, c2 = st.columns(2)
            cn = c1.text_input("公司名称", key="cn")
            cc = c1.text_input("联系人", key="cc")
            cp = c2.text_input("电话", key="cp")
            ca = c2.text_input("地址", key="ca")
            cm = st.multiselect("需求金属品类", metals, key="cm")
            cr = st.slider("信用评级", 1, 5, 3, key="cr")
            cno = st.text_area("备注", key="cno", placeholder="客户备注...")
            if st.button("✅ 添加客户", width='stretch'):
                session = services["session"]()
                try:
                    session.add(Customer(
                        name=cn, contact=cc, phone=cp, address=ca,
                        metal_types=",".join(cm), credit_rating=cr, notes=cno,
                    ))
                    session.commit()
                    st.success(f"已添加客户: {cn}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
                finally:
                    session.close()

        session = services["session"]()
        try:
            custs = session.query(Customer).all()
            if custs:
                st.dataframe(pd.DataFrame([{
                    "ID": c.id, "名称": c.name, "联系人": c.contact,
                    "电话": c.phone, "需求金属": c.metal_types,
                    "信用": "⭐" * c.credit_rating,
                } for c in custs]), width='stretch', hide_index=True)
            else:
                empty_state("暂无客户数据", "🏪")
        finally:
            session.close()


# ═══════════════════════════════════════════════════════════
#  📊 利润分析
# ═══════════════════════════════════════════════════════════
elif page == "📊 利润分析":
    st.title("📊 利润分析")

    p30 = get_profit_summary(30)
    p90 = get_profit_summary(90)

    mobile_kpi_row([
        ("近30天利润", f"¥{p30['total_profit']:,.0f}", f"{p30['total_sell_transactions']}笔", "normal", "📅"),
        ("近90天利润", f"¥{p90['total_profit']:,.0f}", f"{p90['total_sell_transactions']}笔", "normal", "📆"),
        ("平均利润率", f"{p30['avg_profit_margin']:.2f}%", None, "normal", "🎯"),
    ], cols_per_row=2)

    st.markdown("---")
    section_header("📦 浮动盈亏", "各金属持仓盈亏明细")

    inv = get_all_inventory()
    if inv:
        df_inv = pd.DataFrame(inv)

        fig = px.bar(
            df_inv, x='metal_type', y='profit_loss',
            color='profit_loss',
            color_continuous_scale=[
                (0, '#EF4444'), (0.45, '#9CA3AF'), (0.5, '#6B7280'),
                (0.55, '#9CA3AF'), (1, '#10B981')
            ],
            labels={'profit_loss': '浮动盈亏(元)', 'metal_type': '金属'},
        )
        fig.update_traces(marker=dict(line=dict(width=0)))
        styled_plotly(fig)
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_FAST_CONFIG)

        st.dataframe(
            df_inv[['metal_type', 'quantity_kg', 'avg_cost_price',
                    'current_market_price', 'profit_loss', 'profit_loss_pct']],
            width='stretch', hide_index=True,
        )
    else:
        empty_state("暂无库存", "📦")

    st.markdown("---")
    section_header("📈 投资回报率 (ROI)", "")
    inv_s = get_inventory_summary()
    if inv_s['total_cost'] > 0:
        roi = inv_s['profit_pct']
        roi_color = "#10B981" if roi >= 0 else "#EF4444"
        st.markdown(
            f'<div style="text-align:center;padding:20px;">'
            f'<div style="font-size:0.85rem;color:#6B7280;margin-bottom:8px;">'
            f'总投资回报率</div>'
            f'<div style="font-size:2.2rem;font-weight:800;color:{roi_color};">'
            f'{roi:+.2f}%</div>'
            f'<div style="color:#9CA3AF;font-size:0.8rem;margin-top:4px;">'
            f'目标: 30% | 当前: {roi:.2f}%</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(min(abs(roi) / 30, 1.0))
    else:
        empty_state("暂无投资数据", "💼")

# ═══════════════════════════════════════════════════════════
#  🧪 回测
# ═══════════════════════════════════════════════════════════
elif page == "🧪 回测":
    st.title("🧪 推荐回测")

    perf = services["feedback"].get_performance()

    if perf["total"] == 0:
        st.info("📝 尚无回测数据。AI推荐每3天自动评估一次，"
                 "积累足够数据后显示准确率和自学习效果。")
    else:
        mobile_kpi_row([
            ("历史推荐", str(perf["total"]), None, "normal", "📋"),
            ("准确率", f"{perf['accuracy']}%", None,
             "normal" if perf['accuracy'] >= 50 else "inverse", "🎯"),
            ("7日均收益", f"{perf.get('avg_profit_7d', 0):+.2f}%", None, "normal", "📈"),
        ], cols_per_row=2)

        # 按金属
        st.markdown("---")
        section_header("📊 按金属统计", "")
        if perf.get("by_metal"):
            df_m = pd.DataFrame([
                {"金属": mt, "推荐数": d["total"],
                 "准确率%": d["accuracy"], "7日均收益%": d["avg_profit"]}
                for mt, d in perf["by_metal"].items()
            ])
            st.dataframe(df_m, width='stretch', hide_index=True)

        # 最近结果
        st.markdown("---")
        section_header("📋 最近推荐结果", "绿色=正确，红色=错误")
        outcomes = services["feedback"].get_recent_outcomes(20)
        if outcomes:
            for o in outcomes:
                correct = o.get("was_correct")
                if correct is True:
                    bg = "#ECFDF5"; border = "#10B981"; tag = "✅"
                elif correct is False:
                    bg = "#FEF2F2"; border = "#EF4444"; tag = "❌"
                else:
                    bg = "#F9FAFB"; border = "#D1D5DB"; tag = "⏳"
                st.markdown(
                    f'<div style="background:{bg};border-left:3px solid {border};'
                    f'padding:8px 12px;margin:4px 0;border-radius:6px;'
                    f'font-size:0.82rem;display:flex;justify-content:space-between;">'
                    f'<span>{o["date"]} <b>{o["metal_type"]}</b> '
                    f'{o["action"]}({o["confidence"]:.0%})</span>'
                    f'<span>{tag} 3d:{o.get("outcome_3d","?")}% '
                    f'7d:{o.get("outcome_7d","?")}% '
                    f'30d:{o.get("outcome_30d","?")}%</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            empty_state("暂无评估结果", "🧪")

        # 自学习状态
        st.markdown("---")
        section_header("🧠 自学习状态", "")
        if perf["accuracy"] < 45:
            st.warning(f"⚠️ 当前准确率 {perf['accuracy']}%，权重已向均匀分布微调15%")
        elif perf["accuracy"] > 65:
            st.success(f"✅ 当前准确率 {perf['accuracy']}%，权重表现良好无需调整")
        else:
            st.info(f"📊 当前准确率 {perf['accuracy']}%，继续积累数据中")

# ═══════════════════════════════════════════════════════════
#  底部
# ═══════════════════════════════════════════════════════════
st.markdown("---")
if services["price"].is_using_real_data:
    last_up = services["price"].last_update_time
    if last_up:
        real_label = f"🟢 SHFE实时 · 更新于 {last_up.strftime('%H:%M:%S')}"
    else:
        real_label = "🟢 SHFE实时行情"
else:
    real_label = "🟡 本地模拟数据"
st.markdown(
    f'<div style="text-align:center;color:#9CA3AF;font-size:0.78rem;padding:4px 0;">'
    f'🔩 Metal AI Trading System v3.4 · 14因子统计增强 · {real_label}'
    '</div>',
    unsafe_allow_html=True,
)

# 移动端底部导航提示
# (已移除)
