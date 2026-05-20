"""
有色金属新闻快讯服务 — 上海金属网
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 金属 → 新闻分类映射
METAL_NEWS_MAP = {
    "铜": "铜", "铝": "铝", "锌": "锌", "铅": "铅",
    "镍": "镍", "锡": "锡",
    "黄金": "贵金属", "白银": "贵金属",
    "废铜": "铜", "废铝": "铝", "废不锈钢": "镍",
}


class NewsService:
    """金属新闻快讯"""

    def __init__(self):
        self._cache = {}  # {category: (timestamp, items)}

    def get_news(self, category: str = "全部", limit: int = 15) -> list[dict]:
        """
        获取新闻快讯
        category: "全部" | "铜" | "铝" | "锌" | "铅" | "镍" | "锡" | "贵金属"
        """
        now = datetime.now()
        cached = self._cache.get(category)
        if cached:
            ts, items = cached
            if (now - ts).total_seconds() < 300:  # 5分钟缓存
                return items[:limit]

        try:
            import akshare as ak
            df = ak.futures_news_shmet(symbol=category)
            if df is None or df.empty:
                return []

            items = []
            for _, row in df.head(limit).iterrows():
                time_str = str(row.get('发布时间', ''))
                content = str(row.get('内容', ''))
                if content:
                    items.append({
                        "time": time_str,
                        "content": content.strip(),
                        "category": category,
                    })

            self._cache[category] = (now, items)
            return items
        except Exception as e:
            logger.warning(f"新闻获取失败 [{category}]: {e}")
            # 返回缓存的旧数据
            if cached:
                return cached[1][:limit]
            return []

    def get_metal_news(self, metal_type: str, limit: int = 10) -> list[dict]:
        """获取某金属相关新闻（含贵金属通用新闻）"""
        category = METAL_NEWS_MAP.get(metal_type, "全部")
        return self.get_news(category=category, limit=limit)

    def get_all_metals_news(self, limit: int = 20) -> list[dict]:
        """获取所有有色金属相关的综合新闻"""
        return self.get_news(category="全部", limit=limit)

    def get_market_headlines(self, limit: int = 8) -> list[dict]:
        """
        获取市场要闻（用于侧边栏/仪表盘快速浏览）
        优先取"要闻"分类
        """
        items = self.get_news(category="要闻", limit=limit)
        if not items:
            items = self.get_news(category="全部", limit=limit)
        return items
