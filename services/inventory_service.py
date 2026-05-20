"""
库存管理服务
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from database import Inventory, Transaction
from config import METAL_TYPES
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """库存管理服务"""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_all_inventory(self) -> list[dict]:
        """获取所有库存"""
        session: Session = self.session_factory()
        try:
            items = session.query(Inventory).filter(Inventory.status == "持有").all()
            return [self._to_dict(item) for item in items]
        finally:
            session.close()

    def get_inventory_by_metal(self, metal_type: str) -> list[dict]:
        """按金属类型获取库存"""
        session: Session = self.session_factory()
        try:
            items = session.query(Inventory).filter(
                Inventory.metal_type == metal_type,
                Inventory.status == "持有"
            ).all()
            return [self._to_dict(item) for item in items]
        finally:
            session.close()

    def add_inventory(self, metal_type: str, quantity_kg: float,
                      cost_price_per_kg: float, storage_location: str = "主仓库",
                      quality_grade: str = "一级", notes: str = "") -> dict:
        """新增库存（买入入库）"""
        if quantity_kg <= 0:
            return {"success": False, "message": "数量必须大于0"}
        if cost_price_per_kg <= 0:
            return {"success": False, "message": "单价必须大于0"}
        if metal_type not in METAL_TYPES:
            return {"success": False, "message": f"不支持的金属类型: {metal_type}"}

        session: Session = self.session_factory()
        try:
            symbol = METAL_TYPES.get(metal_type, {}).get("symbol", metal_type)
            total_cost = quantity_kg * cost_price_per_kg

            item = Inventory(
                metal_type=metal_type,
                metal_symbol=symbol,
                quantity_kg=quantity_kg,
                avg_cost_price=cost_price_per_kg,
                total_cost=total_cost,
                current_value=total_cost,
                storage_location=storage_location,
                quality_grade=quality_grade,
                status="持有",
                purchase_date=datetime.now(),
                notes=notes,
            )
            session.add(item)

            # 记录交易
            txn = Transaction(
                transaction_type="买入",
                metal_type=metal_type,
                metal_symbol=symbol,
                quantity_kg=quantity_kg,
                price_per_kg=cost_price_per_kg,
                total_amount=total_cost,
                notes=notes,
                transaction_date=datetime.now(),
            )
            session.add(txn)

            session.commit()
            return {"success": True, "id": item.id, "message": f"✅ 成功入库 {metal_type} {quantity_kg}kg"}
        except Exception as e:
            session.rollback()
            logger.error(f"入库失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    def sell_inventory(self, inventory_id: int, quantity_kg: float,
                       sell_price_per_kg: float, counterparty: str = "",
                       notes: str = "") -> dict:
        """卖出库存"""
        import math
        session: Session = self.session_factory()
        try:
            item = session.query(Inventory).filter(Inventory.id == inventory_id).first()
            if not item:
                return {"success": False, "message": "库存记录不存在"}
            if item.status == "已售出":
                return {"success": False, "message": "该库存已售出"}
            if quantity_kg <= 0:
                return {"success": False, "message": "卖出数量必须大于0"}
            if sell_price_per_kg <= 0:
                return {"success": False, "message": "卖出单价必须大于0"}
            if quantity_kg > item.quantity_kg:
                return {"success": False, "message": f"库存不足，当前仅有 {item.quantity_kg}kg"}

            profit = (sell_price_per_kg - item.avg_cost_price) * quantity_kg
            profit_pct = (sell_price_per_kg - item.avg_cost_price) / item.avg_cost_price * 100

            # 用 math.isclose 避免浮点精度问题
            is_full_sale = math.isclose(quantity_kg, item.quantity_kg, rel_tol=1e-9)

            if is_full_sale:
                item.status = "已售出"
            else:
                # 部分卖出：扣减数量，保留成本总额不变
                item.quantity_kg -= quantity_kg
                # total_cost 保持原始总成本不变（已售部分的成本通过交易记录追踪）

            # 记录交易
            txn = Transaction(
                transaction_type="卖出",
                metal_type=item.metal_type,
                metal_symbol=item.metal_symbol,
                quantity_kg=quantity_kg,
                price_per_kg=sell_price_per_kg,
                total_amount=quantity_kg * sell_price_per_kg,
                counterparty=counterparty,
                profit=profit,
                profit_pct=profit_pct,
                notes=notes,
                transaction_date=datetime.now(),
            )
            session.add(txn)
            session.commit()

            return {
                "success": True,
                "message": f"✅ 成功卖出 {item.metal_type} {quantity_kg}kg",
                "profit": round(profit, 2),
                "profit_pct": round(profit_pct, 2),
            }
        except Exception as e:
            session.rollback()
            logger.error(f"卖出失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    def update_market_values(self, prices: dict):
        """根据当前市场价格更新库存市值"""
        session: Session = self.session_factory()
        try:
            items = session.query(Inventory).filter(Inventory.status == "持有").all()
            for item in items:
                current_price = prices.get(item.metal_type, item.avg_cost_price)
                item.current_market_price = current_price
                item.current_value = item.quantity_kg * current_price
                item.profit_loss = item.current_value - item.total_cost
                item.profit_loss_pct = (item.profit_loss / item.total_cost * 100) if item.total_cost > 0 else 0
                item.last_updated = datetime.now()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"更新市值失败: {e}")
        finally:
            session.close()

    def get_inventory_summary(self) -> dict:
        """获取库存汇总"""
        session: Session = self.session_factory()
        try:
            items = session.query(Inventory).filter(Inventory.status == "持有").all()

            if not items:
                return {
                    "total_items": 0,
                    "total_cost": 0,
                    "total_value": 0,
                    "total_profit": 0,
                    "profit_pct": 0,
                    "by_metal": {},
                }

            total_cost = sum(item.total_cost for item in items)
            total_value = sum(item.current_value for item in items)
            total_profit = total_value - total_cost

            by_metal = {}
            for item in items:
                if item.metal_type not in by_metal:
                    by_metal[item.metal_type] = {
                        "quantity_kg": 0, "total_cost": 0,
                        "total_value": 0, "profit_loss": 0,
                    }
                by_metal[item.metal_type]["quantity_kg"] += item.quantity_kg
                by_metal[item.metal_type]["total_cost"] += item.total_cost
                by_metal[item.metal_type]["total_value"] += item.current_value
                by_metal[item.metal_type]["profit_loss"] += item.profit_loss

            return {
                "total_items": len(items),
                "total_cost": round(total_cost, 2),
                "total_value": round(total_value, 2),
                "total_profit": round(total_profit, 2),
                "profit_pct": round(total_profit / total_cost * 100, 2) if total_cost > 0 else 0,
                "by_metal": by_metal,
            }
        finally:
            session.close()

    def get_transaction_history(self, limit: int = 50) -> list[dict]:
        """获取交易历史"""
        session: Session = self.session_factory()
        try:
            txns = session.query(Transaction).order_by(
                Transaction.transaction_date.desc()
            ).limit(limit).all()
            return [{
                "id": t.id,
                "type": t.transaction_type,
                "metal": t.metal_type,
                "quantity_kg": t.quantity_kg,
                "price_per_kg": t.price_per_kg,
                "total": t.total_amount,
                "profit": t.profit,
                "profit_pct": t.profit_pct,
                "counterparty": t.counterparty,
                "date": t.transaction_date.isoformat(),
                "notes": t.notes,
            } for t in txns]
        finally:
            session.close()

    def get_profit_summary(self, days: int = 30) -> dict:
        """获取利润汇总"""
        session: Session = self.session_factory()
        try:
            from datetime import timedelta
            since = datetime.now() - timedelta(days=days)

            txns = session.query(Transaction).filter(
                Transaction.transaction_type == "卖出",
                Transaction.transaction_date >= since,
            ).all()

            total_profit = sum(t.profit for t in txns if t.profit)
            total_revenue = sum(t.total_amount for t in txns)
            avg_margin = sum(t.profit_pct for t in txns if t.profit_pct) / len(txns) if txns else 0

            return {
                "period_days": days,
                "total_sell_transactions": len(txns),
                "total_revenue": round(total_revenue, 2),
                "total_profit": round(total_profit, 2),
                "avg_profit_margin": round(avg_margin, 2),
            }
        finally:
            session.close()

    @staticmethod
    def _to_dict(item: Inventory) -> dict:
        return {
            "id": item.id,
            "metal_type": item.metal_type,
            "metal_symbol": item.metal_symbol,
            "quantity_kg": item.quantity_kg,
            "avg_cost_price": item.avg_cost_price,
            "current_market_price": item.current_market_price,
            "total_cost": item.total_cost,
            "current_value": item.current_value,
            "profit_loss": item.profit_loss,
            "profit_loss_pct": item.profit_loss_pct,
            "storage_location": item.storage_location,
            "quality_grade": item.quality_grade,
            "status": item.status,
            "purchase_date": item.purchase_date.isoformat() if item.purchase_date else "",
            "last_updated": item.last_updated.isoformat() if item.last_updated else "",
            "notes": item.notes,
        }
