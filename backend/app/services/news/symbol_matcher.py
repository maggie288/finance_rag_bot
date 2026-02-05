"""智能股票关联识别模块 - 使用NLP技术提取新闻中的股票代码"""
from __future__ import annotations

import re
import logging
from typing import List, Set, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SymbolMatch:
    """股票匹配结果"""
    symbol: str
    confidence: float  # 0.0-1.0
    matched_by: str  # 匹配方式


class SmartSymbolMatcher:
    """智能股票代码匹配器"""

    # 公司名称到股票代码映射
    COMPANY_MAPPINGS = {
        # 美股科技股
        "apple": ("AAPL", 1.0), "iphone": ("AAPL", 0.8), "tim cook": ("AAPL", 0.9),
        "tesla": ("TSLA", 1.0), "elon musk": ("TSLA", 0.9), "model 3": ("TSLA", 0.9),
        "nvidia": ("NVDA", 1.0), "jensen huang": ("NVDA", 0.9), "geforce": ("NVDA", 0.8),
        "microsoft": ("MSFT", 1.0), "azure": ("MSFT", 0.8), "satya nadella": ("MSFT", 0.9),
        "google": ("GOOGL", 1.0), "alphabet": ("GOOGL", 1.0), "android": ("GOOGL", 0.7),
        "amazon": ("AMZN", 1.0), "aws": ("AMZN", 0.8), "andy jassy": ("AMZN", 0.9),
        "meta": ("META", 1.0), "facebook": ("META", 1.0), "mark zuckerberg": ("META", 0.9),
        "amd": ("AMD", 1.0), "ryzen": ("AMD", 0.9), "intel": ("INTC", 1.0),
        "netflix": ("NFLX", 1.0),
        # 港股
        "tencent": ("0700.HK", 1.0), "腾讯": ("0700.HK", 1.0), "wechat": ("0700.HK", 0.8),
        "alibaba": ("9988.HK", 1.0), "阿里巴巴": ("9988.HK", 1.0), "淘宝": ("9988.HK", 0.8),
        "xiaomi": ("1810.HK", 1.0), "小米": ("1810.HK", 1.0), "雷军": ("1810.HK", 0.9),
        # A股
        "moutai": ("600519.SH", 1.0), "茅台": ("600519.SH", 1.0), "贵州茅台": ("600519.SH", 1.0),
        "wuliangye": ("000858.SZ", 1.0), "五粮液": ("000858.SZ", 1.0),
        "byd": ("002594.SZ", 1.0), "比亚迪": ("002594.SZ", 1.0),
        "catl": ("300750.SZ", 1.0), "宁德时代": ("300750.SZ", 1.0),
    }

    KNOWN_SYMBOLS = {
        "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "INTC", "NFLX",
        "0700.HK", "9988.HK", "1810.HK", "600519.SH", "000858.SZ", "002594.SZ", "300750.SZ",
    }

    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold
        self._build_reverse_index()

    def _build_reverse_index(self):
        self.keyword_to_symbols: Dict[str, List[tuple]] = {}
        for keyword, (symbol, confidence) in self.COMPANY_MAPPINGS.items():
            if keyword not in self.keyword_to_symbols:
                self.keyword_to_symbols[keyword] = []
            self.keyword_to_symbols[keyword].append((symbol, confidence))

    def extract_symbols(self, title: str, content: Optional[str] = None, target_symbol: Optional[str] = None) -> List[SymbolMatch]:
        """从标题和内容中提取股票代码"""
        matches: Dict[str, SymbolMatch] = {}
        text = f"{title} {content or ''}"
        text_lower = text.lower()

        # 直接匹配股票代码
        for symbol in self.KNOWN_SYMBOLS:
            if symbol in text.upper():
                matches[symbol] = SymbolMatch(symbol=symbol, confidence=1.0, matched_by="direct")

        # 通过关键词匹配
        for keyword, symbol_list in self.keyword_to_symbols.items():
            if keyword in text_lower:
                for symbol, conf in symbol_list:
                    if symbol not in matches or matches[symbol].confidence < conf:
                        matches[symbol] = SymbolMatch(symbol=symbol, confidence=conf, matched_by=f"keyword:{keyword}")

        if target_symbol:
            return [matches[target_symbol.upper()]] if target_symbol.upper() in matches else []

        return [m for m in matches.values() if m.confidence >= self.confidence_threshold]

    def add_custom_mapping(self, keyword: str, symbol: str, confidence: float = 0.8):
        """添加自定义映射"""
        keyword_lower = keyword.lower()
        if keyword_lower not in self.keyword_to_symbols:
            self.keyword_to_symbols[keyword_lower] = []
        self.keyword_to_symbols[keyword_lower].append((symbol, confidence))
        self.KNOWN_SYMBOLS.add(symbol)
