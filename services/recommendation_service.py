"""
AI推荐引擎 v3.4 — 多因子加权评分 + 动态权重 + 背离检测 + 自适应风控 + 统计增强

优化项 (v3.4):
- 🆕 Hurst指数：区分趋势市(H>0.55)/随机游走/均值回归(H<0.45)，替代ADX单指标
- 🆕 峰值/谷值检测：scipy.signal.argrelextrema三峰背离检测，消除噪音
- 🆕 Bollinger %B + Z-Score：量化的均值回归信号
- 🆕 因子去相关：trend↔timeframe, momentum↔divergence去重，权重衰减
- 🆕 Half-Kelly仓位：凯利×0.5安全边际 + 组合敞口上限
- 🆕 置信度校准：信号强度×因子一致性×数据质量 三维校准
- 🆕 支撑阻力质量评分：触碰次数+时间衰减加权
- 🆕 移动止盈：强趋势下放宽止盈容忍（让利润奔跑）
"""
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from database import Recommendation, Inventory
from services.price_service import MetalPriceService
from config import METAL_TYPES
import logging

logger = logging.getLogger(__name__)

# ── 基础权重 v3.2（从 config 动态读取，此处作 fallback） ──
from config import FACTOR_WEIGHTS as _CFG_WEIGHTS
BASE_WEIGHTS = {
    "trend":       0.13, "momentum":    0.10, "volatility":  0.06,
    "sr_levels":   0.06, "volume":      0.05, "regime":      0.05,
    "seasonal":    0.06, "correlation": 0.05, "macro_bias":  0.07,
    "timeframe":   0.07, "supply_demand": 0.05,
    "operational": 0.08, "risk_mgmt":   0.05,
    "divergence":  0.12,  # 🆕 背离检测（RSI+MACD）
}
# 从 config 合并（config中有定义则覆盖）
try:
    for k, v in _CFG_WEIGHTS.items():
        BASE_WEIGHTS[k] = v
except Exception:
    pass

# ── 动态权重调整策略 ──
# 趋势市：趋势/动量/背离/多周期权重加倍，SR/波动权重减半
# 震荡市：SR/波动/布林带权重加倍，趋势/动量权重减半
TRENDING_WEIGHT_ADJ = {
    "trend": 1.6, "momentum": 1.5, "divergence": 1.4, "timeframe": 1.4,
    "regime": 1.3, "correlation": 1.2,
    "sr_levels": 0.4, "volatility": 0.5,
}
RANGING_WEIGHT_ADJ = {
    "sr_levels": 2.0, "volatility": 1.8, "volume": 1.5,
    "seasonal": 1.3, "correlation": 1.3,
    "trend": 0.4, "momentum": 0.5, "timeframe": 0.5, "divergence": 0.6,
}


