"""
DeepSeek LLM 分析服务
为金属交易提供专业AI分析，与量化评分互补
"""
import json
import logging
from datetime import datetime
from config import LLM_CONFIG

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深有色金属回收贸易分析师，拥有20年行业经验。
你的客户是废旧金属回收倒卖公司——低价收购废旧金属，高价卖出赚取差价。

你需要基于提供的市场数据和多维度分析，给出专业、实用的交易建议。请严格遵循以下规则：

1. 分析当前市场态势（多头/空头/震荡），考虑宏观环境
2. 结合技术指标 + 季节性规律 + 跨品种联动判断买卖时机
3. 考虑库存成本、资金占用、仓储费用等运营因素
4. 评估组合集中度风险，给出仓位管理建议
5. 关注供需基本面（新能源需求、房地产、基建等产业链影响）
6. 明确指出政策风险、地缘风险和其他不确定性
7. 给出具体的操作建议（买入/卖出/持有）及置信度理由

回复格式要求：
- 用中文回复，简洁专业
- 第一行给出明确结论（买入/卖出/持有）
- 分【市场环境】【技术面】【基本面】【风险提示】四大块说明
- 每个板块2-3句话即可
- 最后给出操作建议置信度（高/中/低）"""


class LLMService:
    """DeepSeek LLM 分析引擎"""

    def __init__(self):
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        """初始化 DeepSeek 客户端"""
        api_key = LLM_CONFIG.get("api_key", "")
        if not api_key:
            logger.info("LLM未配置API Key，使用纯量化分析")
            return
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=api_key,
                base_url=LLM_CONFIG.get("base_url", "https://api.deepseek.com"),
            )
            self._available = True
            logger.info(f"DeepSeek LLM已连接 (model={LLM_CONFIG['model']})")
        except Exception as e:
            logger.warning(f"LLM初始化失败: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def analyze(self, metal_type: str, indicators: dict, inventory: dict,
                quant_result: dict) -> dict:
        """
        LLM综合分析

        Args:
            metal_type: 金属名称
            indicators: 技术指标字典
            inventory: 库存信息
            quant_result: 量化评分结果
        Returns:
            {"analysis": str, "recommendation": str, "confidence": float, "risks": str}
        """
        if not self._available:
            return {
                "analysis": "",
                "recommendation": "",
                "confidence": 0,
                "risks": "",
                "llm_available": False,
            }

        prompt = self._build_prompt(metal_type, indicators, inventory, quant_result)

        try:
            response = self._client.chat.completions.create(
                model=LLM_CONFIG.get("model", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=LLM_CONFIG.get("max_tokens", 1024),
                temperature=LLM_CONFIG.get("temperature", 0.3),
                timeout=15,  # 15秒超时
            )
            text = response.choices[0].message.content.strip()
            return self._parse_response(text)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return {
                "analysis": f"LLM调用失败: {str(e)[:100]}",
                "recommendation": "",
                "confidence": 0,
                "risks": "",
                "llm_available": False,
            }

    def _build_prompt(self, metal: str, ind: dict, inv: dict,
                      quant: dict) -> str:
        """构建分析提示词（防御性格式化）"""
        unit = "元/克" if metal in ("黄金",) else "元/千克" if metal == "白银" else "元/吨"

        def _f(key, fmt=".0f"):
            v = ind.get(key)
            if v is None:
                return "N/A"
            try:
                return format(float(v), fmt)
            except (ValueError, TypeError):
                return str(v)

        def _qf(d, key, default=50.0):
            """安全获取量化分数"""
            v = d.get(key, default)
            if v is None:
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        lines = [f"## {metal} 市场数据 ({unit})", ""]
        lines.append(f"**当前价格**: {_f('current')}")
        lines.append(f"**数据来源**: {'SHFE实时' if quant.get('confidence') else '模拟'}")
        lines.append(f"\n### 📊 技术面")
        lines.append(f"**均线**: MA7={_f('ma7')}, MA20={_f('ma20')}, MA30={_f('ma30')}")
        lines.append(f"**趋势斜率**: {ind.get('trend_slope', 0)}")
        lines.append(f"**RSI(14)**: {_f('rsi', '.1f')}")
        lines.append(f"**MACD**: {_f('macd', '.2f')} (信号: {_f('macd_signal', '.2f')})")
        lines.append(f"**ADX**: {_f('adx', '.1f')}")
        lines.append(f"**ATR**: {_f('atr')} ({float(ind.get('atr_pct', 0) or 0)*100:.1f}%)")
        lines.append(f"**30日波动率**: {float(ind.get('volatility_30d', 0))*100:.1f}%")
        lines.append(f"**布林带**: 上{_f('bb_upper')} / 中{_f('bb_mid')} / 下{_f('bb_lower')}")
        lines.append(f"**支撑/阻力**: ¥{_f('support')} / ¥{_f('resistance')}")

        # 🆕 多因子评分明细
        composite = quant.get('composite_score', 0)
        if isinstance(composite, (int, float)):
            lines.append(f"\n### 🎯 量化因子评分 (综合: {composite:.0f}/100)")
            lines.append(f"趋势:{quant.get('trend_score', 0):.0f} "
                        f"动量:{quant.get('momentum_score', 0):.0f} "
                        f"波动:{quant.get('volatility_score', 0):.0f} "
                        f"支撑:{quant.get('sr_score', 0):.0f}")
            lines.append(f"量价:{_qf(quant, 'volume_score'):.0f} "
                        f"状态:{_qf(quant, 'regime_score'):.0f} "
                        f"季节性:{_qf(quant, 'seasonal_score'):.0f} "
                        f"联动:{_qf(quant, 'correlation_score'):.0f}")
            lines.append(f"周期对齐:{_qf(quant, 'timeframe_score'):.0f} "
                        f"供需:{_qf(quant, 'supply_demand_score'):.0f} "
                        f"宏观:{_qf(quant, 'macro_score'):.0f}")
            lines.append(f"运营:{_qf(quant, 'operational_score'):.0f} "
                        f"风控:{_qf(quant, 'risk_score'):.0f}")

        if inv:
            lines.append(f"\n### 📦 库存与运营")
            lines.append(f"**库存**: {inv.get('total_kg', 0):.0f}kg, 成本¥{inv.get('avg_cost', 0):.0f}, 浮动盈亏{inv.get('profit_pct', 0):+.1f}%")
        else:
            lines.append("\n### 📦 库存: 无持仓")

        lines.append(f"\n**量化建议**: {quant.get('action', '持有')} (信心{float(quant.get('confidence', 0))*100:.0f}%)")
        lines.append(f"**止损**: ¥{_f('stop_loss')} | **止盈**: ¥{_f('take_profit')}")

        return "\n".join(lines)

    @staticmethod
    def _parse_response(text: str) -> dict:
        """解析 LLM 回复（支持 v3 多维度分析格式）"""
        lines = text.strip().split("\n")
        first_line = lines[0] if lines else ""

        # 判断建议方向
        recommendation = ""
        if "买入" in first_line[:15] or "做多" in first_line[:10]:
            recommendation = "买入"
        elif "卖出" in first_line[:15] or "做空" in first_line[:10]:
            recommendation = "卖出"
        elif "持有" in first_line[:15] or "观望" in first_line[:10] or "等待" in first_line[:10]:
            recommendation = "持有"

        # 提取风险提示
        risks = ""
        risk_section = False
        for line in lines:
            if "风险提示" in line or "⚠" in line:
                risk_section = True
            if risk_section and line.strip():
                risks += line.strip() + "\n"
            if "风险" in line or "注意" in line or "谨慎" in line or "警惕" in line:
                if not risk_section:
                    risks += line.strip() + "\n"

        # 提取置信度
        confidence = 0.7
        for line in lines:
            if "置信度" in line:
                if "高" in line:
                    confidence = 0.85
                elif "中" in line:
                    confidence = 0.65
                elif "低" in line:
                    confidence = 0.45
                break

        return {
            "analysis": text,
            "recommendation": recommendation or "持有",
            "confidence": confidence,
            "risks": risks.strip(),
            "llm_available": True,
        }
