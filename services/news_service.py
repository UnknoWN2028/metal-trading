"""
有色金属新闻快讯服务 — 上海金属网
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsService:
    """金属新闻快讯"""

    def __init__(self):
        self._cache = {}  # {category: (timestamp, items)}

    def get_news(self, category: str = "全部", limit: int = 15,
                 max_age_hours: int = 48) -> list[dict]:
        """
        获取新闻快讯
        category: "全部" (主推，其他分类已停更)
        max_age_hours: 超过此时间(小时)的旧闻丢弃
        """
        now = datetime.now()
        cache_key = category
        cached = self._cache.get(cache_key)
        if cached:
            ts, items = cached
            if (now - ts).total_seconds() < 300:  # 5分钟缓存
                return self._filter_recent(items, max_age_hours)[:limit]

        try:
            import akshare as ak
            df = ak.futures_news_shmet(symbol=category)
            if df is None or df.empty:
                return []

            items = []
            for _, row in df.head(min(limit * 3, 200)).iterrows():
                time_str = str(row.get('发布时间', ''))
                content = str(row.get('内容', ''))
                if content:
                    items.append({
                        "time": time_str,
                        "content": content.strip(),
                        "category": category,
                    })

            self._cache[cache_key] = (now, items)
            return self._filter_recent(items, max_age_hours)[:limit]
        except Exception as e:
            logger.warning(f"新闻获取失败 [{category}]: {e}")
            if cached:
                return self._filter_recent(cached[1], max_age_hours)[:limit]
            return []

    def _filter_recent(self, items: list, max_age_hours: int) -> list:
        """过滤掉过旧的新闻"""
        if not items or max_age_hours <= 0:
            return items
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        recent = []
        for item in items:
            time_str = item.get('time', '')
            try:
                # 格式: 2026-05-23 21:23:03+08:00
                t = datetime.fromisoformat(time_str.replace('+08:00', ''))
                if t >= cutoff:
                    recent.append(item)
            except (ValueError, TypeError):
                recent.append(item)  # 解析不了的保留
        return recent

    def get_metal_news(self, metal_type: str, limit: int = 10) -> list[dict]:
        """获取某金属相关新闻（全部分类+关键词过滤）"""
        # 所有金属分类都已停更，统一从"全部"取
        items = self.get_news(category="全部", limit=limit * 2)
        # 用金属名做简单关键词过滤
        filtered = [i for i in items if metal_type in i.get('content', '')
                    or '基本金属' in i.get('content', '')
                    or '有色' in i.get('content', '')]
        if len(filtered) < 3:
            # 如果匹配太少，返回全部
            return items[:limit]
        return filtered[:limit]

    def get_all_metals_news(self, limit: int = 20) -> list[dict]:
        """获取所有有色金属相关的综合新闻"""
        return self.get_news(category="全部", limit=limit)

    def get_market_headlines(self, limit: int = 8) -> list[dict]:
        """
        获取市场要闻（用于侧边栏/仪表盘快速浏览）
        优先取"全部"分类（实时快讯），"要闻"分类数据已不更新(停滞在2026-04-30)
        """
        items = self.get_news(category="全部", limit=limit)
        if not items:
            items = self.get_news(category="要闻", limit=limit, max_age_hours=9999)
        return items
