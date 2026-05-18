# massive_provider.py - Massive API 数据提供者
"""
Massive.com API 集成
支持全球二级市场：股票、期权、期货、指数、外汇、加密、经济数据
"""

import requests
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from base_provider import BaseProvider

logger = logging.getLogger(__name__)

class MassiveProvider(BaseProvider):
    """Massive.com 数据提供者"""
    
    def __init__(self, api_key: str = "YgorrHnF7VG9Sto2gdn4jrXq8P3AtydR"):
        super().__init__("Massive")
        self.api_key = api_key
        self.base_url = "https://api.massive.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.is_connected = self._test_connection()
    
    def _test_connection(self) -> bool:
        """测试API连接"""
        try:
            resp = requests.get(
                f"{self.base_url}/health",
                headers=self.headers,
                timeout=5
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Massive connection test failed: {e}")
            return False
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索标的"""
        try:
            if not self.is_connected:
                return []
            
            url = f"{self.base_url}/search"
            params = {
                "q": query,
                "limit": 20
            }
            
            resp = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            results = []
            
            if 'results' in data:
                for item in data['results']:
                    asset_type = item.get('type', 'UNKNOWN').upper()
                    results.append({
                        'symbol': item.get('symbol', ''),
                        'name': item.get('name', ''),
                        'exchange': item.get('exchange', ''),
                        'type': self._map_asset_type(asset_type)
                    })
            
            return results[:20]
        
        except Exception as e:
            logger.error(f"Massive search failed: {e}")
            return []
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            if not self.is_connected:
                return None
            
            # 转换时间框架
            interval = self._convert_timeframe(timeframe)
            
            url = f"{self.base_url}/bars"
            params = {
                "symbol": symbol,
                "timeframe": interval,
                "limit": min(limit, 1000)
            }
            
            resp = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if resp.status_code != 200:
                logger.warning(f"Massive OHLCV failed: {resp.status_code}")
                return None
            
            data = resp.json()
            if 'bars' not in data:
                return None
            
            records = []
            for bar in data['bars']:
                records.append({
                    'timestamp': bar.get('t'),
                    'open': bar.get('o'),
                    'high': bar.get('h'),
                    'low': bar.get('l'),
                    'close': bar.get('c'),
                    'volume': bar.get('v')
                })
            
            if not records:
                return None
            
            df = pd.DataFrame(records)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.sort_values('timestamp').reset_index(drop=True)
        
        except Exception as e:
            logger.error(f"Massive OHLCV error: {e}")
            return None
    
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        try:
            if not self.is_connected:
                return None
            
            url = f"{self.base_url}/quotes/latest"
            params = {"symbol": symbol}
            
            resp = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if 'quote' in data:
                return data['quote'].get('last', 0)
            
            return None
        
        except Exception as e:
            logger.error(f"Massive price error: {e}")
            return None
    
    def get_market_info(self, symbol: str) -> Optional[Dict]:
        """获取市场信息"""
        try:
            if not self.is_connected:
                return None
            
            url = f"{self.base_url}/quotes/latest"
            params = {"symbol": symbol}
            
            resp = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if 'quote' not in data:
                return None
            
            quote = data['quote']
            return {
                'symbol': symbol,
                'price': quote.get('last', 0),
                'bid': quote.get('bid', 0),
                'ask': quote.get('ask', 0),
                'volume': quote.get('volume', 0),
                'change': quote.get('change', 0),
                'change_percent': quote.get('changePercent', 0),
                'timestamp': quote.get('timestamp', '')
            }
        
        except Exception as e:
            logger.error(f"Massive market info error: {e}")
            return None
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """转换时间框架为Massive格式"""
        mapping = {
            '1m': '1Min',
            '5m': '5Min',
            '15m': '15Min',
            '30m': '30Min',
            '1h': '1H',
            '4h': '4H',
            '1d': '1Day',
            '1w': '1Week',
            '1M': '1Month'
        }
        return mapping.get(timeframe, '1Day')
    
    def _map_asset_type(self, asset_type: str) -> str:
        """映射资产类型"""
        mapping = {
            'STOCK': 'STOCK',
            'OPTION': 'OPTION',
            'FUTURE': 'FUTURE',
            'INDEX': 'INDEX',
            'FOREX': 'FOREX',
            'CRYPTO': 'CRYPTO',
            'ETF': 'ETF'
        }
        return mapping.get(asset_type, 'UNKNOWN')
    
    def get_options_chain(self, symbol: str, expiration: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取期权链"""
        try:
            if not self.is_connected:
                return None
            
            url = f"{self.base_url}/options/chain"
            params = {"symbol": symbol}
            if expiration:
                params["expiration"] = expiration
            
            resp = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if 'chain' not in data:
                return None
            
            records = []
            for option in data['chain']:
                records.append({
                    'symbol': option.get('symbol'),
                    'strike': option.get('strike'),
                    'expiration': option.get('expiration'),
                    'type': option.get('type'),  # CALL or PUT
                    'bid': option.get('bid'),
                    'ask': option.get('ask'),
                    'last': option.get('last'),
                    'volume': option.get('volume'),
                    'open_interest': option.get('openInterest'),
                    'implied_volatility': option.get('impliedVolatility')
                })
            
            return pd.DataFrame(records) if records else None
        
        except Exception as e:
            logger.error(f"Massive options chain error: {e}")
            return None
    
    def get_economic_data(self, indicator: str) -> Optional[List[Dict]]:
        """获取经济指标数据"""
        try:
            if not self.is_connected:
                return None
            
            url = f"{self.base_url}/economic/{indicator}"
            
            resp = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            return data.get('data', [])
        
        except Exception as e:
            logger.error(f"Massive economic data error: {e}")
            return None
