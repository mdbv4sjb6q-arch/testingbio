# ccxt_provider.py - CCXT 加密货币数据提供者
"""
CCXT 加密货币交易所数据提供者
支持 Binance, Coinbase, Kraken 等多个交易所
"""

import ccxt
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from base_provider import BaseProvider, OHLCV

logger = logging.getLogger(__name__)

class CCXTProvider(BaseProvider):
    """CCXT 加密货币数据提供者"""
    
    def __init__(self, exchange_name: str = 'binance'):
        super().__init__(f"CCXT-{exchange_name}")
        self.exchange_name = exchange_name.lower()
        self.exchange = self._init_exchange()
        self.is_connected = self.exchange is not None
    
    def _init_exchange(self):
        """初始化交易所"""
        try:
            if self.exchange_name == 'binance':
                ex = ccxt.binance({'enableRateLimit': True})
            elif self.exchange_name == 'coinbase':
                ex = ccxt.coinbase({'enableRateLimit': True})
            elif self.exchange_name == 'kraken':
                ex = ccxt.kraken({'enableRateLimit': True})
            else:
                ex = ccxt.binance({'enableRateLimit': True})
            ex.load_markets()
            return ex
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_name}: {e}")
            return None
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索交易对"""
        try:
            if not self.exchange or not self.exchange.symbols:
                return []
            
            query_upper = query.upper()
            results = []
            
            for symbol in (self.exchange.symbols or []):
                if query_upper in symbol:
                    results.append({
                        'symbol': symbol,
                        'name': symbol,
                        'exchange': self.exchange_name,
                        'type': 'CRYPTO'
                    })
            
            return results[:10]
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """获取OHLCV数据"""
        try:
            if not self.exchange:
                return None
            
            # 转换时间框架
            tf = self._convert_timeframe(timeframe)
            
            # 获取数据
            ohlcv = self.exchange.fetch_ohlcv(symbol, tf, limit=limit)
            
            if not ohlcv:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {symbol}: {e}")
            return None
    
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        try:
            if not self.exchange:
                return None
            
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """转换时间框架格式"""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            'daily': '1d',
            'weekly': '1w',
            '1w': '1w'
        }
        return mapping.get(timeframe.lower(), '1d')
