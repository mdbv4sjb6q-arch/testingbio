# config.py - AI Trader Pro 统一配置中心
"""
Xbit Research · AI Trader Pro 金融专家系统配置
支持: 外汇(Forex)、全球股票(Stocks)、数字货币(Crypto)、大宗商品(Commodities)、指数(Indices)
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum, auto

# ==================== 系统身份 ====================
SYSTEM_IDENTITY = "Xbit Research 金融分析专家"
SYSTEM_NAME = "AI Trader Pro"
INSTITUTION = "Xbit Research Institute"
# AI 绝对不会暴露以下信息
HIDDEN_IDENTITY = ["dmind", "dmind-trading", "大模型", "语言模型", "LLM"]

# ==================== 模型配置 ====================
MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "/Users/tonychan/Documents/trae_projects/AI/core/dmind-trading-merged/dmind-trading-q4_k_m.gguf"
)
LLAMA_CPP_PATH = os.getenv(
    "LLAMA_CPP_PATH",
    "./core/llama.cpp/build/bin/llama-cli"
)
MODEL_CTX_SIZE = int(os.getenv("MODEL_CTX_SIZE", "4096"))
MODEL_GPU_LAYERS = int(os.getenv("MODEL_GPU_LAYERS", "100"))

# ==================== 资产类别 ====================
class AssetClass(Enum):
    FOREX = auto()
    CRYPTO = auto()
    STOCK = auto()
    COMMODITY = auto()
    INDEX = auto()
    FUTURES = auto()
    BOND = auto()
    ETF = auto()

class MarketRegion(Enum):
    US = "US"
    CA = "CA"
    BR = "BR"
    UK = "UK"
    DE = "DE"
    FR = "FR"
    EU = "EU"
    CN = "CN"
    HK = "HK"
    JP = "JP"
    AU = "AU"
    SG = "SG"
    IN = "IN"
    KR = "KR"
    TW = "TW"
    GLOBAL = "GLOBAL"
    OTC = "OTC"

# ==================== API 配置 ====================
@dataclass
class APIConfig:
    name: str
    base_url: str
    api_key: Optional[str]
    rate_limit_per_min: int
    supports: Set[AssetClass]
    supports_regions: Set[MarketRegion]
    websocket_available: bool = False
    historical_years: int = 1
    realtime_delay_seconds: int = 0

ITICK_API_KEY = "8d22eda64b384378be66728c215e178dcbede04b46a14a22a6e659e5f4ba4d0e"

API_CONFIGS = {
    "itick": APIConfig(
        name="iTick",
        base_url="https://api.itick.org",
        api_key=ITICK_API_KEY,
        rate_limit_per_min=10,
        supports={AssetClass.STOCK, AssetClass.FOREX, AssetClass.CRYPTO, AssetClass.INDEX, AssetClass.COMMODITY},
        supports_regions={
            MarketRegion.US, MarketRegion.HK, MarketRegion.CN,
            MarketRegion.JP, MarketRegion.UK, MarketRegion.EU,
            MarketRegion.GLOBAL
        },
        websocket_available=True,
        historical_years=1,
        realtime_delay_seconds=0
    ),
    "ccxt": APIConfig(
        name="CCXT",
        base_url="",
        api_key=None,
        rate_limit_per_min=1200,
        supports={AssetClass.CRYPTO},
        supports_regions={MarketRegion.GLOBAL},
        websocket_available=True,
        historical_years=7,
        realtime_delay_seconds=0
    ),
    "yfinance": APIConfig(
        name="Yahoo Finance",
        base_url="",
        api_key=None,
        rate_limit_per_min=100,
        supports={AssetClass.STOCK, AssetClass.ETF, AssetClass.FOREX, AssetClass.CRYPTO, AssetClass.COMMODITY, AssetClass.INDEX},
        supports_regions={MarketRegion.GLOBAL},
        websocket_available=False,
        historical_years=20,
        realtime_delay_seconds=900
    )
}

# ==================== API 密钥 ====================
API_KEYS = {
    "alpha_vantage": os.getenv("ALPHA_VANTAGE_KEY", ""),
    "coingecko": os.getenv("COINGECKO_KEY", ""),
    "fred": os.getenv("FRED_KEY", ""),
    "finnhub": os.getenv("FINNHUB_KEY", ""),
    "polygon": os.getenv("POLYGON_KEY", ""),
    "polymarket": os.getenv("POLYMARKET_KEY", ""),
    "coinmarketcap": os.getenv("COINMARKETCAP_KEY", ""),
}

# ==================== Agent 权重 ====================
AGENT_WEIGHTS = {
    "LeviathanAgent": 1.0,
    "MacroEconomistAgent": 0.15,
    "TechnicalAnalystAgent": 0.25,
    "FundamentalAgent": 0.20,
    "CryptoAnalystAgent": 0.15,
    "RiskManagerAgent": 0.10,
    "SentimentAgent": 0.10,
    "EventDrivenAgent": 0.05,
}

LEVIATHAN_OVERRIDE_THRESHOLD = 0.7

# ==================== 时间周期映射 ====================
TIMEFRAMES = {
    "1m": {"seconds": 60, "itick": 1, "ccxt": "1m", "yfinance": "1m", "display": "1分钟"},
    "5m": {"seconds": 300, "itick": 2, "ccxt": "5m", "yfinance": "5m", "display": "5分钟"},
    "15m": {"seconds": 900, "itick": 3, "ccxt": "15m", "yfinance": "15m", "display": "15分钟"},
    "30m": {"seconds": 1800, "itick": 4, "ccxt": "30m", "yfinance": "30m", "display": "30分钟"},
    "1h": {"seconds": 3600, "itick": 5, "ccxt": "1h", "yfinance": "1h", "display": "1小时"},
    "2h": {"seconds": 7200, "itick": 6, "ccxt": "2h", "yfinance": "1h", "display": "2小时"},
    "4h": {"seconds": 14400, "itick": 7, "ccxt": "4h", "yfinance": "1h", "display": "4小时"},
    "1d": {"seconds": 86400, "itick": 8, "ccxt": "1d", "yfinance": "1d", "display": "日线"},
    "1w": {"seconds": 604800, "itick": 9, "ccxt": "1w", "yfinance": "1wk", "display": "周线"},
    "1M": {"seconds": 2592000, "itick": 10, "ccxt": "1M", "yfinance": "1mo", "display": "月线"},
}

# ==================== 缓存配置 ====================
CACHE_CONFIG = {
    "dir": "./market_data_cache",
    "max_age_hours": 24,
    "format": "parquet"
}

# ==================== TypeScript K线桥接 ====================
TYPESCRIPT_BRIDGE_URL = os.getenv("TS_BRIDGE_URL", "ws://localhost:8080/kline")
TYPESCRIPT_INDICATORS_PATH = os.getenv("TS_INDICATORS_PATH", "./indicators")

# ==================== 服务器配置 ====================
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "9000"))

# ==================== 禁用短语 (AI不会说这些) ====================
BANNED_PHRASES = [
    "作为AI", "我是AI", "我是人工智能", "我是模型",
    "我没有", "我不能", "我无法", "我不知道",
    "仅供参考", "不构成建议", "请咨询专业人士",
    "dmind", "大语言模型", "语言模型",
]