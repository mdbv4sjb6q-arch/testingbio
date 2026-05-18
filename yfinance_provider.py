# yfinance_provider.py - Yahoo Finance 数据提供者
"""
Yahoo Finance 市场数据提供者
支持全球股票和指数
"""

import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from base_provider import BaseProvider, OHLCV

logger = logging.getLogger(__name__)

class YFinanceProvider(BaseProvider):
    """Yahoo Finance 数据提供者"""
    
    def __init__(self):
        super().__init__("Yahoo Finance")
        self.is_connected = True
        logger.info("YFinance provider initialized")
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            # 简单的搜索实现 - 直接尝试获取数据
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            
            if info and 'longName' in info:
                return [{
                    'symbol': query.upper(),
                    'name': info.get('longName', query),
                    'exchange': info.get('exchange', 'UNKNOWN'),
                    'type': 'STOCK'
                }]
        except Exception as e:
            logger.warning(f"Search failed for {query}: {e}")
        
        return []
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """获取OHLCV数据"""
        try:
            # 计算时间范围
            end_date = datetime.now()
            days_back = max(limit * 2, 365)  # 多取一些数据
            start_date = end_date - timedelta(days=days_back)
            
            # 获取数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=self._convert_timeframe(timeframe))
            
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return None
            
            df = df.reset_index()
            col_map = {}
            for c in df.columns:
                cl = c.lower() if isinstance(c, str) else str(c).lower()
                if 'open' in cl and 'open' not in col_map.values():
                    col_map[c] = 'open'
                elif 'high' in cl and 'high' not in col_map.values():
                    col_map[c] = 'high'
                elif 'low' in cl and 'low' not in col_map.values():
                    col_map[c] = 'low'
                elif 'close' in cl and 'close' not in col_map.values():
                    col_map[c] = 'close'
                elif 'vol' in cl and 'volume' not in col_map.values():
                    col_map[c] = 'volume'
                elif 'date' in cl or 'time' in cl or 'index' in cl:
                    col_map[c] = 'timestamp'
            df.rename(columns=col_map, inplace=True)
            required = ['open', 'high', 'low', 'close', 'volume']
            for col in required:
                if col not in df.columns:
                    df[col] = 0.0
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.date_range(end=datetime.now(), periods=len(df), freq='D')
            
            # 取最后 limit 条
            return df.tail(limit)
        
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {symbol}: {e}")
            return None
    
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
        
        return None
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """转换时间框架格式"""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '1h',  # 4h 使用 1h 的 4 倍
            '1d': '1d',
            'daily': '1d',
            'weekly': '1wk',
            '1w': '1wk'
        }
        return mapping.get(timeframe.lower(), '1d')
