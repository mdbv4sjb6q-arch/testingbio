# cmc_provider.py - CoinMarketCap API 数据提供者
"""
CoinMarketCap API 集成
支持K线数据、价格、市场信息等加密货币数据
"""

import requests
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from base_provider import BaseProvider

logger = logging.getLogger(__name__)

class CMCProvider(BaseProvider):
    """CoinMarketCap 数据提供者"""
    
    def __init__(self, api_key: str = "41f58281b0a34e8ea821ebb470a2fdde"):
        super().__init__("CoinMarketCap")
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.is_connected = self._test_connection()
    
    def _test_connection(self) -> bool:
        """测试API连接"""
        try:
            url = f"{self.base_url}/cryptocurrency/info"
            params = {"id": "1", "CMC_PRO_API_KEY": self.api_key}
            resp = requests.get(url, params=params, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"CMC connection test failed: {e}")
            return False
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索加密货币"""
        try:
            if not self.is_connected:
                return []
            
            url = f"{self.base_url}/cryptocurrency/map"
            params = {
                "symbol": query.upper(),
                "CMC_PRO_API_KEY": self.api_key,
                "limit": 10
            }
            
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            results = []
            
            if 'data' in data:
                for crypto in data['data']:
                    results.append({
                        'symbol': f"{crypto['symbol']}/USDT",
                        'name': crypto['name'],
                        'exchange': 'CMC',
                        'type': 'CRYPTO',
                        'cmc_id': crypto['id']
                    })
            
            return results[:10]
        
        except Exception as e:
            logger.error(f"CMC search failed: {e}")
            return []
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        try:
            if not self.is_connected:
                return None
            
            # 提取币种符号 (e.g., "BTC" from "BTC/USDT")
            coin_symbol = symbol.split('/')[0].upper()
            
            url = f"{self.base_url}/cryptocurrency/ohlcv/historical"
            params = {
                "symbol": coin_symbol,
                "time_period": self._convert_timeframe_to_cmc(timeframe),
                "time_start": int((datetime.now() - timedelta(days=limit*2)).timestamp()),
                "CMC_PRO_API_KEY": self.api_key,
                "limit": min(limit, 100)  # CMC限制最多100
            }
            
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"CMC OHLCV failed: {resp.status_code}")
                return None
            
            data = resp.json()
            if 'data' not in data or 'quotes' not in data['data']:
                return None
            
            quotes = data['data']['quotes']
            records = []
            
            for quote in quotes:
                timestamp = quote['timestamp']
                quote_data = quote['quote']['USD']
                
                records.append({
                    'timestamp': timestamp,
                    'open': quote_data.get('open', 0),
                    'high': quote_data.get('high', 0),
                    'low': quote_data.get('low', 0),
                    'close': quote_data.get('close', 0),
                    'volume': quote_data.get('volume', 0)
                })
            
            if not records:
                return None
            
            df = pd.DataFrame(records)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.sort_values('timestamp').reset_index(drop=True)
        
        except Exception as e:
            logger.error(f"CMC OHLCV error: {e}")
            return None
    
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        try:
            if not self.is_connected:
                return None
            
            coin_symbol = symbol.split('/')[0].upper()
            
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            params = {
                "symbol": coin_symbol,
                "CMC_PRO_API_KEY": self.api_key,
                "convert": "USD"
            }
            
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if 'data' in data and coin_symbol in data['data']:
                return data['data'][coin_symbol]['quote']['USD']['price']
            
            return None
        
        except Exception as e:
            logger.error(f"CMC price error: {e}")
            return None
    
    def _convert_timeframe_to_cmc(self, timeframe: str) -> str:
        """转换时间框架为CMC格式"""
        mapping = {
            '1m': 'minutely',
            '5m': 'hourly',
            '15m': 'hourly',
            '1h': 'hourly',
            '4h': 'daily',
            '1d': 'daily',
            '1w': 'weekly',
            '1M': 'monthly'
        }
        return mapping.get(timeframe, 'daily')
    
    def get_market_info(self, symbol: str) -> Optional[Dict]:
        """获取市场信息"""
        try:
            if not self.is_connected:
                return None
            
            coin_symbol = symbol.split('/')[0].upper()
            
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            params = {
                "symbol": coin_symbol,
                "CMC_PRO_API_KEY": self.api_key,
                "convert": "USD"
            }
            
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            if 'data' in data and coin_symbol in data['data']:
                crypto_data = data['data'][coin_symbol]
                quote = crypto_data['quote']['USD']
                
                return {
                    'symbol': coin_symbol,
                    'name': crypto_data.get('name', ''),
                    'price': quote.get('price', 0),
                    'market_cap': quote.get('market_cap', 0),
                    'volume_24h': quote.get('volume_24h', 0),
                    'percent_change_24h': quote.get('percent_change_24h', 0),
                    'percent_change_7d': quote.get('percent_change_7d', 0),
                    'percent_change_30d': quote.get('percent_change_30d', 0)
                }
            
            return None
        
        except Exception as e:
            logger.error(f"CMC market info error: {e}")
            return None
