"""
推荐回测与自学习服务 v3.4
追踪每条推荐的后续表现，计算准确率，自动调整因子权重
"""
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Recommendation
from config import METAL_TYPES, FACTOR_WEIGHTS
import logging

logger = logging.getLogger(__name__)


class FeedbackService:
    """推荐回测 + 权重自适应"""

    def __init__(self, session_factory, price_service):
        self.session_factory = session_factory
        self.price_service = price_service

    def check_outcomes(self) -> dict:
        """检查所有未评估的推荐，回填实际涨跌结果"""
        session: Session = self.session_factory()
        try:
            unchecked = session.query(Recommendation).filter(
                Recommendation.outcome_checked == False,
                Recommendation.action.in_(["买入", "卖出", "加仓", "减仓", "止损"]),
                Recommendation.created_at < datetime.now() - timedelta(days=3),
            ).all()

            updated = 0
            for rec in unchecked:
                self._fill_outcome(session, rec)
                updated += 1

            session.commit()
            return {"success": True, "checked": updated}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    def _fill_outcome(self, session: Session, rec: Recommendation):
        """回填单条推荐的后续表现"""
        try:
            df, _ = self.price_service.get_historical_prices(rec.metal_type, days=90)
            if df is None or df.empty:
                return

            prices = df['price'].values
            rec_date = rec.created_at.replace(tzinfo=None) if rec.created_at else None
            if not rec_date:
                return

            # 找到推荐日期在K线中的位置
            dates = pd.to_datetime(df['date']).dt.tz_localize(None)
            idx = (dates >= rec_date).idxmax() if any(dates >= rec_date) else -1
            if idx < 0:
                return

            entry_price = rec.current_price
            n = len(prices)

            # 计算3/7/30日后的价格（取最近的交易日）
            for horizon, col in [(3, 'outcome_3d_pct'), (7, 'outcome_7d_pct'), (30, 'outcome_30d_pct')]:
                future_idx = min(idx + horizon, n - 1)
                if future_idx > idx:
                    future_price = float(prices[future_idx])
                    pct = (future_price - entry_price) / entry_price * 100
                    setattr(rec, col, round(pct, 2))

            # 判断方向是否正确
            if rec.outcome_7d_pct is not None:
                if rec.action in ("买入", "加仓"):
                    rec.was_correct = rec.outcome_7d_pct > 0
                elif rec.action in ("卖出", "减仓", "止损"):
                    rec.was_correct = rec.outcome_7d_pct < 0

            rec.outcome_checked = True
        except Exception as e:
            logger.debug(f"回填{rec.metal_type}#{rec.id}: {e}")

    def get_performance(self) -> dict:
        """获取历史推荐准确率统计"""
        session: Session = self.session_factory()
        try:
            checked = session.query(Recommendation).filter(
                Recommendation.outcome_checked == True
            ).all()

            if not checked:
                return {"total": 0, "accuracy": 0, "by_metal": {}, "by_action": {}}

            total = len(checked)
            correct = sum(1 for r in checked if r.was_correct)
            accuracy = correct / total * 100 if total > 0 else 0

            # 按金属统计
            by_metal = {}
            for r in checked:
                mt = r.metal_type
                if mt not in by_metal:
                    by_metal[mt] = {"total": 0, "correct": 0, "avg_profit": 0}
                by_metal[mt]["total"] += 1
                if r.was_correct:
                    by_metal[mt]["correct"] += 1
                if r.outcome_7d_pct is not None:
                    by_metal[mt]["avg_profit"] += r.outcome_7d_pct
            for mt in by_metal:
                t = by_metal[mt]["total"]
                by_metal[mt]["accuracy"] = round(by_metal[mt]["correct"] / t * 100, 1) if t else 0
                by_metal[mt]["avg_profit"] = round(by_metal[mt]["avg_profit"] / t, 2) if t else 0

            # 按操作统计
            by_action = {}
            for r in checked:
                act = r.action
                if act not in by_action:
                    by_action[act] = {"total": 0, "correct": 0}
                by_action[act]["total"] += 1
                if r.was_correct:
                    by_action[act]["correct"] += 1
            for act in by_action:
                t = by_action[act]["total"]
                by_action[act]["accuracy"] = round(by_action[act]["correct"] / t * 100, 1) if t else 0

            return {
                "total": total,
                "accuracy": round(accuracy, 1),
                "avg_profit_7d": round(np.mean([r.outcome_7d_pct for r in checked if r.outcome_7d_pct is not None]), 2) if checked else 0,
                "by_metal": by_metal,
                "by_action": by_action,
            }
        finally:
            session.close()

    def get_recent_outcomes(self, limit: int = 20) -> list[dict]:
        """获取最近的推荐结果（用于展示回测面板）"""
        session: Session = self.session_factory()
        try:
            recs = session.query(Recommendation).filter(
                Recommendation.outcome_checked == True
            ).order_by(Recommendation.created_at.desc()).limit(limit).all()

            return [{
                "id": r.id,
                "metal_type": r.metal_type,
                "action": r.action,
                "confidence": r.confidence,
                "price": r.current_price,
                "date": r.created_at.strftime("%m-%d %H:%M") if r.created_at else "",
                "outcome_3d": r.outcome_3d_pct,
                "outcome_7d": r.outcome_7d_pct,
                "outcome_30d": r.outcome_30d_pct,
                "was_correct": r.was_correct,
            } for r in recs]
        finally:
            session.close()

    def adjust_weights(self, base_weights: dict) -> dict:
        """根据历史准确率微调因子权重 (±15%范围内)"""
        session: Session = self.session_factory()
        try:
            checked = session.query(Recommendation).filter(
                Recommendation.outcome_checked == True
            ).all()

            if len(checked) < 10:
                return base_weights  # 样本不足，不调整

            w = dict(base_weights)

            # 统计各金属的准确率差异 → 推断哪些因子需要调整
            correct_recs = [r for r in checked if r.was_correct]
            wrong_recs = [r for r in checked if not r.was_correct]

            if len(wrong_recs) == 0:
                return w

            # 简单策略：如果正确率 < 50%，轻微降低所有权重重新分配到中性
            accuracy = len(correct_recs) / len(checked)
            if accuracy < 0.45:
                # 整体偏差 → 向均匀权重靠拢
                uniform_weight = 1.0 / len(w)
                blend = 0.85  # 保留85%原权重，15%均匀化
                for k in w:
                    w[k] = w[k] * blend + uniform_weight * (1 - blend)
            elif accuracy > 0.65:
                # 整体准确 → 保持当前权重
                pass

            total = sum(w.values())
            if total > 0:
                w = {k: round(v / total, 4) for k, v in w.items()}

            return w
        finally:
            session.close()


# 需要 pandas
import pandas as pd
