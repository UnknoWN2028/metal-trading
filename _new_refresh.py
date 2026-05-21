    def refresh_spot_only(self) -> dict:
        """v3.2.2 新浪HTTP即时行情 — fields[3]=当前价 fields[2]=昨结算"""
        from config import METAL_TYPES
        import urllib.request
        import re

        try:
            symbols = []
            metal_by_code = {}
            for metal, cfg in METAL_TYPES.items():
                code = cfg.get('futures_code', '')
                if code and not cfg.get('is_scrap'):
                    symbols.append(code)
                    metal_by_code[code.upper()] = metal

            if not symbols:
                return {"success": False, "message": "无可用合约"}

            url = "http://hq.sinajs.cn/list=" + ",".join(symbols)
            req = urllib.request.Request(url)
            req.add_header("Referer", "https://finance.sina.com.cn")
            resp = urllib.request.urlopen(req, timeout=6)
            raw_text = resp.read().decode("gbk")

            if not raw_text or "hq_str_" not in raw_text:
                return {"success": False, "message": "新浪无数据"}

            updated = 0
            ts_now = datetime.now()
            for line in raw_text.strip().split("\n"):
                m = re.match(r"var hq_str_(\w+)=\"(.+)\"", line)
                if not m:
                    continue
                sym = m.group(1).upper()
                fields = m.group(2).split(",")
                metal = metal_by_code.get(sym)
                if not metal:
                    base = re.sub(r'\d+$', '', sym)
                    for c, mn in metal_by_code.items():
                        if re.sub(r'\d+$', '', c) == base:
                            metal = mn
                            break
                if not metal or len(fields) < 6:
                    continue
                try:
                    price = float(fields[3])
                    prev = float(fields[2])
                    high = float(fields[4]) if len(fields) > 4 and fields[4] else price * 1.005
                    low = float(fields[5]) if len(fields) > 5 and fields[5] else price * 0.995
                    if price <= 0:
                        continue
                    if high <= 0:
                        high = price * 1.005
                    if low <= 0:
                        low = price * 0.995
                    chg = (price - prev) / prev * 100 if prev > 0 else 0
                    if abs(chg) > 20:
                        chg = 0
                    self._real_prices[metal] = {
                        "price": price, "change_pct": round(chg, 2),
                        "high": high, "low": low,
                        "volume": 0, "timestamp": ts_now,
                    }
                    updated += 1
                except (ValueError, IndexError):
                    continue

            for metal, cfg in METAL_TYPES.items():
                ref = cfg.get('ref_metal')
                if cfg.get("is_scrap") and ref and ref in self._real_prices:
                    rp = self._real_prices[ref]
                    ratio = cfg.get("ratio", 0.6)
                    self._real_prices[metal] = {
                        "price": rp["price"] * ratio,
                        "change_pct": rp["change_pct"],
                        "high": rp["high"] * ratio,
                        "low": rp["low"] * ratio,
                        "volume": 0, "timestamp": rp["timestamp"],
                    }
                    updated += 1

            if updated > 0:
                self._last_update = ts_now
                self._use_real = True
                self._history_cache.clear()
                return {"success": True, "message": f"OK {updated}品种",
                        "updated": updated}
            return {"success": False, "message": "无匹配"}

        except Exception as e:
            logger.warning(f"refresh_spot_only: {e}")
            return {"success": False, "message": str(e)[:80]}
