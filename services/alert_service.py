"""
价格预警与通知服务
"""
from datetime import datetime
from sqlalchemy.orm import Session
from database import PriceAlert
from config import NOTIFICATION
import logging
import requests

logger = logging.getLogger(__name__)


class AlertService:
    """价格预警服务"""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create_alert(self, metal_type: str, alert_type: str,
                     trigger_price: float, message: str = "") -> dict:
        """创建价格预警"""
        if alert_type not in ("高于", "低于"):
            return {"success": False, "message": "预警类型必须是 '高于' 或 '低于'"}

        session: Session = self.session_factory()
        try:
            alert = PriceAlert(
                metal_type=metal_type,
                alert_type=alert_type,
                trigger_price=trigger_price,
                message=message,
            )
            session.add(alert)
            session.commit()
            return {
                "success": True,
                "id": alert.id,
                "message": f"✅ 已创建预警：{metal_type} {alert_type} ¥{trigger_price}"
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    def get_active_alerts(self) -> list[dict]:
        """获取活跃的预警"""
        session: Session = self.session_factory()
        try:
            alerts = session.query(PriceAlert).filter(
                PriceAlert.is_triggered == False
            ).all()
            return [self._to_dict(a) for a in alerts]
        finally:
            session.close()

    def check_alerts(self, current_prices: dict) -> list[dict]:
        """检查所有预警是否触发"""
        session: Session = self.session_factory()
        triggered = []
        try:
            active_alerts = session.query(PriceAlert).filter(
                PriceAlert.is_triggered == False
            ).all()

            for alert in active_alerts:
                current_price = current_prices.get(alert.metal_type)
                if current_price is None:
                    continue

                alert.current_price = current_price
                should_trigger = False

                if alert.alert_type == "高于" and current_price >= alert.trigger_price:
                    should_trigger = True
                elif alert.alert_type == "低于" and current_price <= alert.trigger_price:
                    should_trigger = True

                if should_trigger:
                    alert.is_triggered = True
                    alert.triggered_at = datetime.now()
                    triggered.append(self._to_dict(alert))

            session.commit()
            return triggered
        except Exception as e:
            session.rollback()
            logger.error(f"检查预警失败: {e}")
            return []
        finally:
            session.close()

    def delete_alert(self, alert_id: int) -> dict:
        """删除预警"""
        session: Session = self.session_factory()
        try:
            alert = session.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
            if alert:
                session.delete(alert)
                session.commit()
                return {"success": True, "message": "已删除预警"}
            return {"success": False, "message": "预警不存在"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def _to_dict(alert: PriceAlert) -> dict:
        return {
            "id": alert.id,
            "metal_type": alert.metal_type,
            "alert_type": alert.alert_type,
            "trigger_price": alert.trigger_price,
            "current_price": alert.current_price,
            "is_triggered": alert.is_triggered,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            "message": alert.message,
            "created_at": alert.created_at.isoformat(),
        }


class NotificationService:
    """消息推送服务（支持钉钉/企业微信/飞书 Webhook）"""

    @staticmethod
    def send_notification(title: str, content: str, msg_type: str = "text") -> bool:
        """发送通知到配置的渠道"""
        if not NOTIFICATION.get("enabled"):
            return False

        webhook_url = NOTIFICATION.get("webhook_url")
        if not webhook_url:
            return False

        import requests

        try:
            if NOTIFICATION["type"] == "dingtalk":
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": title,
                        "text": f"## {title}\n\n{content}\n\n---\n> 有色金属回收AI系统"
                    }
                }
            elif NOTIFICATION["type"] == "wecom":
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"## {title}\n{content}"
                    }
                }
            else:
                payload = {
                    "msg_type": "interactive",
                    "card": {
                        "header": {"title": {"content": title, "tag": "plain_text"}},
                        "elements": [{"tag": "div", "text": {"content": content, "tag": "lark_md"}}]
                    }
                }

            resp = requests.post(webhook_url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False

    @classmethod
    def notify_price_alert(cls, metal_type: str, alert_type: str,
                           trigger_price: float, current_price: float):
        """发送价格预警通知"""
        title = f"🚨 价格预警触发 - {metal_type}"
        content = (
            f"**金属类型**: {metal_type}\n"
            f"**预警条件**: {alert_type} ¥{trigger_price}\n"
            f"**当前价格**: ¥{current_price}\n"
            f"**触发时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        return cls.send_notification(title, content)

    @classmethod
    def notify_recommendation(cls, metal_type: str, action: str,
                              confidence: float, reason: str):
        """发送AI推荐通知"""
        emoji = "📈" if action == "买入" else ("📉" if action == "卖出" else "⏸️")
        title = f"{emoji} AI交易推荐 - {metal_type} {action}"
        content = (
            f"**推荐操作**: {action}\n"
            f"**信心指数**: {confidence:.0%}\n"
            f"**分析理由**: {reason}\n"
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        return cls.send_notification(title, content)

    @classmethod
    def notify_daily_summary(cls, summary: str):
        """发送每日汇总"""
        title = "📊 每日金属行情汇总"
        return cls.send_notification(title, summary)
