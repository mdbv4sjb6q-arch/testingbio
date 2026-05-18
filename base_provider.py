# base_provider.py - 数据提供者基类
"""
所有市场数据提供者的基类
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class OHLCV:
    """OHLCV 数据点"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class BaseProvider(ABC):
    """市场数据提供者基类"""
    
    def __init__(self, name: str = "BaseProvider"):
        self.name = name
        self.is_connected = False
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索标的"""
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str = "1d", 
                  limit: int = 100) -> Optional[pd.DataFrame]:
        """获取OHLCV数据"""
        pass
    
    @abstractmethod
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """获取实时价格"""
        pass
    
    def health_check(self) -> bool:
        """健康检查"""
        return self.is_connected
