# itick_provider.py - iTick 市场数据提供者
"""
iTick API 市场数据提供者
支持全球市场（外汇、美股、港股、指数、商品、加密货币）
API文档: https://docs.itick.org/en
"""

import requests
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from base_provider import BaseProvider, OHLCV
from config import ITICK_API_KEY

logger = logging.getLogger(__name__)

KTYPE_MAP = {
    '1m': 1, '5m': 2, '15m': 3, '30m': 4,
    '1h': 5, '2h': 6, '4h': 7,
    '1d': 8, '1w': 9, '1M': 10,
}

SYMBOL_REGION_MAP = {
    'AAPL': ('US', 'AAPL', 'stock'),
    'MSFT': ('US', 'MSFT', 'stock'),
    'GOOGL': ('US', 'GOOGL', 'stock'),
    'AMZN': ('US', 'AMZN', 'stock'),
    'TSLA': ('US', 'TSLA', 'stock'),
    'NVDA': ('US', 'NVDA', 'stock'),
    'META': ('US', 'META', 'stock'),
    'NFLX': ('US', 'NFLX', 'stock'),
}


def _parse_symbol(symbol: str):
    """解析symbol为(region, code, asset_type)"""
    s = symbol.upper().strip()

    if s in SYMBOL_REGION_MAP:
        return SYMBOL_REGION_MAP[s]

    if '.HK' in s:
        code = s.replace('.HK', '').lstrip('0')
        return ('HK', code, 'stock')
    if '.SH' in s:
        return ('SH', s.replace('.SH', ''), 'stock')
    if '.SZ' in s:
        return ('SZ', s.replace('.SZ', ''), 'stock')

    if '/' in s and 'USD' in s:
        return (None, s.replace('/', ''), 'crypto')

    forex_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
    if s in forex_pairs:
        return (None, s, 'forex')

    return ('US', s, 'stock')


class ITickProvider(BaseProvider):
    """iTick 数据提供者"""

    def __init__(self):
        super().__init__("iTick")
        self.api_key = ITICK_API_KEY
        self.base_url = "https://api.itick.org"
        self.is_connected = True

    def _headers(self):
        return {
            'accept': 'application/json',
            'token': self.api_key
        }

    def search(self, query: str) -> List[Dict[str, Any]]:
        return []

    def get_ohlcv(self, symbol: str, timeframe: str = "1d",
                  limit: int = 100) -> Optional[pd.DataFrame]:
        try:
            region, code, asset_type = _parse_symbol(symbol)
            ktype = KTYPE_MAP.get(timeframe, 8)

            url = f"{self.base_url}/{asset_type}/kline"
            params = {
                'code': code,
                'kType': ktype,
                'limit': limit,
            }
            if region and asset_type == 'stock':
                params['region'] = region

            logger.info(f"iTick request: {url} params={params}")
            response = requests.get(url, params=params, headers=self._headers(), timeout=10)

            if response.status_code != 200:
                logger.warning(f"iTick HTTP {response.status_code}: {response.text[:200]}")
                return None

            result = response.json()
            if result.get('code') != 0:
                logger.warning(f"iTick API error: {result.get('msg')}")
                return None

            data = result.get('data', [])
            if not data:
                return None

            df = pd.DataFrame(data)
            col_map = {'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume', 't': 'timestamp'}
            df.rename(columns=col_map, inplace=True)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            required = ['open', 'high', 'low', 'close', 'volume']
            for col in required:
                if col not in df.columns:
                    df[col] = 0.0

            logger.info(f"iTick got {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"iTick get_ohlcv failed for {symbol}: {e}")
            return None

    def get_realtime_price(self, symbol: str) -> Optional[float]:
        try:
            region, code, asset_type = _parse_symbol(symbol)
            url = f"{self.base_url}/{asset_type}/quote"
            params = {'code': code}
            if region and asset_type == 'stock':
                params['region'] = region

            response = requests.get(url, params=params, headers=self._headers(), timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 and result.get('data'):
                    return float(result['data'].get('c', 0) or result['data'].get('price', 0))
        except Exception as e:
            logger.error(f"iTick get_realtime_price failed for {symbol}: {e}")
        return None