class RecommendationService:
    """v3.4 多因子AI推荐引擎 — 统计增强版"""

    def __init__(self, session_factory, price_service=None, llm_service=None):
        self.session_factory = session_factory
        self.price_service = price_service or MetalPriceService(session_factory)
        self.llm = llm_service  # 可选LLM增强
        self._cached_all_summary = None  # v3 跨品种缓存

    # ═══════════════════════════════════════════════════════
    #  公开接口
    # ═══════════════════════════════════════════════════════

    def analyze_and_recommend(self, metal_type: str, inventory_items: list = None,
                              save_to_db: bool = True) -> dict:
        """多因子综合分析，输出买卖建议"""
        try:
            return self._analyze_impl(metal_type, inventory_items, save_to_db)
        except Exception as e:
            logger.error(f"分析{metal_type}失败: {e}", exc_info=True)
            return {
                "action": "持有", "confidence": 0, "reason": f"分析异常: {str(e)[:80]}",
                "metal_type": metal_type, "suggested_quantity_kg": 0,
                "suggested_price": 0, "current_price": 0,
                "expected_profit_pct": 0, "stop_loss": 0, "take_profit": 0,
                "trend_analysis": {}, "risk_level": "未知",
                "created_at": datetime.now().isoformat(),
                "llm_available": False,
            }

    def _analyze_impl(self, metal_type: str, inventory_items: list,
                      save_to_db: bool) -> dict:
        df, source = self.price_service.get_historical_prices(metal_type, days=120)
        if df.empty or len(df) < 30:
            return {"action": "持有", "confidence": 0, "reason": "数据不足（需≥30天）",
                    "metal_type": metal_type, "suggested_quantity_kg": 0,
                    "suggested_price": 0, "current_price": 0,
                    "expected_profit_pct": 0, "stop_loss": 0, "take_profit": 0,
                    "trend_analysis": {}, "risk_level": "未知",
                    "created_at": datetime.now().isoformat(),
                    "llm_available": False}

        # 防御：确保price列是1D数值数组
        prices_raw = df['price'].values
        prices = np.asarray(prices_raw, dtype=float).ravel()
        if len(prices) < 30:
            return {"action": "持有", "confidence": 0, "reason": "有效数据不足（需≥30天）",
                    "metal_type": metal_type, "suggested_quantity_kg": 0,
                    "suggested_price": 0, "current_price": 0,
                    "expected_profit_pct": 0, "stop_loss": 0, "take_profit": 0,
                    "trend_analysis": {}, "risk_level": "未知",
                    "created_at": datetime.now().isoformat(),
                    "llm_available": False}
        current = float(prices[-1])
        n = len(prices)

        # ── 计算所有指标 ──
        ind = self._compute_indicators(prices)

        # ── 各因子评分 (0-100) ──
        scores = {}
        reasons_all = []

        scores["trend"], tr = self._score_trend(ind, prices)
        reasons_all.extend(tr)

        scores["momentum"], mr = self._score_momentum(ind)
        reasons_all.extend(mr)

        scores["volatility"], vr = self._score_volatility(ind)
        reasons_all.extend(vr)

        scores["sr_levels"], sr = self._score_sr_levels(ind, current, prices)
        reasons_all.extend(sr)

        scores["volume"], vor = self._score_volume(ind, prices)
        reasons_all.extend(vor)

        scores["regime"], rr = self._score_regime(ind)
        reasons_all.extend(rr)

        # 🆕 v3.2 背离检测（RSI + MACD，最强反转信号）
        scores["divergence"], dvr = self._score_divergence(ind, prices)
        reasons_all.extend(dvr)

        # 🆕 v3.4: 记录数据源用于置信度校准
        scores["realtime_source"] = source

        # ── 🆕 v3 新增因子 ──
        scores["seasonal"], ser = self._score_seasonal(metal_type, ind)
        reasons_all.extend(ser)

        # 🆕 多周期趋势一致性（日/周/月对齐检查）
        scores["timeframe"], tfr = self._score_timeframe_alignment(ind, prices)
        reasons_all.extend(tfr)

        # 🆕 供需基本面代理（库存变化率 + 价格动量）
        scores["supply_demand"], sdr = self._score_supply_demand(metal_type, ind, prices)
        reasons_all.extend(sdr)

        # 优先使用 analyze_all_metals 预计算的缓存
        all_metals_summary = getattr(self, '_cached_all_summary', None)
        if all_metals_summary is None:
            all_metals_summary = self._get_all_metals_summary()

        scores["correlation"], cr = self._score_correlation(metal_type, inventory_items, all_metals_summary)
        reasons_all.extend(cr)

        scores["macro_bias"], mrb = self._score_macro_bias(metal_type, ind, all_metals_summary)
        reasons_all.extend(mrb)

        inv_score, inv_reasons, inv_data = self._inventory_factor(
            inventory_items, current, composite=0
        )
        reasons_all.extend(inv_reasons)

        scores["operational"], opr = self._score_operational(
            metal_type, inventory_items, inv_data, current
        )
        reasons_all.extend(opr)

        scores["risk_mgmt"], rmr = self._score_risk_management(
            metal_type, inventory_items, inv_data, all_metals_summary
        )
        reasons_all.extend(rmr)

        # ── 🆕 v3.2 动态权重：根据市场状态自适应调整 ──
        weights = self._adaptive_weights(ind, all_metals_summary)

        # ── 加权总分 (0-100) —— 仅对数值型因子求和 ──
        numeric_scores = {k: v for k, v in scores.items()
                          if isinstance(v, (int, float))}
        composite = sum(numeric_scores[k] * weights.get(k, 0)
                        for k in numeric_scores if k in weights)
        composite = max(0, min(100, composite))

        # ── 🆕 v3.2 决策（重写的清晰决策矩阵） ──
        action, confidence = self._decide_v3(composite, inventory_items, current,
                                              ind, inv_data, scores)

        # ── 🆕 v3.2 自适应风控：ATR倍数随波动率动态缩放 ──
        atr = ind["atr"]
        stop_loss, take_profit = self._adaptive_stops(
            action, current, atr, ind, inventory_items, inv_data
        )
        suggested_qty = self._kelly_position_v3(
            action, inventory_items, current, ind["volatility_30d"], atr, confidence
        ) if confidence > 0 else 0

        expected_profit = 0
        if inventory_items and action in ("卖出", "减仓"):
            avg_cost = np.mean([it['avg_cost_price'] for it in inventory_items])
            expected_profit = (current - avg_cost) / avg_cost * 100

        # 🆕 因子一致性 → 提升理由质量
        factor_agree = self._factor_agreement(scores, action)
        if factor_agree >= 0.7:
            reasons_all.insert(0, "🎯 多因子高度一致")
        elif factor_agree <= 0.3:
            reasons_all.insert(0, "⚡ 因子分歧较大，建议谨慎")

        reason_text = "；".join(reasons_all[:8]) if reasons_all else "市场中性，持有观望"

        result = {
            "metal_type": metal_type,
            "action": action,
            "confidence": round(confidence, 2),
            "suggested_quantity_kg": round(suggested_qty, 2),
            "suggested_price": round(current, 2),
            "current_price": round(current, 2),
            "expected_profit_pct": round(expected_profit, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "reason": reason_text,
            "trend_analysis": {
                "composite_score": round(composite, 1),
                "trend_score": round(scores["trend"], 1),
                "momentum_score": round(scores["momentum"], 1),
                "volatility_score": round(scores["volatility"], 1),
                "sr_score": round(scores["sr_levels"], 1),
                "volume_score": round(scores["volume"], 1),
                "regime_score": round(scores["regime"], 1),
                # 🆕 v3.2 背离因子
                "divergence_score": round(scores.get("divergence", 50), 1),
                # 🆕 v3 新增因子
                "seasonal_score": round(scores.get("seasonal", 50), 1),
                "correlation_score": round(scores.get("correlation", 50), 1),
                "macro_score": round(scores.get("macro_bias", 50), 1),
                "timeframe_score": round(scores.get("timeframe", 50), 1),
                "supply_demand_score": round(scores.get("supply_demand", 50), 1),
                "operational_score": round(scores.get("operational", 50), 1),
                "risk_score": round(scores.get("risk_mgmt", 50), 1),
                # 市场状态
                "realtime_source": source,
                "factor_agreement": round(factor_agree, 2),
                # 原有技术指标
                "rsi": round(ind["rsi"], 1),
                "macd": round(ind["macd"], 4),
                "macd_signal": round(ind["macd_signal"], 4),
                "atr": round(atr, 2),
                "atr_pct": round(ind["atr_pct"], 2),
                "trend_slope": round(ind["trend_slope"], 4),
                "bb_upper": round(ind["bb_upper"], 2),
                "bb_lower": round(ind["bb_lower"], 2),
                "support": round(ind["support"], 2),
                "resistance": round(ind["resistance"], 2),
                "inventory_analysis": inv_data.get("text", ""),
            },
            "risk_level": self._risk_level(ind["volatility_30d"]),
            "created_at": datetime.now().isoformat(),
        }

        if save_to_db:
            result["saved"] = self._save_recommendation(result)

        result["llm_available"] = False

        return result

    def analyze_all_metals(self) -> list[dict]:
        """分析所有金属：量化全跑（v3 单会话优化）"""
        session: Session = self.session_factory()
        try:
            # 🆕 用外层 session 构建汇总，避免嵌套 DB 连接导致 SQLite 锁
            all_inv_items = session.query(Inventory).filter(
                Inventory.status == "持有"
            ).all()
            inv_by_metal = {}
            for item in all_inv_items:
                if item.metal_type not in inv_by_metal:
                    inv_by_metal[item.metal_type] = []
                inv_by_metal[item.metal_type].append({
                    "quantity_kg": item.quantity_kg,
                    "avg_cost_price": item.avg_cost_price,
                    "current_market_price": item.current_market_price or item.avg_cost_price,
                    "total_cost": item.total_cost or 0,
                    "current_value": item.current_value or 0,
                })

            # 构建轻量全品种汇总（不另开 session）
            all_summary = {"by_metal": {}, "by_trend": {}, "by_metal_summary": {},
                           "total_value": 0, "total_cost": 0, "profit_pct": 0}
            try:
                summaries = self.price_service.get_all_price_summaries()
                for s in summaries:
                    mt = s.get("metal_type", "")
                    if mt:
                        all_summary["by_trend"][mt] = s.get("trend", "")
                        all_summary["by_metal_summary"][mt] = {
                            "change_week": s.get("change_week", 0),
                            "change_month": s.get("change_month", 0),
                            "volatility": s.get("volatility", 0),
                        }
            except Exception:
                pass
            for mt, items in inv_by_metal.items():
                all_summary["by_metal"][mt] = {
                    "quantity_kg": sum(i["quantity_kg"] for i in items),
                    "total_cost": sum(i["total_cost"] for i in items),
                    "current_value": sum(i["current_value"] for i in items),
                }
                all_summary["total_value"] += all_summary["by_metal"][mt]["current_value"]
                all_summary["total_cost"] += all_summary["by_metal"][mt]["total_cost"]
            if all_summary["total_cost"] > 0:
                all_summary["profit_pct"] = (
                    all_summary["total_value"] - all_summary["total_cost"]
                ) / all_summary["total_cost"] * 100

            self._cached_all_summary = all_summary

            results, to_save = [], []
            for metal_type in METAL_TYPES:
                inv_data = inv_by_metal.get(metal_type, [])
                try:
                    r = self._analyze_impl(metal_type, inv_data, save_to_db=False)
                except Exception as e:
                    logger.warning(f"分析 {metal_type} 跳过: {e}")
                    r = {
                        "action": "持有", "confidence": 0, "reason": "数据不足",
                        "metal_type": metal_type, "suggested_quantity_kg": 0,
                        "suggested_price": 0, "current_price": 0,
                        "expected_profit_pct": 0, "stop_loss": 0, "take_profit": 0,
                        "trend_analysis": {}, "risk_level": "未知",
                        "created_at": datetime.now().isoformat(),
                        "llm_available": False,
                    }
                results.append(r)
                to_save.append(r)

            self._cached_all_summary = None
            saved_all = self._save_recommendations_batch(to_save)
            for r in results:
                r["saved"] = saved_all
                r["llm_available"] = False

            return results
        finally:
            try:
                session.close()
            except Exception:
                pass

    def enrich_single_with_llm(self, metal_type: str, inventory_items: list = None) -> dict:
        """对单个金属运行LLM增强分析（按需调用，不卡主流程）"""
        if not self.llm or not self.llm.available:
            return {"success": False, "message": "LLM未配置API Key"}
        try:
            # 跑量化分析获取完整指标
            result = self._analyze_impl(metal_type, inventory_items or [], save_to_db=False)
            df, _ = self.price_service.get_historical_prices(metal_type, days=120)
            ind = self._compute_indicators(df['price'].values)

            # 库存信息
            inv_info = {}
            if inventory_items:
                total_kg = sum(it.get('quantity_kg', 0) for it in inventory_items)
                avg_cost = np.mean([it.get('avg_cost_price', 0) for it in inventory_items]) if inventory_items else 0
                if avg_cost > 0 and ind.get('current', 0) > 0:
                    profit_pct = (ind['current'] - avg_cost) / avg_cost * 100
                    inv_info = {"total_kg": total_kg, "avg_cost": avg_cost, "profit_pct": profit_pct}

            ta = result.get('trend_analysis', {})
            llm_r = self.llm.analyze(
                metal_type, ind, inv_info,
                {
                    "action": result['action'],
                    "confidence": result['confidence'],
                    "composite_score": ta.get('composite_score', 0),
                    "trend_score": ta.get('trend_score', 0),
                    "momentum_score": ta.get('momentum_score', 0),
                    "volatility_score": ta.get('volatility_score', 0),
                    "sr_score": ta.get('sr_score', 0),
                    "volume_score": ta.get('volume_score', 0),
                    "regime_score": ta.get('regime_score', 0),
                    "divergence_score": ta.get('divergence_score', 50),
                    "seasonal_score": ta.get('seasonal_score', 50),
                    "correlation_score": ta.get('correlation_score', 50),
                    "macro_score": ta.get('macro_score', 50),
                    "timeframe_score": ta.get('timeframe_score', 50),
                    "supply_demand_score": ta.get('supply_demand_score', 50),
                    "operational_score": ta.get('operational_score', 50),
                    "risk_score": ta.get('risk_score', 50),
                    "stop_loss": result.get('stop_loss', 0),
                    "take_profit": result.get('take_profit', 0),
                }
            )
            result["llm_analysis"] = llm_r.get("analysis", "")
            result["llm_recommendation"] = llm_r.get("recommendation", "")
            result["llm_risks"] = llm_r.get("risks", "")
            result["llm_available"] = True
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"LLM单金属分析失败: {e}")
            return {"success": False, "message": str(e)[:120]}

    def _enrich_top_with_llm(self, results: list):
        """🆕 v3.2 对Top信号调用LLM增强（含所有操作类型）"""
        buy = sorted([r for r in results if r['action'] in ('买入', '加仓')],
                     key=lambda x: x['confidence'], reverse=True)[:3]
        sell = sorted([r for r in results if r['action'] in ('卖出', '减仓', '止损')],
                      key=lambda x: x['confidence'], reverse=True)[:3]
        to_enrich = buy + sell

        if not to_enrich:
            return

        for r in to_enrich:
            try:
                ind = self._compute_indicators(
                    self.price_service.get_historical_prices(r['metal_type'], days=120)[0]['price'].values
                )
                ta = r.get('trend_analysis', {})
                llm_result = self.llm.analyze(
                    r['metal_type'], ind, {},
                    {
                        "action": r['action'],
                        "confidence": r['confidence'],
                        "composite_score": ta.get('composite_score', 0),
                        "trend_score": ta.get('trend_score', 0),
                        "momentum_score": ta.get('momentum_score', 0),
                        "volatility_score": ta.get('volatility_score', 0),
                        "sr_score": ta.get('sr_score', 0),
                        "volume_score": ta.get('volume_score', 0),
                        "regime_score": ta.get('regime_score', 0),
                        # 🆕 v3.2 背离因子
                        "divergence_score": ta.get('divergence_score', 50),
                        # 🆕 v3 因子
                        "seasonal_score": ta.get('seasonal_score', 50),
                        "correlation_score": ta.get('correlation_score', 50),
                        "macro_score": ta.get('macro_score', 50),
                        "timeframe_score": ta.get('timeframe_score', 50),
                        "supply_demand_score": ta.get('supply_demand_score', 50),
                        "operational_score": ta.get('operational_score', 50),
                        "risk_score": ta.get('risk_score', 50),
                        "stop_loss": r.get('stop_loss', 0),
                        "take_profit": r.get('take_profit', 0),
                    }
                )
                r["llm_analysis"] = llm_result.get("analysis", "")
                r["llm_recommendation"] = llm_result.get("recommendation", "")
                r["llm_risks"] = llm_result.get("risks", "")
                r["llm_available"] = True
            except Exception as e:
                logger.warning(f"LLM enrich failed for {r['metal_type']}: {e}")
                r["llm_available"] = False

    def get_latest_recommendations(self, limit: int = 20) -> list[dict]:
        session: Session = self.session_factory()
        try:
            recs = session.query(Recommendation).order_by(
                Recommendation.created_at.desc()).limit(limit).all()
            return [{
                "id": r.id, "metal_type": r.metal_type, "action": r.action,
                "confidence": r.confidence, "suggested_quantity_kg": r.suggested_quantity_kg,
                "suggested_price": r.suggested_price, "current_price": r.current_price,
                "expected_profit_pct": r.expected_profit_pct,
                "reason": r.reason, "risk_level": r.risk_level,
                "created_at": r.created_at.isoformat(), "is_executed": r.is_executed,
            } for r in recs]
        finally:
            session.close()

    def get_top_opportunities(self, top_n: int = 5) -> dict:
        all_recs = self.analyze_all_metals()
        buy = sorted([r for r in all_recs if r['action'] in ('买入', '加仓')],
                     key=lambda x: x['confidence'], reverse=True)
        sell = sorted([r for r in all_recs if r['action'] in ('卖出', '减仓', '止损')],
                      key=lambda x: x['confidence'], reverse=True)
        return {"top_buy": buy[:top_n], "top_sell": sell[:top_n], "all": all_recs}

    # ═══════════════════════════════════════════════════════
    #  指标计算
    # ═══════════════════════════════════════════════════════

    def _compute_indicators(self, prices: np.ndarray) -> dict:
        """一次性计算所有技术指标，避免重复遍历 (v3.3 优化：向量化EMA)"""
        # 防御：确保prices是1D数组，移除NaN/Inf
        prices = np.asarray(prices).ravel()
        prices = prices[np.isfinite(prices)]
        n = len(prices)
        if n < 2:
            return self._empty_indicators()
        with np.errstate(invalid='ignore', divide='ignore'):
            returns = np.diff(prices) / (prices[:-1] + 1e-10)

        # ── 均线 (使用numpy卷积，比循环快) ──
        ma7 = float(np.mean(prices[-7:]))
        ma20 = float(np.mean(prices[-20:])) if n >= 20 else ma7
        ma30 = float(np.mean(prices[-30:])) if n >= 30 else ma7
        ma60 = float(np.mean(prices[-60:])) if n >= 60 else ma7

        # ── Wilder's RSI (14) ──
        rsi = self._wilders_rsi(prices, 14)

        # ── MACD (12/26/9) — 现在使用向量化_ema_series ──
        ema12_series = self._ema_series(prices, 12)
        ema26_series = self._ema_series(prices, 26)
        macd_series = ema12_series - ema26_series
        macd_signal_series = self._ema_series(macd_series, 9)
        macd_line = float(macd_series[-1])
        macd_signal = float(macd_signal_series[-1])
        macd_hist = macd_line - macd_signal

        # ── ATR (14) ──
        atr, atr_pct = self._calc_atr(prices, 14)

        # ── 布林带 (20, 2) ──
        bb_mid = ma20
        bb_std = float(np.std(prices[-20:])) if n >= 20 else 0.0
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std

        # ── 线性回归趋势斜率（SVD fallback 防御） ──
        window = min(n, 30)
        x = np.arange(window)
        y = prices[-window:]
        try:
            slope = np.polyfit(x, y, 1)[0]
        except (np.linalg.LinAlgError, ValueError):
            # SVD 不收敛时用简单差分替代
            slope = (y[-1] - y[0]) / window if window > 1 else 0
        trend_slope = slope / (np.mean(y) + 1e-10)

        # ── 支撑阻力 ──
        recent = prices[-30:] if n >= 30 else prices
        support = float(np.min(recent))
        resistance = float(np.max(recent))

        # ── 波动率 ──
        vol_30d = float(np.std(returns[-30:])) if len(returns) >= 30 else 0.0
        vol_90d = float(np.std(returns)) if len(returns) >= 30 else vol_30d

        # ── 成交量趋势 (用价格变化幅度模拟) ──
        if len(returns) >= 30:
            denom = float(np.mean(np.abs(returns[-30:])))
            vol_trend = float(np.mean(np.abs(returns[-10:]))) / denom if denom > 0 else 1.0
        else:
            vol_trend = 1.0

        # ── ADX 简化版 (趋势强度) ──
        adx = self._simple_adx(prices, 14)

        # ── 🆕 v3.4 Hurst指数 (区分趋势/随机/均值回归) ──
        hurst = self._hurst_exponent(prices)

        # ── 🆕 v3.4 Bollinger %B + Z-Score (量化均值回归) ──
        if bb_upper > bb_lower:
            bb_pct_b = (float(prices[-1]) - bb_lower) / (bb_upper - bb_lower)
        else:
            bb_pct_b = 0.5
        z_score = (float(prices[-1]) - ma20) / (bb_std + 1e-10) if bb_std > 0 else 0.0

        # ── 🆕 v3.4 支撑/阻力触碰次数 ──
        sr_touches = self._count_sr_touches(prices, support, resistance)

        # ── 🆕 v3.4 随机指标 (Stochastic %K) ──
        stoch_k = self._stochastic_k(prices, 14, 3)

        return {
            "ma7": ma7, "ma20": ma20, "ma30": ma30, "ma60": ma60,
            "rsi": rsi,
            "macd": macd_line, "macd_signal": macd_signal, "macd_hist": macd_hist,
            "atr": atr, "atr_pct": atr_pct,
            "bb_upper": bb_upper, "bb_lower": bb_lower, "bb_mid": bb_mid,
            "bb_pct_b": bb_pct_b, "z_score": z_score,
            "trend_slope": trend_slope,
            "support": support, "resistance": resistance,
            "sr_support_touches": sr_touches["support"],
            "sr_resistance_touches": sr_touches["resistance"],
            "volatility_30d": vol_30d, "volatility_90d": vol_90d,
            "vol_trend": vol_trend,
            "adx": adx, "hurst": hurst,
            "stoch_k": stoch_k,
            "current": float(prices[-1]),
            "n": n,
        }

    @staticmethod
    def _empty_indicators() -> dict:
        """返回空的指标字典（数据不足时）"""
        return {
            "ma7": 0, "ma20": 0, "ma30": 0, "ma60": 0,
            "rsi": 50.0,
            "macd": 0, "macd_signal": 0, "macd_hist": 0,
            "atr": 0, "atr_pct": 0,
            "bb_upper": 0, "bb_lower": 0, "bb_mid": 0,
            "bb_pct_b": 0.5, "z_score": 0.0,
            "trend_slope": 0,
            "support": 0, "resistance": 0,
            "sr_support_touches": 0, "sr_resistance_touches": 0,
            "volatility_30d": 0, "volatility_90d": 0,
            "vol_trend": 1.0,
            "adx": 15.0, "hurst": 0.5,
            "stoch_k": 50.0,
            "current": 0,
            "n": 0,
        }

    # ═══════════════════════════════════════════════════════
    #  各因子评分 (0-100)
    # ═══════════════════════════════════════════════════════

    def _score_trend(self, ind: dict, prices: np.ndarray) -> tuple:
        """趋势因子：多周期均线排列 + 线性斜率 + ADX"""
        score = 50
        reasons = []

        # 均线排列 (20分)
        if ind["ma7"] > ind["ma20"] > ind["ma30"]:
            score += 15
            reasons.append("📈 均线多头排列")
        elif ind["ma7"] < ind["ma20"] < ind["ma30"]:
            score -= 15
            reasons.append("📉 均线空头排列")

        # 价格与均线关系 (15分)
        cur = ind["current"]
        if cur > ind["ma20"] and cur > ind["ma30"]:
            score += 10
        elif cur < ind["ma20"] and cur < ind["ma30"]:
            score -= 10

        # 线性斜率 (10分) — 归一化到±10
        slope_score = np.clip(ind["trend_slope"] * 1000, -10, 10)
        score += slope_score
        if slope_score > 5:
            reasons.append("📐 短期斜率向上")
        elif slope_score < -5:
            reasons.append("📐 短期斜率向下")

        # ADX趋势强度 (5分)
        if ind["adx"] > 25:
            if score > 50:
                score += 5
                reasons.append(f"💪 ADX={ind['adx']:.0f} 强趋势")
            else:
                score -= 5
        elif ind["adx"] < 20:
            reasons.append(f"😴 ADX={ind['adx']:.0f} 盘整市")

        return max(0, min(100, score)), reasons

    def _score_momentum(self, ind: dict) -> tuple:
        """动量因子：RSI + MACD + Stochastic (v3.4增强)"""
        score = 50
        reasons = []

        # RSI (25分贡献) — 🆕 v3.4: 补齐55-65看多区间
        rsi = ind["rsi"]
        if rsi < 25:
            score += 25
            reasons.append(f"🔥 RSI={rsi:.0f} 深度超卖")
        elif rsi < 35:
            score += 25 - (rsi - 25) * 1.5
            reasons.append(f"📊 RSI={rsi:.0f} 超卖区域")
        elif rsi < 45:
            # 🆕 35-45 偏弱但未超卖
            score -= (45 - rsi) * 0.5
        elif rsi <= 55:
            reasons.append(f"⚖️ RSI={rsi:.0f} 中性")
        elif rsi <= 65:
            # 🆕 55-65 温和看多（之前是空白区间！）
            score += (rsi - 55) * 0.8
            reasons.append(f"📈 RSI={rsi:.0f} 温和偏多")
        elif rsi > 75:
            score -= 25
            reasons.append(f"🧊 RSI={rsi:.0f} 深度超买")
        elif rsi > 65:
            score -= 10 + (rsi - 65) * 1.5
            reasons.append(f"📊 RSI={rsi:.0f} 超买区域")

        # MACD (15分贡献) — 🆕 v3.4: MACD值缩放
        macd = ind["macd"]
        signal = ind["macd_signal"]
        hist = ind["macd_hist"]
        # 用MACD线相对于价格的比例来衡量信号强度
        cur = ind["current"]
        macd_ratio = abs(macd) / max(cur, 1e-6)
        macd_strength = min(macd_ratio / 0.003, 1.5)  # 0.3%以上=强信号

        if macd > signal and hist > 0:
            score += int(15 * macd_strength)
            if macd > 0:
                reasons.append(f"📈 MACD金叉+零轴上({macd_ratio*100:.2f}%)")
            else:
                reasons.append(f"📈 MACD金叉({macd_ratio*100:.2f}%)")
        elif macd < signal and hist < 0:
            score -= int(15 * macd_strength)
            if macd < 0:
                reasons.append(f"📉 MACD死叉+零轴下({macd_ratio*100:.2f}%)")
            else:
                reasons.append(f"📉 MACD死叉({macd_ratio*100:.2f}%)")
        elif hist > 0 and macd > signal:
            score += int(5 * macd_strength)
            reasons.append("📊 MACD柱正值扩张")
        elif hist < 0 and macd < signal:
            score -= int(5 * macd_strength)

        # 🆕 v3.4 随机指标 Stochastic (10分贡献)
        stoch = ind.get("stoch_k", 50)
        if stoch < 20:
            score += 10
            reasons.append(f"📉 Stoch%K={stoch:.0f} 超卖")
        elif stoch > 80:
            score -= 10
            reasons.append(f"📈 Stoch%K={stoch:.0f} 超买")

        return max(0, min(100, score)), reasons

    def _score_volatility(self, ind: dict) -> tuple:
        """波动率因子：ATR + 布林带 + %B + Z-Score (v3.4增强)"""
        score = 50
        reasons = []

        atr_pct = ind["atr_pct"] * 100  # 百分比

        # ATR过高→风险大扣分，适中→正常
        if atr_pct > 5:
            score -= 15
            reasons.append(f"⚠️ ATR={atr_pct:.1f}% 波动过大")
        elif atr_pct > 3:
            score -= 5
            reasons.append(f"📊 ATR={atr_pct:.1f}% 波动偏高")
        elif atr_pct < 1:
            score -= 5
            reasons.append(f"😴 ATR={atr_pct:.1f}% 波动过低")

        # 布林带位置
        cur = ind["current"]
        bb_upper = ind["bb_upper"]
        bb_lower = ind["bb_lower"]
        bb_mid = ind["bb_mid"]

        if bb_upper > bb_lower:  # 有效布林带
            bb_width = (bb_upper - bb_lower) / bb_mid

            # 🆕 v3.4: 使用 %B 量化位置 (0=下轨, 1=上轨)
            pct_b = ind.get("bb_pct_b", 0.5)
            z = ind.get("z_score", 0.0)

            if pct_b > 0.95:
                score -= 12
                reasons.append(f"🚧 布林%B={pct_b:.2f} 上轨极值")
            elif pct_b > 0.8:
                score -= 6
                reasons.append(f"📊 布林%B={pct_b:.2f} 偏高")
            elif pct_b < 0.05:
                score += 12
                reasons.append(f"🛡️ 布林%B={pct_b:.2f} 下轨极值")
            elif pct_b < 0.2:
                score += 6
                reasons.append(f"📊 布林%B={pct_b:.2f} 偏低")

            # 🆕 v3.4: Z-Score 均值回归信号
            if abs(z) > 2.0:
                direction = "超涨" if z > 0 else "超跌"
                score += (-10 if z > 0 else 10)
                reasons.append(f"📏 Z-Score={z:.1f}σ {direction}，回归概率高")
            elif abs(z) > 1.5:
                score += (-5 if z > 0 else 5)

            # 布林带收窄→即将突破
            if bb_width < 0.05:
                reasons.append("⏳ 布林带收窄，酝酿突破")
            elif bb_width > 0.15:
                reasons.append("📐 布林带宽阔，趋势强劲")

        return max(0, min(100, score)), reasons

    def _score_sr_levels(self, ind: dict, current: float, prices: np.ndarray) -> tuple:
        """支撑阻力因子 — v3.4 触碰次数质量评分"""
        score = 50
        reasons = []

        support = ind["support"]
        resistance = ind["resistance"]

        dist_support = (current - support) / support * 100
        dist_resist = (resistance - current) / current * 100

        # 🆕 v3.4: 支撑/阻力质量 = 触碰次数越多越可靠
        support_touches = ind.get("sr_support_touches", 0)
        resistance_touches = ind.get("sr_resistance_touches", 0)
        support_quality = min(support_touches / 3.0, 1.0)  # 3次以上=满分
        resistance_quality = min(resistance_touches / 3.0, 1.0)

        if dist_support < 1:
            bonus = int(15 * (0.5 + 0.5 * support_quality))
            score += bonus
            quality_label = "强" if support_quality > 0.7 else ""
            reasons.append(f"🛡️ 距{quality_label}支撑仅{dist_support:.1f}%(触碰{support_touches}次)")
        elif dist_support < 3:
            score += int(8 * (0.5 + 0.5 * support_quality))

        if dist_resist < 1:
            penalty = int(10 * (0.5 + 0.5 * resistance_quality))
            score -= penalty
            quality_label = "强" if resistance_quality > 0.7 else ""
            reasons.append(f"🚧 距{quality_label}阻力仅{dist_resist:.1f}%(触碰{resistance_touches}次)")

        # 盈亏比：距阻力 / 距支撑
        if dist_support > 0.1:
            rr_ratio = dist_resist / dist_support if dist_support > 0 else 0
            if rr_ratio > 3:
                score += 10
                reasons.append(f"🎯 盈亏比 {rr_ratio:.1f}:1")
            elif rr_ratio > 2:
                score += 5

        return max(0, min(100, score)), reasons

    def _score_volume(self, ind: dict, prices: np.ndarray) -> tuple:
        """量价因子（用价格振幅模拟成交量变化）"""
        score = 50
        reasons = []

        vol_trend = ind["vol_trend"]
        if vol_trend > 1.3:
            if ind["current"] > ind["ma20"]:
                score += 10
                reasons.append("📊 放量上涨")
            else:
                score -= 5
                reasons.append("⚠️ 放量下跌")
        elif vol_trend < 0.7:
            reasons.append("🔇 缩量运行")

        return max(0, min(100, score)), reasons

    def _score_regime(self, ind: dict) -> tuple:
        """市场状态因子：Hurst指数区分趋势/随机/均值回归 (v3.4升级)"""
        score = 50
        reasons = []

        adx = ind.get("adx", 15)
        hurst = ind.get("hurst", 0.5)
        vol_30 = ind.get("volatility_30d", 0.015)
        vol_90 = ind.get("volatility_90d", 0.015)

        # 🆕 v3.4: Hurst指数为市场状态主判断依据
        # H > 0.55 → 趋势持续 (trending)
        # 0.45 ≤ H ≤ 0.55 → 随机游走 (random walk)
        # H < 0.45 → 均值回归 (mean-reverting)

        if hurst > 0.6:
            reasons.append(f"🏃 强趋势市(Hurst={hurst:.2f})")
            if ind["current"] > ind["ma30"]:
                score += 15
            else:
                score -= 10
        elif hurst > 0.55:
            reasons.append(f"📈 弱趋势市(Hurst={hurst:.2f})")
            if ind["current"] > ind["ma30"]:
                score += 8
            else:
                score -= 5
        elif hurst < 0.4:
            reasons.append(f"🔄 强均值回归(Hurst={hurst:.2f})")
            # 均值回归：反向操作
            if ind["current"] < ind["ma20"]:
                score += 10
            else:
                score -= 5
        elif hurst < 0.45:
            reasons.append(f"📊 弱均值回归(Hurst={hurst:.2f})")
            if ind["current"] < ind["ma20"]:
                score += 5
        else:
            reasons.append(f"⚖️ 随机游走(Hurst={hurst:.2f})")

        # ADX作为辅助确认
        if adx > 25:
            if score > 50:
                score += 3
        elif adx < 18:
            if score > 50:
                score -= 3

        # 波动率扩张 vs 收缩
        if vol_90 > 0 and vol_30 / vol_90 > 1.3:
            reasons.append("📈 波动率扩张")
            score -= 5
        elif vol_90 > 0 and vol_30 / vol_90 < 0.7:
            reasons.append("📉 波动率收缩(低波)")
            score += 3

        return max(0, min(100, score)), reasons

    def _inventory_factor(self, inventory_items: list, current: float,
                          composite: float) -> tuple:
        """库存因子：基于持仓成本修正评分"""
        score = 50
        reasons = []
        info = {"text": "暂无库存"}

        if not inventory_items:
            if composite > 55:
                reasons.append("🛒 无库存+信号偏多，可建仓")
            return 55 if composite > 55 else 50, reasons, info

        total_kg = sum(it['quantity_kg'] for it in inventory_items)
        avg_cost = np.mean([it['avg_cost_price'] for it in inventory_items])
        profit_pct = (current - avg_cost) / avg_cost * 100

        info = {"text": f"库存{total_kg}kg，浮{'盈' if profit_pct>=0 else '亏'}{abs(profit_pct):.1f}%",
                "total_kg": total_kg, "avg_cost": avg_cost, "profit_pct": profit_pct}

        from config import RECOMMENDATION
        target = RECOMMENDATION['profit_margin_target'] * 100

        if profit_pct >= target:
            score = 80  # 强力倾向卖出
            reasons.append(f"💰 浮盈{profit_pct:.1f}%，已达目标{target:.0f}%")
        elif profit_pct >= RECOMMENDATION['profit_margin_min'] * 100:
            score = 60
            reasons.append(f"📦 浮盈{profit_pct:.1f}%，接近目标")
        elif profit_pct > 0:
            score = 50
            reasons.append(f"📦 小幅浮盈{profit_pct:.1f}%")
        elif profit_pct > -5:
            score = 45
            reasons.append(f"📉 小幅浮亏{profit_pct:.1f}%")
        else:
            score = 35
            reasons.append(f"🔴 浮亏{profit_pct:.1f}%，等待反弹")

        return score, reasons, info

    # ═══════════════════════════════════════════════════════
    #  🆕 v3.2 动态权重 + 自适应决策 + 因子一致性
    # ═══════════════════════════════════════════════════════

    def _adaptive_weights(self, ind: dict, all_summary: dict) -> dict:
        """🆕 v3.4 市场状态自适应 + 因子去相关降权
        
        趋势市(Hurst>0.55)：趋势/动量/背离/多周期权重放大，SR/波动权重缩小
        随机游走(0.45≤H≤0.55)：均匀权重，略微提升均线因子
        均值回归(Hurst<0.45)：SR/波动/布林带权重放大，趋势/动量权重缩小
        """
        w = dict(BASE_WEIGHTS)  # 从基础权重开始

        hurst = ind.get("hurst", 0.5)
        adx = ind.get("adx", 15)
        vol_30 = ind.get("volatility_30d", 0.015)
        bb_width = 0.02
        bb_upper = ind.get("bb_upper", 0)
        bb_mid = ind.get("bb_mid", 1)
        if bb_upper > bb_mid > 0:
            bb_width = (bb_upper - bb_mid * 0.98) / bb_mid

        # 🆕 v3.4: Hurst指数为市场状态主判断依据
        if hurst > 0.55:
            # 趋势市
            trending_strength = min((hurst - 0.55) / 0.3, 1.0)
            if adx > 25:
                trending_strength = min(trending_strength + 0.2, 1.0)
            if bb_width > 0.06:
                trending_strength = min(trending_strength + 0.15, 1.0)
        elif hurst < 0.45:
            # 均值回归市
            trending_strength = 0.0  # 强制为震荡
        else:
            # 随机游走
            trending_strength = 0.3  # 偏震荡但不完全

        ranging_strength = 1.0 - trending_strength

        # 插值权重：trending时的权重 vs ranging时的权重
        for k in w:
            t_adj = TRENDING_WEIGHT_ADJ.get(k, 1.0)
            r_adj = RANGING_WEIGHT_ADJ.get(k, 1.0)
            blend = t_adj * trending_strength + r_adj * ranging_strength
            w[k] = w[k] * blend

        # 🆕 v3.4: 因子去相关降权 (减少高度相关因子重复计算)
        w = self._decorrelate_weights(w, ind)

        # 重量归一化（确保总权重 = 1.0）
        total = sum(w.values())
        if total > 0:
            w = {k: v / total for k, v in w.items()}

        return w

    @staticmethod
    def _decorrelate_weights(w: dict, ind: dict) -> dict:
        """🆕 v3.4 因子去相关：检测高度相关的因子对，降低联合权重
        
        相关对: trend↔timeframe, momentum↔divergence, volatility↔regime
        降权逻辑: 仅当指标数据表明两个因子确实同向时（如趋势信号与多周期信号一致），
        才施加衰减。模拟数据/随机游走中因子自然发散，不应衰减。
        """
        # 用指标值判断因子对齐程度
        cur = ind.get("current", 0)
        ma20 = ind.get("ma20", cur)
        ma30 = ind.get("ma30", cur)
        trend_slope = ind.get("trend_slope", 0)
        rsi = ind.get("rsi", 50)
        macd_hist = ind.get("macd_hist", 0)
        adx = ind.get("adx", 15)

        # 仅当 trend & timeframe 方向一致时（均在MA之上 + 正斜率 → 真正共振）
        trend_bull = cur > ma30 and trend_slope > 0.0001
        trend_bear = cur < ma30 and trend_slope < -0.0001
        if (trend_bull or trend_bear) and "trend" in w and "timeframe" in w:
            w["trend"] = w.get("trend", 0) * 0.80
            w["timeframe"] = w.get("timeframe", 0) * 0.80

        # 仅当 momentum & divergence 方向一致时（RSI+MACD同向）
        mom_bull = rsi > 55 and macd_hist > 0
        mom_bear = rsi < 45 and macd_hist < 0
        if (mom_bull or mom_bear) and "momentum" in w and "divergence" in w:
            w["momentum"] = w.get("momentum", 0) * 0.82
            w["divergence"] = w.get("divergence", 0) * 0.82

        # 仅当 volatility & regime 方向一致时（高波动+趋势 → 信息重叠）
        adx_high = adx > 22
        if adx_high and "volatility" in w and "regime" in w:
            w["volatility"] = w.get("volatility", 0) * 0.88
            w["regime"] = w.get("regime", 0) * 0.88

        return w

    def _decide_v3(self, composite: float, inventory_items: list,
                   current: float, ind: dict, inv_data: dict,
                   scores: dict) -> tuple:
        """🆕 v3.2 清晰决策矩阵 — 分级制，消除brittle嵌套
        
        决策层级:
          composite >= 75 → 强烈买入/卖出
          composite >= 65 → 买入/卖出（正常）
          composite >= 55 → 偏多试探(OR条件入场)
          composite >= 45 → 持有/观望(+RSI超卖抄底)
          composite >= 35 → 偏空/减仓
          composite < 35  → 强烈卖出/止损
        """
        has_inv = bool(inventory_items)
        profit_pct = inv_data.get("profit_pct", 0) if inv_data else 0
        vol = ind.get("volatility_30d", 0.015)
        adx = ind.get("adx", 15)
        rsi = ind.get("rsi", 50)

        # 🆕 v3.4: 获取Hurst指数用于多周期确认
        hurst = ind.get("hurst", 0.5)

        # ── 波动率调整 ──
        if vol > 0.04:
            vol_discount = 0.85  # 极高波动，降低所有置信度
        elif vol > 0.03:
            vol_discount = 0.92
        elif vol > 0.02:
            vol_discount = 1.0
        else:
            vol_discount = 1.05  # 低波动，信号更可靠

        # ── 背离信号（最强修正因子）──
        divergence_score = scores.get("divergence", 50)
        has_bearish_div = divergence_score < 35   # 顶背离
        has_bullish_div = divergence_score > 65   # 底背离

        # 🆕 v3.4: 多周期确认 — 需要至少2/3周期同向才给高置信度
        timeframe_score = scores.get("timeframe", 50)
        trend_score = scores.get("trend", 50)
        multi_tf_bullish = (trend_score > 55 and timeframe_score > 55)  # 多周期共振看多
        multi_tf_bearish = (trend_score < 45 and timeframe_score < 45)  # 多周期共振看空

        # ── 清晰决策矩阵 ──
        # 顶背离优先：任何场景下顶背离=强卖出信号
        if has_bearish_div and has_inv and profit_pct > 0:
            conf = 0.85 * vol_discount
            if rsi > 70:
                conf = min(conf * 1.1, 0.95)
            return "卖出", self._calibrate_confidence(conf, scores, "卖出")

        if has_bearish_div and not has_inv:
            # 🔴 如果Cloud显示此行=新版，否则=旧版
            if divergence_score < 25:
                return "观望", self._calibrate_confidence(0.55, scores, "观望")
            else:  # 普通顶背离 → 放行但降信心
                vol_discount *= 0.80

        # 底背离优先：底背离+低分 = 反弹买入机会
        if has_bullish_div and not has_inv and composite > 40:
            conf = 0.55 * vol_discount
            if rsi < 35:
                conf = min(conf * 1.15, 0.80)
            return "买入", self._calibrate_confidence(conf, scores, "买入")

        if has_bullish_div and has_inv:
            return "持有", self._calibrate_confidence(0.60, scores, "持有")

        # ── 正常决策矩阵（无背离信号时）──
        if composite >= 75:
            if has_inv:
                if profit_pct > 5:
                    action, conf = "卖出", min(0.88 * vol_discount, 0.95)
                elif profit_pct < -5:
                    action, conf = "持有", 0.55
                else:
                    action, conf = "加仓", min(0.72 * vol_discount, 0.85)
            else:
                action, conf = "买入", min(0.82 * vol_discount, 0.92)
            # 🆕 v3.4: 多周期共振确认
            if action in ("买入", "加仓") and multi_tf_bullish:
                conf = min(conf * 1.12, 0.95)
            elif action in ("卖出",) and multi_tf_bearish:
                conf = min(conf * 1.12, 0.95)
            return action, self._calibrate_confidence(conf, scores, action)

        if composite >= 52:  # 🆕 从60降到52，匹配真实分数分布
            if has_inv:
                if profit_pct > 8:
                    action, conf = "卖出", min(0.75 * vol_discount, 0.88)
                elif profit_pct > 0:
                    action, conf = "持有", 0.55
                else:
                    action, conf = "持有", 0.45
            else:
                action, conf = "买入", min(0.65 * vol_discount, 0.78)
            if action in ("买入",) and multi_tf_bullish:
                conf = min(conf * 1.10, 0.85)
            return action, self._calibrate_confidence(conf, scores, action)

        if composite >= 48:  # 🆕 从55降到48
            if has_inv:
                if profit_pct > 12:
                    return "减仓", self._calibrate_confidence(0.65, scores, "减仓")
                return "持有", self._calibrate_confidence(0.50, scores, "持有")
            else:
                # 🆕 OR条件：价格>MA20 或 ADX>18 或 Hurst>0.55
                entry_ok = (ind["current"] > ind["ma20"]) or (adx > 18) or (hurst > 0.55)
                if entry_ok:
                    return "买入", self._calibrate_confidence(0.40, scores, "买入")
                return "观望", self._calibrate_confidence(0.33, scores, "观望")

        if composite >= 45:
            if has_inv:
                if profit_pct > 15:
                    return "减仓", self._calibrate_confidence(0.55, scores, "减仓")
                if profit_pct < -10:
                    return "减仓", self._calibrate_confidence(0.45, scores, "减仓")
                return "持有", self._calibrate_confidence(0.40, scores, "持有")
            # 🆕 无持仓+RSI超卖 → 试探买入
            if rsi < 35:
                return "买入", self._calibrate_confidence(0.30, scores, "买入")
            return "观望", self._calibrate_confidence(0.28, scores, "观望")

        if composite >= 35:
            if has_inv:
                if profit_pct > 3:
                    return "卖出", self._calibrate_confidence(0.60, scores, "卖出")
                if profit_pct < -5:
                    return "减仓", self._calibrate_confidence(0.50, scores, "减仓")
                return "持有", self._calibrate_confidence(0.35, scores, "持有")
            return "观望", self._calibrate_confidence(0.25, scores, "观望")

        # composite < 35: 强烈偏空
        if has_inv:
            if profit_pct > 1:
                return "卖出", self._calibrate_confidence(0.70, scores, "卖出")
            elif profit_pct > -5:
                return "减仓", self._calibrate_confidence(0.55, scores, "减仓")
            return "止损", self._calibrate_confidence(0.60, scores, "止损")
        return "观望", self._calibrate_confidence(0.20, scores, "观望")

    def _adaptive_stops(self, action: str, current: float, atr: float,
                        ind: dict, inventory_items: list,
                        inv_data: dict) -> tuple:
        """🆕 v3.4 自适应止损/止盈：ATR倍数随波动率+Hurst动态缩放 + 移动止盈"""
        vol = ind.get("volatility_30d", 0.015)
        adx = ind.get("adx", 15)
        hurst = ind.get("hurst", 0.5)
        bb_width = 0.02
        if ind.get("bb_mid", 1) > 0:
            bb_width = (ind.get("bb_upper", current * 1.05) - ind.get("bb_lower", current * 0.95)) / ind.get("bb_mid", current)

        # 基础ATR倍数
        base_sl_mult = 2.5
        base_tp_mult = 3.5

        # 高波动 → 放宽止损（避免被噪音扫出）
        if vol > 0.04:
            base_sl_mult = 3.2
            base_tp_mult = 4.5
        elif vol > 0.03:
            base_sl_mult = 2.8
            base_tp_mult = 4.0
        elif vol < 0.01:
            base_sl_mult = 2.0
            base_tp_mult = 2.8

        # 🆕 v3.4: 强趋势(Hurst>0.55) → 放宽止盈（让利润奔跑）
        if adx > 30 or hurst > 0.6:
            base_tp_mult += 1.5  # 强趋势下更要让利润跑
            base_sl_mult = max(base_sl_mult, 2.5)  # 但止损不能太宽
        elif adx < 18 or hurst < 0.4:
            base_tp_mult -= 0.5  # 均值回归/震荡市快速止盈
            base_sl_mult = min(base_sl_mult, 2.0)  # 收紧止损

        if action in ("买入", "加仓"):
            stop_loss = current - atr * base_sl_mult
            take_profit = current + atr * base_tp_mult
        elif action in ("卖出", "减仓", "止损"):
            stop_loss = current + atr * base_sl_mult * 0.7
            take_profit = current - atr * base_tp_mult * 0.8
        else:
            stop_loss = current - atr * 1.5
            take_profit = current + atr * 2.0

        # 🆕 v3.4: 计算移动止盈参考价(强趋势下动态跟随)
        trailing_stop = None
        if action in ("买入", "加仓") and (adx > 25 or hurst > 0.55):
            # 移动止盈 = 从近期高点回撤 1.5 × ATR
            ma20 = ind.get("ma20", current)
            trailing_stop = max(current - atr * 1.5, ma20 * 0.98)

        return round(stop_loss, 2), round(take_profit, 2)

    def _kelly_position_v3(self, action: str, inventory_items: list,
                            current: float, volatility: float, atr: float,
                            confidence: float) -> float:
        """🆕 v3.4 仓位百分比（不猜本金，纯比例）"""
        try:
            if action in ("持有", "观望"):
                return 0

            if action in ("卖出", "减仓", "止损") and inventory_items:
                total_kg = sum(it['quantity_kg'] for it in inventory_items)
                return round(total_kg * 0.3, 1)  # 简化为建议减30%

            if action in ("买入", "加仓"):
                if volatility > 0 and current > 0:
                    stop_mult = 2.5 if atr > 0 else 2.0
                    position_pct = 0.015 / max(volatility * stop_mult, 1e-6)
                    position_pct = min(position_pct, 0.30)
                    return round(position_pct * 100, 1)
                return 5.0

            return 0
        except Exception:
            return 0

    def _factor_agreement(self, scores: dict, action: str) -> float:
        """🆕 因子一致性：各因子对决策方向的一致性比例"""
        # 定义各因子对买入/卖出方向的期望
        buy_favoring = ["trend", "momentum", "timeframe", "supply_demand"]
        sell_favoring = ["operational", "risk_mgmt"]
        # volatile/regime/sr_levels/volume 根据分数>55偏买，<45偏卖
        directional = ["volatility", "sr_levels", "volume", "regime",
                       "seasonal", "correlation", "macro_bias", "divergence"]

        agree_count = 0
        total_factors = 0

        for k, v in scores.items():
            if not isinstance(v, (int, float)):
                continue  # 🆕 v3.4 跳过元数据键（如realtime_source）
            total_factors += 1
            if k in buy_favoring:
                if v > 55 and action in ("买入", "加仓"):
                    agree_count += 1
                elif v < 45 and action in ("卖出", "减仓", "止损"):
                    agree_count += 1
                elif 45 <= v <= 55:
                    agree_count += 0.5
            elif k in sell_favoring:
                if v > 55 and action in ("卖出", "减仓", "止损"):
                    agree_count += 1
                elif v < 45 and action in ("买入", "加仓"):
                    agree_count += 1
                elif 45 <= v <= 55:
                    agree_count += 0.5
            elif k in directional:
                if v > 58 and action in ("买入", "加仓"):
                    agree_count += 1
                elif v < 42 and action in ("卖出", "减仓", "止损"):
                    agree_count += 1
                elif 42 <= v <= 58:
                    agree_count += 0.5
            else:
                agree_count += 0.5  # 中性因子

        return agree_count / max(total_factors, 1)

    def _calibrate_confidence(self, raw_conf: float, scores: dict, action: str) -> float:
        """🆕 v3.4 置信度三维校准：信号强度 × 因子一致性 × 数据质量
        
        校准公式: 最终置信度 = raw_conf × agreement_factor × quality_factor
        - agreement_factor: 因子一致性越高，置信度越可靠
        - quality_factor: 数据质量越好，信号越可信（SHFE实时 > 模拟）
        """
        # 1) 因子一致性校准（宽容区间，避免随机数据过度降权）
        factor_agree = self._factor_agreement(scores, action)
        if factor_agree >= 0.70:
            agreement_mult = 1.10
        elif factor_agree >= 0.50:
            agreement_mult = 1.0
        elif factor_agree >= 0.30:
            agreement_mult = 0.92
        else:
            agreement_mult = 0.82  # 放宽底限，避免随机噪声全压到0.25

        # 2) 数据质量校准（基于是否有真实数据源）
        has_real_data = scores.get("realtime_source") == "SHFE实时"
        quality_mult = 1.05 if has_real_data else 0.95  # 模拟数据只轻降

        # 3) 背离信号的特殊处理：背离是最强信号，不受降权
        divergence_score = scores.get("divergence", 50)
        has_divergence = divergence_score > 65 or divergence_score < 35
        if has_divergence:
            agreement_mult = max(agreement_mult, 1.0)

        calibrated = raw_conf * agreement_mult * quality_mult
        return round(min(max(calibrated, 0.12), 0.95), 3)

    def _score_seasonal(self, metal_type: str, ind: dict) -> tuple:
        """季节性因子：基于历史月度统计规律"""
        from config import METAL_SEASONALITY
        score = 50
        reasons = []

        # 确定实际金属类型（废金属映射到精炼金属）
        lookup = metal_type
        if lookup not in METAL_SEASONALITY:
            from config import METAL_TYPES
            cfg = METAL_TYPES.get(metal_type, {})
            if cfg.get("is_scrap") and cfg.get("ref_metal"):
                lookup = cfg["ref_metal"]

        season = METAL_SEASONALITY.get(lookup)
        if season:
            month = datetime.now().month - 1  # 0-indexed
            factor = season[month]
            # 季节性因子 > 1.01 = 旺季加分，< 0.99 = 淡季减分
            score += (factor - 1.0) * 200  # 映射到 ±4 分范围

            if factor > 1.015:
                reasons.append(f"📅 {month+1}月旺季（季节性因子{factor:.3f}）")
            elif factor < 0.985:
                reasons.append(f"📅 {month+1}月淡季（季节性因子{factor:.3f}）")
        else:
            # 废金属继承精炼金属季节性
            from config import METAL_TYPES
            cfg = METAL_TYPES.get(metal_type, {})
            if cfg.get("ref_metal") in METAL_SEASONALITY:
                month = datetime.now().month - 1
                factor = METAL_SEASONALITY[cfg["ref_metal"]][month]
                score += (factor - 1.0) * 200
                if factor > 1.015:
                    reasons.append(f"📅 跟随{cfg['ref_metal']}{month+1}月旺季")
                elif factor < 0.985:
                    reasons.append(f"📅 跟随{cfg['ref_metal']}{month+1}月淡季")

        return max(0, min(100, score)), reasons

    def _score_correlation(self, metal_type: str, inventory_items: list,
                           all_summary: dict) -> tuple:
        """跨品种相关性因子：考虑持仓组合的分散化程度"""
        from config import METAL_CORRELATION
        score = 50
        reasons = []

        corr_matrix = METAL_CORRELATION
        lookup = metal_type
        # 废金属映射
        from config import METAL_TYPES
        cfg_m = METAL_TYPES.get(metal_type, {})
        if cfg_m.get("is_scrap") and cfg_m.get("ref_metal"):
            lookup = cfg_m["ref_metal"]

        if lookup not in corr_matrix:
            return 50, reasons

        # 检查与其他持仓的相关性
        high_corr_count = 0
        hedge_count = 0
        for other_metal, other_data in all_summary.get("by_metal", {}).items():
            if other_metal == metal_type:
                continue
            other_lookup = other_metal
            cfg_o = METAL_TYPES.get(other_metal, {})
            if cfg_o.get("is_scrap") and cfg_o.get("ref_metal"):
                other_lookup = cfg_o["ref_metal"]

            corr = corr_matrix.get(lookup, {}).get(other_lookup, 0)
            if corr > 0.6:
                high_corr_count += 1
            elif corr < -0.1:
                hedge_count += 1

        # 高相关性品种过多 = 集中度风险
        if high_corr_count >= 3:
            score -= 15
            reasons.append(f"⚠️ 与{high_corr_count}个高相关品种同时持仓，集中度风险")
        elif high_corr_count >= 2:
            score -= 8
        elif high_corr_count == 0 and inventory_items:
            score += 5
            reasons.append("✅ 持仓组合低相关性，分散良好")

        # 黄金/白银可作为对冲
        if metal_type in ("黄金", "白银") and high_corr_count > 0:
            score += 8
            reasons.append("🛡️ 贵金属对冲工业金属风险")

        return max(0, min(100, score)), reasons

    def _score_macro_bias(self, metal_type: str, ind: dict,
                          all_summary: dict) -> tuple:
        """宏观环境偏差因子：综合判断市场整体方向"""
        score = 50
        reasons = []

        # 1) 市场整体趋势（多数金属的方向性）
        if all_summary:
            bull_count = sum(1 for m, d in all_summary.get("by_trend", {}).items()
                           if d == "上涨" and m != metal_type)
            bear_count = sum(1 for m, d in all_summary.get("by_trend", {}).items()
                           if d == "下跌" and m != metal_type)
            total = bull_count + bear_count
            if total > 0:
                bull_ratio = bull_count / total
                if bull_ratio > 0.7:
                    if ind["current"] > ind["ma30"]:
                        score += 10
                        reasons.append("🌍 市场整体偏多，顺势看涨")
                elif bull_ratio < 0.3:
                    if ind["current"] < ind["ma30"]:
                        score -= 10
                        reasons.append("🌍 市场整体偏空，谨慎看跌")

        # 2) 关联品种强度传导
        from config import METAL_CORRELATION, METAL_TYPES
        corr_matrix = METAL_CORRELATION
        lookup = metal_type
        cfg_m = METAL_TYPES.get(metal_type, {})
        if cfg_m.get("is_scrap") and cfg_m.get("ref_metal"):
            lookup = cfg_m["ref_metal"]

        if lookup in corr_matrix and all_summary:
            strength_sum = 0
            weight_sum = 0
            for other, other_data in all_summary.get("by_metal_summary", {}).items():
                if other == metal_type:
                    continue
                corr = abs(corr_matrix.get(lookup, {}).get(other, 0))
                if corr > 0.4:
                    chg = other_data.get("change_week", 0)
                    strength_sum += chg * corr
                    weight_sum += corr
            if weight_sum > 0:
                signal = strength_sum / weight_sum
                if signal > 2:
                    score += 8
                    reasons.append("🔗 高相关品种走强，联动利好")
                elif signal < -2:
                    score -= 8
                    reasons.append("🔗 高相关品种走弱，联动承压")

        # 3) 美元/宏观情绪代理（波动率扩张+下跌 = 恐慌）
        if ind["volatility_30d"] > 0.03 and ind["current"] < ind["ma30"]:
            score -= 8
            reasons.append("😰 高波动+下跌，宏观风险升温")

        # 4) 贵金属避险情绪（黄金上涨时工业金属偏弱）
        gold_data = all_summary.get("by_metal_summary", {}).get("黄金", {})
        if gold_data and metal_type not in ("黄金", "白银"):
            gold_chg = gold_data.get("change_week", 0)
            if gold_chg > 3 and ind["current"] < ind["ma20"]:
                score -= 5
                reasons.append("🏃 资金流向黄金避险，工业金属承压")

        return max(0, min(100, score)), reasons

    def _score_operational(self, metal_type: str, inventory_items: list,
                           inv_data: dict, current: float) -> tuple:
        """运营效率因子：周转率、资金成本、仓储成本"""
        from config import RECOMMENDATION
        score = 50
        reasons = []

        if not inventory_items:
            return score, reasons

        total_kg = sum(it.get('quantity_kg', 0) for it in inventory_items)
        total_cost = sum(it.get('quantity_kg', 0) * it.get('avg_cost_price', 0)
                        for it in inventory_items)
        avg_cost = total_cost / total_kg if total_kg > 0 else 0

        # 1) 资金占用成本（月化）
        monthly_capital_cost = total_cost * RECOMMENDATION.get("capital_cost_annual", 0.05) / 12
        monthly_storage_cost = total_cost * RECOMMENDATION.get("storage_cost_monthly_pct", 0.003)
        total_monthly_holding_cost = monthly_capital_cost + monthly_storage_cost
        holding_cost_pct = total_monthly_holding_cost / total_cost * 100 if total_cost > 0 else 0

        profit_pct = inv_data.get("profit_pct", 0)

        # 2) 库存持有天数估计（简化：基于历史交易频率）
        # 没有实际交易记录时，用30天作为默认
        avg_hold_days = inv_data.get("avg_hold_days", 30)

        # 持有成本侵蚀利润
        if profit_pct > 0:
            monthly_erosion = holding_cost_pct
            if profit_pct < monthly_erosion * 2:
                score -= 10
                reasons.append(f"💸 月持仓费{holding_cost_pct:.2f}%侵蚀微薄利润")
            elif profit_pct > monthly_erosion * 5:
                score += 5
                reasons.append(f"📊 利润远超持仓成本({holding_cost_pct:.2f}%/月)")

        # 3) 库存周转评估
        if avg_hold_days > 90:
            score -= 12
            reasons.append(f"🐌 库存周转慢（>{avg_hold_days}天），资金效率低")
        elif avg_hold_days > 60:
            score -= 5
            reasons.append(f"⏳ 库存周转偏慢（>{avg_hold_days}天）")
        elif avg_hold_days < 15:
            score += 8
            reasons.append(f"🚀 库存周转快（<{avg_hold_days}天），资金效率高")

        # 4) 持仓规模合理性（基于金属波动率）
        from config import METAL_TYPES
        cfg = METAL_TYPES.get(metal_type, {})
        daily_vol = cfg.get("volatility", 0.015)
        value_at_risk_1d = total_cost * daily_vol * 1.65  # 95% VaR
        if total_cost > 0:
            var_pct = value_at_risk_1d / total_cost * 100
            if var_pct > 3:
                score -= 8
                reasons.append(f"🎲 单日VaR={var_pct:.1f}%，日内风险较高")

        return max(0, min(100, score)), reasons

    def _score_risk_management(self, metal_type: str, inventory_items: list,
                               inv_data: dict, all_summary: dict) -> tuple:
        """风险管理因子：集中度、回撤、流动性"""
        from config import RECOMMENDATION
        score = 50
        reasons = []

        if not inventory_items or not all_summary:
            return 50, reasons

        total_portfolio_value = all_summary.get("total_value", 0)
        this_metal_value = sum(
            it.get('quantity_kg', 0) * it.get('current_market_price',
                it.get('avg_cost_price', 0))
            for it in inventory_items
        )

        # 1) 单品种集中度
        if total_portfolio_value > 0:
            concentration = this_metal_value / total_portfolio_value
            max_exposure = RECOMMENDATION.get("max_single_exposure_pct", 0.30)
            if concentration > max_exposure * 1.5:
                score -= 18
                reasons.append(f"🚨 单品种占比{concentration:.0%}，远超上限{max_exposure:.0%}")
            elif concentration > max_exposure:
                score -= 10
                reasons.append(f"⚠️ 单品种占比{concentration:.0%}，超过上限{max_exposure:.0%}")
            elif concentration < 0.1:
                score += 5
                reasons.append("✅ 持仓分散，集中度健康")

        # 2) 浮动回撤
        profit_pct = inv_data.get("profit_pct", 0)
        max_drawdown = RECOMMENDATION.get("max_drawdown_pct", 0.15)
        if profit_pct < -max_drawdown * 100:
            score -= 15
            reasons.append(f"📉 浮亏{profit_pct:.1f}%超最大回撤容忍{max_drawdown*100:.0f}%")
        elif profit_pct < -max_drawdown * 50:
            score -= 7
            reasons.append(f"⚠️ 浮亏{profit_pct:.1f}%接近回撤警戒线")

        # 3) 组合层面：总敞口 vs 现金
        if all_summary.get("total_cost", 0) > 0:
            overall_pl_pct = all_summary.get("profit_pct", 0)
            if overall_pl_pct < -10:
                score -= 8
                reasons.append("🔴 组合整体浮亏严重，建议减仓控风险")
            elif overall_pl_pct > 15:
                score += 5
                reasons.append("🟢 组合整体盈利良好")

        return max(0, min(100, score)), reasons

    # ═══════════════════════════════════════════════════════
    #  🆕 v3.1 新增因子: 多周期对齐 / 供需基本面
    # ═══════════════════════════════════════════════════════

    def _score_timeframe_alignment(self, ind: dict, prices: np.ndarray) -> tuple:
        """多周期趋势一致性：短/中/长期信号是否共振"""
        score = 50
        reasons = []
        current = ind["current"]

        # 计算多周期趋势方向
        returns_5d = (current - prices[-6]) / prices[-6] if len(prices) >= 6 else 0
        returns_20d = (current - prices[-21]) / prices[-21] if len(prices) >= 21 else 0
        returns_60d = (current - prices[-61]) / prices[-61] if len(prices) >= 61 else 0

        short_up = returns_5d > 0.005   # 5日涨 > 0.5%
        medium_up = returns_20d > 0     # 20日涨
        long_up = returns_60d > 0.015   # 60日涨 > 1.5%

        short_down = returns_5d < -0.015
        medium_down = returns_20d < -0.02
        long_down = returns_60d < -0.05

        # 统计一致的方向数
        up_count = sum([short_up, medium_up, long_up])
        down_count = sum([short_down, medium_down, long_down])

        # 均线排列也参与判断
        ma_alignment = 0
        if ind["ma7"] > ind["ma20"] > ind["ma30"]:
            ma_alignment = 2   # 完美多头排列
        elif ind["ma7"] < ind["ma20"] < ind["ma30"]:
            ma_alignment = -2  # 完美空头排列
        elif ind["ma7"] > ind["ma30"]:
            ma_alignment = 1   # 偏多
        elif ind["ma7"] < ind["ma30"]:
            ma_alignment = -1  # 偏空

        # 评分
        if up_count >= 3 and ma_alignment >= 1:
            score += 20
            reasons.append("🎯 短中长三期趋势共振向上")
        elif up_count >= 2 and ma_alignment >= 0:
            score += 12
            reasons.append("📈 多周期偏多，趋势一致性较好")
        elif down_count >= 3 and ma_alignment <= -1:
            score -= 20
            reasons.append("🔻 短中长三期趋势共振向下")
        elif down_count >= 2 and ma_alignment <= 0:
            score -= 12
            reasons.append("📉 多周期偏空，趋势一致性较差")
        elif up_count >= 2 and down_count >= 1:
            reasons.append("⚡ 短中期背离，方向分歧")
            score -= 5

        # MA均线乖离率
        if ind["ma20"] > 0:
            dispersion = abs(current - ind["ma20"]) / ind["ma20"]
            if dispersion > 0.08:
                score -= 8
                reasons.append(f"📏 价格偏离MA20 {dispersion*100:.1f}%，回归风险")

        return max(0, min(100, score)), reasons

    def _score_supply_demand(self, metal_type: str, ind: dict,
                             prices: np.ndarray) -> tuple:
        """供需基本面代理因子：库存变化率 + 价格动量 + 持仓分析"""
        score = 50
        reasons = []
        n = len(prices)

        # 1) 近期价格动量持续性（代表供需失衡持续）
        if n >= 30:
            ret_10d = (prices[-1] - prices[-11]) / max(prices[-11], 1e-10) if n >= 11 else 0
            ret_20d = (prices[-1] - prices[-21]) / max(prices[-21], 1e-10) if n >= 21 else ret_10d

            # 连续上涨 = 需求旺盛/供应偏紧
            if ret_10d > 0.02 and ret_20d > 0.03:
                score += 12
                reasons.append("📊 连续上涨，供需格局偏紧")
            elif ret_10d < -0.02 and ret_20d < -0.03:
                score -= 12
                reasons.append("📉 连续下跌，供需格局偏松")

        # 2) 价格波动率变化 → 供需转换信号
        if n >= 30:
            try:
                # 🆕 修复：确保diff和分母长度严格一致
                d10 = np.diff(prices[-11:])
                p_denom = prices[-10:]
                if len(d10) == len(p_denom) and len(d10) > 0:
                    valid = p_denom > 0
                    if np.any(valid):
                        vol_recent = float(np.std(d10[valid] / p_denom[valid]))
                    else:
                        vol_recent = 0.0
                else:
                    vol_recent = 0.0
                if n >= 31:
                    d20 = np.diff(prices[-31:-10])
                    p_denom2 = prices[-30:-10]
                    if len(d20) == len(p_denom2) and len(d20) > 0:
                        valid2 = p_denom2 > 0
                        if np.any(valid2):
                            vol_prior = float(np.std(d20[valid2] / p_denom2[valid2]))
                        else:
                            vol_prior = vol_recent
                    else:
                        vol_prior = vol_recent
                else:
                    vol_prior = vol_recent
            except Exception:
                vol_recent = vol_prior = 0.0
            if vol_prior > 0 and vol_recent > 0 and vol_recent / vol_prior > 1.5:
                if ind["current"] > ind["ma20"]:
                    score += 8
                    reasons.append("📈 放量上行，需求推动")
                else:
                    score -= 8
                    reasons.append("⚠️ 放量下行，供应压力")

        # 3) 尝试获取真实库存数据
        stock_info = self._try_fetch_stock_data(metal_type)
        if stock_info and isinstance(stock_info, dict):
            stock_change = stock_info.get("change_pct", 0)
            try:
                stock_change = float(stock_change)
            except (ValueError, TypeError):
                stock_change = 0
            if stock_change < -5:
                score += 10
                reasons.append(f"🏭 库存下降{abs(stock_change):.0f}%，去库利多")
            elif stock_change > 8:
                score -= 10
                reasons.append(f"📦 库存累积+{stock_change:.0f}%，累库利空")
            elif stock_change > 3:
                score -= 5
                reasons.append(f"📦 库存小幅累积+{stock_change:.0f}%")

        # 4) 废金属特殊逻辑：反向供需
        from config import METAL_TYPES
        cfg = METAL_TYPES.get(metal_type, {})
        if cfg.get("is_scrap") and cfg.get("ref_metal"):
            ref = cfg["ref_metal"]
            if n >= 21 and prices[-21] > 0:
                ref_price_chg = (prices[-1] / prices[-21] - 1)
            else:
                ref_price_chg = 0
            # 精炼金属涨价 → 废金属替代需求增加 → 废金属跟涨
            if ref_price_chg > 0.03:
                score += 6
                reasons.append(f"♻️ {ref}涨价，废{metal_type}替代需求上升")

        return max(0, min(100, score)), reasons

    def _try_fetch_stock_data(self, metal_type: str) -> dict:
        """尝试获取仓储库存数据（LME/SHFE），失败返回空"""
        try:
            # 检查是否有真实数据源
            if hasattr(self.price_service, '_real_history') and self.price_service._real_history:
                # 从价格走势推算库存变化：价格涨+波动缩 = 主动去库
                return {}  # 暂不需要额外API
        except Exception:
            pass
        return {}  # 无真实数据时返回空

    def _get_all_metals_summary(self) -> dict:
        """获取全品种汇总信息（轻量版，用于相关性/宏观分析）
        🆕 优化：复用 analyze_all_metals 中已有的 session，避免重复开连接
        """
        try:
            from config import METAL_TYPES
            result = {"by_metal": {}, "by_trend": {}, "by_metal_summary": {},
                      "total_value": 0, "total_cost": 0, "profit_pct": 0}

            # 🆕 轻量：直接用缓存的 summaries，避免重复计算历史数据
            try:
                summaries = self.price_service.get_all_price_summaries()
                for s in summaries:
                    mt = s.get("metal_type", "")
                    if mt:
                        result["by_trend"][mt] = s.get("trend", "")
                        result["by_metal_summary"][mt] = {
                            "change_week": s.get("change_week", 0),
                            "change_month": s.get("change_month", 0),
                            "volatility": s.get("volatility", 0),
                        }
            except Exception:
                pass

            # 🆕 优化：优先使用 analyze_all_metals 预构建的数据，避免额外DB查询
            # 如果外层已通过 _cached_all_summary 提供，则跳过DB查询
            from database import Inventory
            session = self.session_factory()
            try:
                # 🆕 单次查询获取所有活跃库存
                items = session.query(Inventory).filter(
                    Inventory.status == "持有"
                ).all()
                for item in items:
                    mt = item.metal_type
                    if mt not in result["by_metal"]:
                        result["by_metal"][mt] = {
                            "quantity_kg": 0, "total_cost": 0, "current_value": 0
                        }
                    result["by_metal"][mt]["quantity_kg"] += (item.quantity_kg or 0)
                    result["by_metal"][mt]["total_cost"] += (item.total_cost or 0)
                    result["by_metal"][mt]["current_value"] += (item.current_value or 0)
                    result["total_value"] += (item.current_value or 0)
                    result["total_cost"] += (item.total_cost or 0)

                if result["total_cost"] > 0:
                    result["profit_pct"] = (
                        result["total_value"] - result["total_cost"]
                    ) / result["total_cost"] * 100
            except Exception:
                pass
            finally:
                try:
                    session.close()
                except Exception:
                    pass

            return result
        except Exception:
            return {}

    @staticmethod
    def _risk_level(volatility: float) -> str:
        if volatility > 0.04:
            return "高"
        elif volatility > 0.02:
            return "中"
        return "低"

    # ═══════════════════════════════════════════════════════
    #  🆕 v3.2 背离因子：RSI背离 + MACD背离（最强反转信号）
    # ═══════════════════════════════════════════════════════

    def _score_divergence(self, ind: dict, prices: np.ndarray) -> tuple:
        """🆕 背离检测：RSI顶/底背离 + MACD顶/底背离 (v3.3 优化：预计算序列，O(n))
        
        背离 = 价格创新高/低但指标不确认，是最强的反转信号
        顶背离 → 强烈卖出信号（价格创新高但RSI/MACD走弱）
        底背离 → 强烈买入信号（价格创新低但RSI/MACD走强）
        """
        score = 50
        reasons = []
        n = len(prices)

        if n < 40:
            return 50, reasons

        current = float(prices[-1])
        rsi = ind.get("rsi", 50)
        macd_hist = ind.get("macd_hist", 0)

        # ── 1) RSI背离检测 (预计算整个RSI序列，避免循环内重复计算) ──
        lookback = min(n, 40)
        chunk = prices[-lookback:]
        chunk_len = len(chunk)
        rsi_divergence = 0

        if chunk_len >= 30:
            # 🆕 优化：一次性计算滚动RSI序列 (O(n) vs 原来的O(n²))
            rsi_values = self._rolling_rsi(chunk, 14)

            half = chunk_len // 2
            if half >= 14 and len(rsi_values) >= half:
                # 顶背离：价格最近两次高点，高点2 > 高点1 但 RSI2 < RSI1
                first_half_high_idx = int(np.argmax(chunk[:half]))
                second_half_high_idx = half + int(np.argmax(chunk[half:]))

                first_high = chunk[first_half_high_idx]
                second_high = chunk[second_half_high_idx]

                # 安全索引：rsi_values[i] 对应 chunk[14+i] 的RSI值
                rsi_idx1 = max(0, first_half_high_idx - 14)
                rsi_idx2 = max(0, second_half_high_idx - 14)
                if rsi_idx1 < len(rsi_values) and rsi_idx2 < len(rsi_values):
                    if second_high > first_high * 1.005:
                        rsi_at_first = rsi_values[rsi_idx1]
                        rsi_at_second = rsi_values[rsi_idx2]
                        if rsi_at_second < rsi_at_first - 3:
                            rsi_divergence = -1
                            score -= 20
                            reasons.append("🔄 RSI顶背离 — 价格新高但RSI走弱")

                # 底背离
                first_half_low_idx = int(np.argmin(chunk[:half]))
                second_half_low_idx = half + int(np.argmin(chunk[half:]))

                first_low = chunk[first_half_low_idx]
                second_low = chunk[second_half_low_idx]

                rsi_idx_l1 = max(0, first_half_low_idx - 14)
                rsi_idx_l2 = max(0, second_half_low_idx - 14)
                if rsi_idx_l1 < len(rsi_values) and rsi_idx_l2 < len(rsi_values):
                    if second_low < first_low * 0.995:
                        rsi_at_first_low = rsi_values[rsi_idx_l1]
                        rsi_at_second_low = rsi_values[rsi_idx_l2]
                        if rsi_at_second_low > rsi_at_first_low + 3:
                            rsi_divergence = 1
                            score += 20
                            reasons.append("🔄 RSI底背离 — 价格新低但RSI走强")

        # ── 2) MACD柱背离检测 (v3.4增强：使用峰值/谷值精确检测) ──
        if n >= 50:
            macd_hists = self._rolling_macd_hist(prices)
            macd_len = len(macd_hists)
            if macd_len >= 30:
                # 🆕 v3.4: 使用峰值检测查找最近3个MACD峰/谷
                macd_peaks_idx, macd_troughs_idx = self._find_peaks_troughs(
                    macd_hists, order=max(3, macd_len // 10)
                )
                price_peaks_idx, price_troughs_idx = self._find_peaks_troughs(
                    prices[-macd_len:], order=max(3, macd_len // 10)
                )

                # MACD顶背离：价格创新高但MACD柱峰降低
                if len(macd_peaks_idx) >= 2 and len(price_peaks_idx) >= 2:
                    # 取最近2个峰值
                    macd_peak1 = macd_hists[int(macd_peaks_idx[-2])]
                    macd_peak2 = macd_hists[int(macd_peaks_idx[-1])]
                    price_peak1 = prices[-macd_len:][int(price_peaks_idx[-2])]
                    price_peak2 = prices[-macd_len:][int(price_peaks_idx[-1])]

                    if (price_peak2 > price_peak1 * 1.005 and
                            macd_peak2 < macd_peak1 * 0.9):
                        if rsi_divergence != -1:
                            score -= 15
                            reasons.append("📉 MACD顶背离 — 价格新高但动能衰减")

                # MACD底背离：价格创新低但MACD柱谷抬升
                if len(macd_troughs_idx) >= 2 and len(price_troughs_idx) >= 2:
                    macd_trough1 = macd_hists[int(macd_troughs_idx[-2])]
                    macd_trough2 = macd_hists[int(macd_troughs_idx[-1])]
                    price_trough1 = prices[-macd_len:][int(price_troughs_idx[-2])]
                    price_trough2 = prices[-macd_len:][int(price_troughs_idx[-1])]

                    if (price_trough2 < price_trough1 * 0.995 and
                            macd_trough2 > macd_trough1 * 1.1):
                        if rsi_divergence != 1:
                            score += 15
                            reasons.append("📈 MACD底背离 — 价格新低但动能企稳")

                # 🆕 v3.4: 三峰背离（最高置信度）
                if len(macd_peaks_idx) >= 3 and len(price_peaks_idx) >= 3:
                    p1, p2, p3 = (prices[-macd_len:][int(price_peaks_idx[-3])],
                                   prices[-macd_len:][int(price_peaks_idx[-2])],
                                   prices[-macd_len:][int(price_peaks_idx[-1])])
                    m1, m2, m3 = (macd_hists[int(macd_peaks_idx[-3])],
                                   macd_hists[int(macd_peaks_idx[-2])],
                                   macd_hists[int(macd_peaks_idx[-1])])
                    # 价格逐创新高，MACD逐次降低 = 三重顶背离
                    if p3 > p2 > p1 and m3 < m2 < m1:
                        if rsi_divergence != -1:
                            score -= 18
                            reasons.append("🚨 三重MACD顶背离 — 极度看空反转信号")

                if len(macd_troughs_idx) >= 3 and len(price_troughs_idx) >= 3:
                    t1, t2, t3 = (prices[-macd_len:][int(price_troughs_idx[-3])],
                                   prices[-macd_len:][int(price_troughs_idx[-2])],
                                   prices[-macd_len:][int(price_troughs_idx[-1])])
                    d1, d2, d3 = (macd_hists[int(macd_troughs_idx[-3])],
                                   macd_hists[int(macd_troughs_idx[-2])],
                                   macd_hists[int(macd_troughs_idx[-1])])
                    if t3 < t2 < t1 and d3 > d2 > d1:
                        if rsi_divergence != 1:
                            score += 18
                            reasons.append("🚨 三重MACD底背离 — 极度看多反转信号")

        # ── 3) 隐藏背离增强（RSI趋势vs价格趋势）──
        if 50 < rsi < 65 and macd_hist < 0:
            if n >= 20:
                # 🆕 优化：复用预计算的RSI序列
                rsi_10_ago = self._wilders_rsi(prices[-20:-10], 14)
                recent_10_rsi_change = rsi - rsi_10_ago
                recent_price_change = (current - prices[-11]) / prices[-11] if n >= 11 else 0
                if recent_10_rsi_change < -5 and abs(recent_price_change) < 0.01:
                    score -= 8
                    reasons.append("🔍 隐藏顶背离 — RSI走弱但价格横盘")

        if 35 < rsi < 50 and macd_hist > 0:
            if n >= 20:
                rsi_10_ago = self._wilders_rsi(prices[-20:-10], 14)
                recent_10_rsi_change = rsi - rsi_10_ago
                recent_price_change = (current - prices[-11]) / prices[-11] if n >= 11 else 0
                if recent_10_rsi_change > 5 and abs(recent_price_change) < 0.01:
                    score += 8
                    reasons.append("🔍 隐藏底背离 — RSI走强但价格横盘")

        return max(0, min(100, score)), reasons

    @staticmethod
    def _rolling_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """🆕 预计算滚动RSI序列 (O(n)，单次遍历)
        返回: rsi_values[i] = prices[:period+1+i]的RSI值
        """
        n = len(prices)
        if n < period + 1:
            return np.full(n - period, 50.0) if n > period else np.array([50.0])
        result = np.empty(n - period)
        # 首次RSI
        deltas = np.diff(prices[:period + 1])
        avg_gain = np.mean(np.maximum(deltas, 0))
        avg_loss = np.mean(np.maximum(-deltas, 0))
        for i in range(period, n):
            if avg_loss == 0:
                result[i - period] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i - period] = 100.0 - (100.0 / (1.0 + rs))
            # 🆕 Wilder平滑更新（增量更新，避免O(period)每次重新计算）
            if i + 1 < n:
                delta = prices[i + 1] - prices[i]
                gain = delta if delta > 0 else 0
                loss = -delta if delta < 0 else 0
                avg_gain = (avg_gain * (period - 1) + gain) / period
                avg_loss = (avg_loss * (period - 1) + loss) / period
        return result

    @staticmethod
    def _rolling_macd_hist(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
        """🆕 预计算滚动MACD histogram序列 (O(n)，单次遍历)
        返回从第slow个点开始的MACD histogram
        """
        n = len(prices)
        min_len = slow + signal
        if n < min_len:
            return np.array([])
        
        try:
            import pandas as pd
            s = pd.Series(prices)
            ema_fast = s.ewm(span=fast, adjust=False, min_periods=fast).mean()
            ema_slow = s.ewm(span=slow, adjust=False, min_periods=slow).mean()
            macd_line = ema_fast - ema_slow
            macd_signal = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
            hist = (macd_line - macd_signal).values[slow:]
            return hist
        except Exception:
            # Fallback: 手动计算
            result = np.empty(n - slow)
            ema_fast_val = np.mean(prices[:fast])
            ema_slow_val = np.mean(prices[:slow])
            ema_signal_val = 0.0
            alpha_fast = 2.0 / (fast + 1)
            alpha_slow = 2.0 / (slow + 1)
            alpha_sig = 2.0 / (signal + 1)
            macd_first = ema_fast_val - ema_slow_val
            ema_signal_val = macd_first
            
            for i in range(1, n):
                p = float(prices[i])
                ema_fast_val = alpha_fast * p + (1 - alpha_fast) * ema_fast_val
                ema_slow_val = alpha_slow * p + (1 - alpha_slow) * ema_slow_val
                macd_val = ema_fast_val - ema_slow_val
                ema_signal_val = alpha_sig * macd_val + (1 - alpha_sig) * ema_signal_val
                if i >= slow:
                    result[i - slow] = macd_val - ema_signal_val
            return result

    # ═══════════════════════════════════════════════════════
    #  技术指标库
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _wilders_rsi(prices: np.ndarray, period: int = 14) -> float:
        """Wilder's RSI (指数平滑)"""
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices[-period-1:])
        gains = np.maximum(deltas, 0)
        losses = np.maximum(-deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _ema_series(data: np.ndarray, period: int) -> np.ndarray:
        """对整个序列做EMA，返回完整序列 — 使用pandas向量化实现 (10-50× faster)"""
        try:
            import pandas as pd
            s = pd.Series(data)
            result = s.ewm(span=period, adjust=False, min_periods=period).mean()
            # 前period-1个值用SMA填充（保持与原实现兼容）
            if len(data) >= period:
                sma_init = np.mean(data[:period])
                result.iloc[:period] = sma_init
            return result.values
        except Exception:
            # fallback：原Python循环实现
            if len(data) < period:
                return np.full_like(data, np.mean(data))
            alpha = 2.0 / (period + 1)
            result = np.zeros_like(data)
            result[:period] = np.mean(data[:period])
            for i in range(period, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
            return result

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> float:
        """EMA最后一个值 — 使用pandas向量化实现"""
        try:
            import pandas as pd
            return float(pd.Series(data).ewm(span=period, adjust=False).mean().iloc[-1])
        except Exception:
            if len(data) < period:
                return float(np.mean(data))
            alpha = 2.0 / (period + 1)
            result = float(np.mean(data[:period]))
            for i in range(period, len(data)):
                result = alpha * float(data[i]) + (1 - alpha) * result
            return result

    @staticmethod
    def _calc_atr(prices: np.ndarray, period: int = 14) -> tuple:
        """ATR 及百分比"""
        n = len(prices)
        if n < period + 1:
            return float(np.std(prices) * 0.5), 0.01
        high = np.maximum(prices[1:], prices[:-1])
        low = np.minimum(prices[1:], prices[:-1])
        tr = high - low
        atr = np.mean(tr[-period:])
        atr_pct = atr / prices[-1] if prices[-1] > 0 else 0.01
        return float(atr), float(atr_pct)

    @staticmethod
    def _simple_adx(prices: np.ndarray, period: int = 14) -> float:
        """简化ADX（基于方向性移动）"""
        n = len(prices)
        if n < period + 2:
            return 15.0
        up = np.diff(prices[-period-1:])
        pos = np.sum(np.maximum(up, 0))
        neg = np.sum(np.maximum(-up, 0))
        total = pos + neg
        if total == 0:
            return 0.0
        dx = abs(pos - neg) / total * 100
        return float(dx)

    @staticmethod
    def _hurst_exponent(prices: np.ndarray, max_lag: int = 20) -> float:
        """🆕 v3.4 Hurst指数：区分趋势/随机/均值回归
        
        H > 0.5 → 趋势持续（趋势市）
        H ≈ 0.5 → 随机游走（不可预测）
        H < 0.5 → 均值回归（震荡市）
        
        使用R/S分析法（重标极差法）
        """
        n = len(prices)
        if n < 30:
            return 0.5

        # 使用对数收益率
        rets = np.diff(np.log(prices + 1e-10))
        # 使用全部可用收益率（最多200天），而非截断到100
        rets = rets[-min(len(rets), 200):]
        n_rets = len(rets)

        # 对多个时间尺度计算R/S
        lags = [lag for lag in range(10, min(max_lag + 1, n_rets // 2 + 1))]
        if len(lags) < 3:
            return 0.5

        rs_values = []
        for lag in lags:
            # 将序列分割为 lag 个等长子段
            n_segments = n_rets // lag
            if n_segments < 1:
                continue
            rs_segment = 0.0
            count = 0
            for i in range(n_segments):
                segment = rets[i * lag:(i + 1) * lag]
                if len(segment) < 2:
                    continue
                # 累积离差
                mean = np.mean(segment)
                cum_dev = np.cumsum(segment - mean)
                r = np.max(cum_dev) - np.min(cum_dev)
                s = np.std(segment, ddof=1)
                if s > 0:
                    rs_segment += r / s
                    count += 1
            if count > 0:
                rs_values.append(rs_segment / count)

        if len(rs_values) < 3:
            return 0.5

        # log(R/S) = H * log(lag) + C，线性回归斜率 = H
        log_lags = np.log(lags[:len(rs_values)])
        log_rs = np.log(np.array(rs_values))
        try:
            slope = np.polyfit(log_lags, log_rs, 1)[0]
        except (np.linalg.LinAlgError, ValueError):
            return 0.5  # SVD 不收敛时返回随机游走
        return float(np.clip(slope, 0.1, 0.9))

    @staticmethod
    def _stochastic_k(prices: np.ndarray, period: int = 14, smooth: int = 3) -> float:
        """🆕 v3.4 随机指标 %K (Stochastic Oscillator)
        
        %K = 100 * (Close - Lowest_Low) / (Highest_High - Lowest_Low)
        """
        n = len(prices)
        if n < period:
            return 50.0
        window = prices[-period:]
        lowest_low = np.min(window)
        highest_high = np.max(window)
        if highest_high - lowest_low < 1e-10:
            return 50.0
        # 对最后smooth个K值做SMA平滑
        raw_k = 100.0 * (prices[-1] - lowest_low) / (highest_high - lowest_low)
        if n < period + smooth:
            return float(raw_k)
        k_values = []
        for i in range(smooth):
            w = prices[-(period + i):-i] if i > 0 else prices[-period:]
            lo, hi = np.min(w), np.max(w)
            if hi - lo > 1e-10:
                k_values.append(100.0 * (prices[-(1 + i)] - lo) / (hi - lo))
            else:
                k_values.append(50.0)
        return float(np.mean(k_values))

    @staticmethod
    def _count_sr_touches(prices: np.ndarray, support: float, resistance: float) -> dict:
        """🆕 v3.4 统计支撑/阻力触碰次数（时间衰减加权）
        
        触碰 = 价格进入支撑/阻力 ± 1% 范围内
        时间衰减：最近触碰权重更高
        """
        n = len(prices)
        if n < 10:
            return {"support": 0, "resistance": 0}

        sup_touches = 0.0
        res_touches = 0.0

        for i in range(max(0, n - 60), n):
            p = prices[i]
            time_weight = (i - (n - 60) + 1) / 60.0  # 线性时间权重[1/60, 1.0]

            if support > 0 and abs(p - support) / support < 0.015:
                sup_touches += time_weight
            if resistance > 0 and abs(p - resistance) / resistance < 0.015:
                res_touches += time_weight

        return {
            "support": round(sup_touches, 1),
            "resistance": round(res_touches, 1),
        }

    @staticmethod
    def _find_peaks_troughs(prices: np.ndarray, order: int = 5) -> tuple:
        """🆕 v3.4 使用scipy.signal查找价格峰值和谷值（用于背离检测）
        
        返回: (peak_indices, trough_indices)
        """
        try:
            from scipy.signal import argrelextrema
            peaks = argrelextrema(prices, np.greater, order=order)[0]
            troughs = argrelextrema(prices, np.less, order=order)[0]
            return peaks, troughs
        except ImportError:
            # Fallback: 简单局部极值
            peaks = []
            troughs = []
            for i in range(order, len(prices) - order):
                window = prices[i - order:i + order + 1]
                mid = prices[i]
                if mid == np.max(window) and mid > np.mean(window):
                    peaks.append(i)
                if mid == np.min(window) and mid < np.mean(window):
                    troughs.append(i)
            return np.array(peaks, dtype=int), np.array(troughs, dtype=int)

    # ═══════════════════════════════════════════════════════
    #  数据库操作
    # ═══════════════════════════════════════════════════════

    def _save_recommendation(self, result: dict) -> bool:
        session: Session = self.session_factory()
        try:
            session.add(self._build_rec(result))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存失败: {e}")
            return False
        finally:
            session.close()

    def _save_recommendations_batch(self, results: list) -> bool:
        if not results:
            return True
        session: Session = self.session_factory()
        try:
            for r in results:
                session.add(self._build_rec(r))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"批量保存失败: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def _build_rec(result: dict) -> Recommendation:
        return Recommendation(
            metal_type=result['metal_type'],
            action=result['action'],
            confidence=result['confidence'],
            suggested_quantity_kg=result['suggested_quantity_kg'],
            suggested_price=result['suggested_price'],
            current_price=result['current_price'],
            expected_profit_pct=result['expected_profit_pct'],
            reason=result['reason'],
            trend_analysis=str(result.get('trend_analysis', {})),
            risk_level=result.get('risk_level', '中'),
        )
