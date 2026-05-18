# technical_indicators.py - 完整的技术指标引擎
"""
将TypeScript K线指标转换为Python实现
支持所有您提供的技术指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum

class IndicatorSignal(Enum):
    """指标信号"""
    BUY = "buy"
    SELL = "sell"
    SHORT_BUY = "short_buy"  # 空头补仓
    SHORT_SELL = "short_sell"  # 空头建仓
    HOLD = "hold"
    STOP_LOSS = "stop_loss"  # 止损
    TAKE_PROFIT = "take_profit"  # 止盈

class TechnicalIndicators:
    """技术指标计算引擎"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化指标引擎
        df: DataFrame with columns [open, high, low, close, volume]
        """
        self.df = df.copy()
        self.results = {}
        
    def sma(self, col, period: int) -> np.ndarray:
        """简单移动平均 (Simple Moving Average)"""
        if isinstance(col, (pd.Series, np.ndarray)):
            return pd.Series(col).rolling(window=period).mean().values
        return self.df[col].rolling(window=period).mean().values
    
    def ema(self, col, period: int) -> np.ndarray:
        """指数移动平均 (Exponential Moving Average)"""
        if isinstance(col, (pd.Series, np.ndarray)):
            return pd.Series(col).ewm(span=period, adjust=False).mean().values
        return self.df[col].ewm(span=period, adjust=False).mean().values
    
    def ma(self, col, period: int) -> np.ndarray:
        """移动平均（MA）"""
        return self.sma(col, period)
    
    def ref(self, arr: np.ndarray, periods: int) -> np.ndarray:
        """参考（向后移动）- 取过去第n个值"""
        result = np.full_like(arr, np.nan, dtype=float)
        if periods > 0:
            result[periods:] = arr[:-periods]
        return result
    
    def hhv(self, col: str, period: int) -> np.ndarray:
        """最高值 (Highest High Value)"""
        return self.df[col].rolling(window=period).max().values
    
    def llv(self, col: str, period: int) -> np.ndarray:
        """最低值 (Lowest Low Value)"""
        return self.df[col].rolling(window=period).min().values
    
    def cross(self, arr1: np.ndarray, arr2: np.ndarray) -> np.ndarray:
        """交叉信号 - arr1从下穿过arr2"""
        result = np.zeros(len(arr1), dtype=bool)
        for i in range(1, len(arr1)):
            if not (np.isnan(arr1[i]) or np.isnan(arr2[i]) or 
                   np.isnan(arr1[i-1]) or np.isnan(arr2[i-1])):
                result[i] = (arr1[i-1] <= arr2[i-1]) and (arr1[i] > arr2[i])
        return result
    
    def barslast(self, condition: np.ndarray) -> np.ndarray:
        """最后一次满足条件的K线数"""
        result = np.full(len(condition), np.inf)
        for i in range(len(condition)):
            if condition[i]:
                result[i] = 0
            elif i > 0 and not np.isinf(result[i-1]):
                result[i] = result[i-1] + 1
        return result
    
    def filter_signal(self, condition: np.ndarray, threshold_bars: int = 3) -> np.ndarray:
        """过滤信号 - 信号持续threshold_bars根K线才有效"""
        result = np.zeros(len(condition), dtype=bool)
        for i in range(len(condition)):
            if condition[i]:
                result[i] = True
            elif i > 0 and result[i-1]:
                result[i] = True
            elif i >= threshold_bars:
                # 检查前threshold_bars根K线是否有信号
                if np.any(condition[i-threshold_bars:i]):
                    result[i] = True
        return result
    
    # ==================== 主图指标 ====================
    
    def indicator_main_chart(self) -> Dict[str, np.ndarray]:
        """
        主图指标 - 包含均线、波段和买卖点
        
        返回值:
        {
            'MA1': 5日均线,
            'MA2': 10日均线,
            'MA3': 20日均线,
            'MA4': 60日均线,
            'VAR3': 波段指标,
            'VAR4': 快速波段,
            'BUY_SIGNAL': 买点,
            'SELL_SIGNAL': 卖点,
            'STOP_LOSS_SIGNAL': 止损
        }
        """
        close = self.df['close'].values
        high = self.df['high'].values
        low = self.df['low'].values
        
        # 基础计算
        va2 = (close + high + low) / 3
        va3 = self.ema(pd.Series(va2), 10)
        va4 = self.ref(va3, 1)
        
        # 均线
        ma1 = self.ma('close', 5)
        ma2 = self.ma('close', 10)
        ma3 = self.ma('close', 20)
        ma4 = self.ma('close', 60)
        
        # 波段计算
        var1 = self.hhv('high', 25)  # 25周期最高
        var2 = self.llv('low', 25)   # 25周期最低
        
        # 避免除以零
        denominator = var1 - var2
        denominator = np.where(denominator == 0, 1, denominator)
        
        wave_raw = (close - var2) / denominator * 100
        wave_series = pd.Series(wave_raw)
        var3 = self.ema(wave_series, 20)  # 20日EMA波段
        var4 = self.ema(wave_series, 5)   # 5日EMA波段
        
        # 买卖信号
        buy_signal = self.cross(var4, var3)  # 快线上穿慢线
        sell_signal = self.cross(var3, var4)  # 慢线上穿快线
        
        # 止损信号
        barslast_buy = self.barslast(buy_signal)
        stop_loss_signal = sell_signal & (barslast_buy <= 3)
        
        return {
            'MA1': ma1,
            'MA2': ma2,
            'MA3': ma3,
            'MA4': ma4,
            'VAR3': var3,
            'VAR4': var4,
            'BUY_SIGNAL': buy_signal,
            'SELL_SIGNAL': sell_signal,
            'STOP_LOSS_SIGNAL': stop_loss_signal,
            'WAVE_VAR1': var1,
            'WAVE_VAR2': var2
        }
    
    # ==================== 副图指标1 ====================
    
    def indicator_subplot1(self) -> Dict[str, np.ndarray]:
        """
        副图指标1 - 逃顶信号
        
        返回值:
        {
            'XX': KDJ K值,
            'YY': KDJ D值,
            'ESCAPE_TOP_SIGNAL': 逃顶信号
        }
        """
        close = self.df['close'].values
        high = self.df['high'].values
        low = self.df['low'].values
        
        # 计算KDJ
        var1 = (2 * close + high + low) / 4
        var2 = self.llv('low', 34)
        var3 = self.hhv('high', 34)
        
        denominator = var3 - var2
        denominator = np.where(denominator == 0, 1, denominator)
        
        kdj_raw = (var1 - var2) / denominator * 100
        kdj_series = pd.Series(kdj_raw)
        
        xx = self.ema(kdj_series, 13)
        yy_raw = 0.667 * self.ref(xx, 1) + 0.333 * xx
        yy = self.ema(pd.Series(yy_raw), 2)
        
        # 逃顶信号 - XX > 80且YY上穿XX
        escape_top = (xx > 80) & self.cross(yy, xx)
        
        return {
            'XX': xx,
            'YY': yy,
            'ESCAPE_TOP_SIGNAL': escape_top
        }
    
    # ==================== 副图指标2 ====================
    
    def indicator_subplot2(self) -> Dict[str, np.ndarray]:
        """
        副图指标2 - MACD-like指标
        
        返回值:
        {
            'MACD_LINE': MACD线,
            'SIGNAL_LINE': 信号线
        }
        """
        n = 5
        close = self.df['close'].values
        high = self.df['high'].values
        low = self.df['low'].values
        
        # 计算RSV（相对强弱）
        rsv_raw = (close - self.llv('low', n)) / (self.hhv('high', n) - self.llv('low', n)) * 100
        rsv_series = pd.Series(rsv_raw)
        
        # 计算MACD-like
        var1 = 4 * self.sma(rsv_series, 5) - 3 * self.sma(
            pd.Series(self.sma(rsv_series, 5)), int(3.2)
        )
        
        return {
            'MACD_LINE': np.asarray(var1)
        }
    
    # ==================== 副图指标3 ====================
    
    def indicator_subplot3(self) -> Dict[str, np.ndarray]:
        """
        副图指标3 - CCI-like指标
        
        返回值:
        {
            'CCI_VALUE': CCI值,
            'CCI_THRESHOLD': 阈值线
        }
        """
        close = self.df['close'].values
        high = self.df['high'].values
        low = self.df['low'].values
        
        varo5 = self.llv('low', 27)
        varo6 = self.hhv('high', 34)
        
        denominator = varo6 - varo5
        denominator = np.where(denominator == 0, 1, denominator)
        
        cci_raw = (close - varo5) / denominator * 4
        cci_series = pd.Series(cci_raw)
        varo7 = self.ema(cci_series, 4) * 25
        
        # 阈值
        threshold = np.where(varo7 < 10, 80, 100)
        
        return {
            'CCI_VALUE': varo7,
            'CCI_THRESHOLD': threshold
        }
    
    # ==================== 副图指标4 ====================
    
    def indicator_subplot4(self) -> Dict[str, np.ndarray]:
        """
        副图指标4 - 不要操作信号
        
        返回值:
        {
            'DONT_BUY': 不要买信号,
            'DONT_OPERATE': 不要操作信号
        }
        """
        low = self.df['low'].values
        open_ = self.df['open'].values
        high = self.df['high'].values
        
        var1 = self.ref((low + open_ + high + self.df['close'].values) / 4, 1)
        
        # ATR-like计算
        tr_list = []
        for i in range(len(low)):
            if i == 0:
                tr = high[i] - low[i]
            else:
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - low[i-1]) if not np.isnan(low[i-1]) else 0,
                    abs(low[i] - high[i-1]) if not np.isnan(high[i-1]) else 0
                )
            tr_list.append(tr)
        
        tr_arr = np.array(tr_list)
        tr_series = pd.Series(tr_arr)
        
        # 计算指标
        var2 = self.sma(
            pd.Series(np.abs(low - var1)),
            13
        ) / self.sma(
            pd.Series(np.maximum(low - var1, 0)),
            10
        )
        
        var2 = np.where(np.isinf(var2), 0, var2)
        var2_series = pd.Series(var2)
        var3 = self.ema(var2_series, 10)
        var4 = self.llv('low', 33)
        var5_raw = np.where(low <= var4, var3, 0)
        var5_series = pd.Series(var5_raw)
        var5 = self.ema(var5_series, 3)
        
        # 信号
        dont_buy = var5 > self.ref(var5, 1)
        dont_operate = var5 < self.ref(var5, 1)
        
        return {
            'DONT_BUY': dont_buy,
            'DONT_OPERATE': dont_operate,
            'VAR5': var5
        }
    
    # ==================== 综合评分 ====================
    
    def get_comprehensive_signal(self) -> Dict:
        """获取综合交易信号"""
        main = self.indicator_main_chart()
        sub1 = self.indicator_subplot1()
        sub2 = self.indicator_subplot2()
        sub3 = self.indicator_subplot3()
        sub4 = self.indicator_subplot4()
        
        # 获取最后一根K线的信号
        idx = -1
        
        signals = {
            'buy': 0,
            'sell': 0,
            'short_buy': 0,
            'stop_loss': 0,
            'escape_top': 0,
            'dont_buy': 0,
            'dont_operate': 0
        }
        
        # 主图信号
        if main['BUY_SIGNAL'][idx]:
            signals['buy'] += 2
        if main['SELL_SIGNAL'][idx]:
            signals['sell'] += 2
        if main['STOP_LOSS_SIGNAL'][idx]:
            signals['stop_loss'] += 1
        
        # 副图1信号
        if sub1['ESCAPE_TOP_SIGNAL'][idx]:
            signals['escape_top'] += 1
            signals['sell'] += 1
        
        # 副图4信号
        if sub4['DONT_BUY'][idx]:
            signals['dont_buy'] += 1
        if sub4['DONT_OPERATE'][idx]:
            signals['dont_operate'] += 1
        
        return {
            'signals': signals,
            'buy': main['BUY_SIGNAL'][idx],
            'sell': main['SELL_SIGNAL'][idx],
            'ma1': main['MA1'][idx],
            'ma2': main['MA2'][idx],
            'ma3': main['MA3'][idx],
            'ma4': main['MA4'][idx],
            'var3': main['VAR3'][idx],
            'var4': main['VAR4'][idx],
            'xx': sub1['XX'][idx],
            'yy': sub1['YY'][idx],
            'cci': sub3['CCI_VALUE'][idx],
            'var5': sub4['VAR5'][idx]
        }
    
    def get_all_indicators(self) -> Dict[str, np.ndarray]:
        """获取所有指标值"""
        main = self.indicator_main_chart()
        sub1 = self.indicator_subplot1()
        sub2 = self.indicator_subplot2()
        sub3 = self.indicator_subplot3()
        sub4 = self.indicator_subplot4()
        
        result = {}
        for d in [main, sub1, sub2, sub3, sub4]:
            result.update(d)
        
        return result

def calculate_all_indicators(market_data_df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """便捷函数：计算所有指标"""
    indicators = TechnicalIndicators(market_data_df)
    return indicators.get_all_indicators()

def get_trading_signal(market_data_df: pd.DataFrame) -> Dict:
    """便捷函数：获取综合交易信号"""
    indicators = TechnicalIndicators(market_data_df)
    return indicators.get_comprehensive_signal()
