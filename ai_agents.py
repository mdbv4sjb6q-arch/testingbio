# ai_agents.py - AI Agent 系统
"""
投资AI多Agent共识决策系统
包含技术分析、动量、波动率和风险管理4个Agent
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class AgentDecision:
    """Agent决策"""
    agent_name: str
    signal: str  # BUY, SELL, HOLD
    confidence: float  # 0-1
    reasoning: str

@dataclass
class ConsensusDecision:
    """共识决策"""
    symbol: str
    timeframe: str
    overall_signal: str  # BUY, SELL, HOLD
    consensus_score: float  # 0-1
    agent_decisions: List[AgentDecision]
    timestamp: str

class AgentSystem:
    """Agent系统 - 支持所有10个分析Agent"""
    
    def __init__(self):
        self.agents = {
            'technical': TechnicalAgent(),           # 技术分析
            'momentum': MomentumAgent(),             # 动量分析
            'volatility': VolatilityAgent(),         # 波动率分析
            'risk': RiskManagementAgent(),           # 风险管理
            'crypto': CryptoAnalystAgent(),          # 加密货币分析
            'fundamental': FundamentalAnalystAgent(), # 基本面分析
            'sentiment': SentimentAnalystAgent(),    # 情绪分析
            'macro': MacroAnalystAgent(),            # 宏观经济分析
            'event': EventDrivenAgent(),             # 事件驱动分析
            'advanced': AdvancedAnalystAgent()       # 高级综合分析
        }
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str = "1d") -> ConsensusDecision:
        """执行所有Agent分析"""
        decisions = []
        
        for agent_name, agent in self.agents.items():
            try:
                decision = agent.analyze(symbol, data, timeframe)
                decisions.append(decision)
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
        
        # 计算共识
        consensus = self._calculate_consensus(decisions)
        
        from datetime import datetime
        return ConsensusDecision(
            symbol=symbol,
            timeframe=timeframe,
            overall_signal=consensus['signal'],
            consensus_score=consensus['score'],
            agent_decisions=decisions,
            timestamp=datetime.now().isoformat()
        )
    
    def _calculate_consensus(self, decisions: List[AgentDecision]) -> Dict[str, Any]:
        """计算共识 - 只考虑BUY和SELL，剔除HOLD"""
        if not decisions:
            return {'signal': 'BUY', 'score': 0.5}
        
        # 只统计BUY和SELL，忽略HOLD
        buy_count = 0
        sell_count = 0
        buy_confidence = 0
        sell_confidence = 0
        
        for decision in decisions:
            signal = decision.signal
            if signal == 'BUY':
                buy_count += 1
                buy_confidence += decision.confidence
            elif signal == 'SELL':
                sell_count += 1
                sell_confidence += decision.confidence
            # HOLD信号被忽略，不参与计算
        
        # 计算最终信号：哪个方向Agent数量多就选哪个
        if buy_count > sell_count:
            best_signal = 'BUY'
            score = buy_confidence / max(1, buy_count)
        elif sell_count > buy_count:
            best_signal = 'SELL'
            score = sell_confidence / max(1, sell_count)
        else:
            # 平票的情况，默认选BUY
            best_signal = 'BUY'
            score = 0.5
        
        return {'signal': best_signal, 'score': min(score, 1.0)}

class BaseAgent:
    """Agent基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """分析市场"""
        raise NotImplementedError

class TechnicalAgent(BaseAgent):
    """技术分析Agent"""
    
    def __init__(self):
        super().__init__("TechnicalAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """技术分析"""
        if data.empty or len(data) < 20:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 简单的移动平均线分析
        data['MA20'] = data['close'].rolling(20).mean()
        data['MA50'] = data['close'].rolling(50).mean() if len(data) >= 50 else data['close'].mean()
        
        current_price = data['close'].iloc[-1]
        ma20 = data['MA20'].iloc[-1]
        ma50 = data['MA50'].iloc[-1]
        
        # 黄金交叉
        if ma20 > ma50 and current_price > ma20:
            signal = 'BUY'
            confidence = 0.7
            reasoning = "黄金交叉信号 - 短期均线在长期均线上方"
        elif ma20 < ma50 and current_price < ma20:
            signal = 'SELL'
            confidence = 0.7
            reasoning = "死亡交叉信号 - 短期均线在长期均线下方"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "走势不明确"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class MomentumAgent(BaseAgent):
    """动量Agent"""
    
    def __init__(self):
        super().__init__("MomentumAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """动量分析"""
        if data.empty or len(data) < 10:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # ROC (Rate of Change) 分析
        data['ROC'] = data['close'].pct_change(10) * 100
        
        current_roc = data['ROC'].iloc[-1]
        
        if current_roc > 5:
            signal = 'BUY'
            confidence = 0.6 + min(current_roc / 100, 0.2)
            reasoning = f"强势上涨 - ROC: {current_roc:.2f}%"
        elif current_roc < -5:
            signal = 'SELL'
            confidence = 0.6 + min(abs(current_roc) / 100, 0.2)
            reasoning = f"强势下跌 - ROC: {current_roc:.2f}%"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "动量中性"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class VolatilityAgent(BaseAgent):
    """波动率Agent"""
    
    def __init__(self):
        super().__init__("VolatilityAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """波动率分析"""
        if data.empty or len(data) < 20:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 计算ATR (Average True Range)
        data['HL'] = data['high'] - data['low']
        data['HC'] = abs(data['high'] - data['close'].shift())
        data['LC'] = abs(data['low'] - data['close'].shift())
        data['TR'] = data[['HL', 'HC', 'LC']].max(axis=1)
        data['ATR'] = data['TR'].rolling(14).mean()
        
        current_atr = data['ATR'].iloc[-1]
        avg_atr = data['ATR'].mean()
        
        if current_atr > avg_atr * 1.5:
            signal = 'SELL'
            confidence = 0.6
            reasoning = f"高波动率 - 建议谨慎"
        elif current_atr < avg_atr * 0.5:
            signal = 'BUY'
            confidence = 0.5
            reasoning = f"低波动率 - 可能突破"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "波动率正常"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class RiskManagementAgent(BaseAgent):
    """风险管理Agent"""
    
    def __init__(self):
        super().__init__("RiskManagementAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """风险管理分析"""
        if data.empty or len(data) < 10:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 下跌风险评估
        data['Returns'] = data['close'].pct_change()
        current_return = data['Returns'].iloc[-1]
        volatility = data['Returns'].std()
        
        # Sharpe ratio 简化
        risk_score = abs(volatility) * 100
        
        if current_return < -2 or risk_score > 10:
            signal = 'SELL'
            confidence = 0.6
            reasoning = f"风险过高 - 建议减持"
        elif current_return > 2 and risk_score < 5:
            signal = 'BUY'
            confidence = 0.6
            reasoning = f"风险可控 - 可以买入"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "风险平衡"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class CryptoAnalystAgent(BaseAgent):
    """加密货币分析Agent"""
    
    def __init__(self):
        super().__init__("CryptoAnalystAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """加密货币分析"""
        if data.empty or len(data) < 5:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 加密货币特有的分析
        close_prices = data['close'].values
        current_price = close_prices[-1]
        price_change = (close_prices[-1] - close_prices[-5]) / close_prices[-5] if len(close_prices) >= 5 else 0
        
        # 24小时涨跌分析
        if price_change > 5:
            signal = 'SELL'
            confidence = 0.6
            reasoning = "加密货币短期涨幅过大，可能回调"
        elif price_change < -5:
            signal = 'BUY'
            confidence = 0.7
            reasoning = "加密货币深度下跌，可能反弹"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "加密货币走势平稳"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class FundamentalAnalystAgent(BaseAgent):
    """基本面分析Agent"""
    
    def __init__(self):
        super().__init__("FundamentalAnalystAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """基本面分析"""
        if data.empty:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="无基本面数据"
            )
        
        # 简化的基本面评分
        # 通常基本面分析需要额外的财务数据
        volume_trend = data['volume'].iloc[-1] / data['volume'].mean()
        
        if volume_trend > 1.5:
            signal = 'BUY'
            confidence = 0.6
            reasoning = "成交量突增，可能有重要信息"
        elif volume_trend < 0.5:
            signal = 'SELL'
            confidence = 0.5
            reasoning = "成交量萎缩，买入意愿不足"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "基本面保持稳定"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class SentimentAnalystAgent(BaseAgent):
    """情绪分析Agent"""
    
    def __init__(self):
        super().__init__("SentimentAnalystAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """市场情绪分析"""
        if data.empty or len(data) < 5:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 基于价格变化和成交量的情绪指标
        returns = data['close'].pct_change().dropna()
        positive_days = (returns > 0).sum()
        total_days = len(returns)
        positive_ratio = positive_days / total_days if total_days > 0 else 0.5
        
        if positive_ratio > 0.7:
            signal = 'BUY'
            confidence = 0.6
            reasoning = f"市场情绪乐观，{positive_ratio*100:.0f}%的交易日上涨"
        elif positive_ratio < 0.3:
            signal = 'SELL'
            confidence = 0.6
            reasoning = f"市场情绪悲观，{(1-positive_ratio)*100:.0f}%的交易日下跌"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "市场情绪中性"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class MacroAnalystAgent(BaseAgent):
    """宏观经济分析Agent"""
    
    def __init__(self):
        super().__init__("MacroAnalystAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """宏观经济分析"""
        if data.empty or len(data) < 20:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 基于长期趋势的宏观分析
        long_term_trend = data['close'].iloc[-1] > data['close'].iloc[0]
        volatility = data['close'].pct_change().std()
        
        if long_term_trend and volatility < 0.05:
            signal = 'BUY'
            confidence = 0.6
            reasoning = "长期上升趋势，波动平稳，宏观面支撑"
        elif not long_term_trend and volatility > 0.05:
            signal = 'SELL'
            confidence = 0.6
            reasoning = "长期下降趋势，波动增加，宏观风险上升"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "宏观环境处于平衡状态"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class EventDrivenAgent(BaseAgent):
    """事件驱动分析Agent"""
    
    def __init__(self):
        super().__init__("EventDrivenAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """事件驱动分析"""
        if data.empty or len(data) < 5:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        # 检测异常波动作为事件信号
        returns = data['close'].pct_change().dropna()
        current_return = returns.iloc[-1]
        std_dev = returns.std()
        z_score = abs(current_return) / std_dev if std_dev > 0 else 0
        
        if z_score > 2:  # 2个标准差异常
            if current_return > 0:
                signal = 'SELL'
                confidence = 0.7
                reasoning = f"检测到重大买入事件（{z_score:.1f}σ），可能跳空高开"
            else:
                signal = 'BUY'
                confidence = 0.7
                reasoning = f"检测到重大卖出事件（{z_score:.1f}σ），可能过度下跌"
        else:
            signal = 'HOLD'
            confidence = 0.5
            reasoning = "暂无重大事件信号"
        
        return AgentDecision(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class AdvancedAnalystAgent(BaseAgent):
    """高级综合分析Agent - 使用多个指标组合"""
    
    def __init__(self):
        super().__init__("AdvancedAnalystAgent")
    
    def analyze(self, symbol: str, data: pd.DataFrame, timeframe: str) -> AgentDecision:
        """综合分析"""
        if data.empty or len(data) < 50:
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="数据不足"
            )
        
        try:
            # 综合多个指标
            # 1. 趋势（MA）
            data = data.copy()
            data['MA20'] = data['close'].rolling(20).mean()
            data['MA50'] = data['close'].rolling(50).mean()
            trend_score = 0
            
            current_price = float(data['close'].iloc[-1])
            ma20 = float(data['MA20'].iloc[-1])
            ma50 = float(data['MA50'].iloc[-1])
            
            if current_price > ma20 > ma50:
                trend_score = 1
            elif current_price < ma20 < ma50:
                trend_score = -1
            
            # 2. 动量（RSI简化）
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            
            last_loss = float(loss.iloc[-1]) if not pd.isna(loss.iloc[-1]) else 0
            last_gain = float(gain.iloc[-1]) if not pd.isna(gain.iloc[-1]) else 0
            
            if last_loss > 0:
                rs = last_gain / last_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50
            
            momentum_score = 0
            if rsi > 70:
                momentum_score = -1
            elif rsi < 30:
                momentum_score = 1
            
            # 3. 综合评分
            total_score = trend_score + momentum_score
            
            if total_score >= 1:
                signal = 'BUY'
                confidence = 0.7
                reasoning = f"趋势看涨，动量指标支持买入"
            elif total_score <= -1:
                signal = 'SELL'
                confidence = 0.7
                reasoning = f"趋势看跌，动量指标支持卖出"
            else:
                signal = 'HOLD'
                confidence = 0.6
                reasoning = "指标混合，建议观望"
            
            return AgentDecision(
                agent_name=self.name,
                signal=signal,
                confidence=confidence,
                reasoning=reasoning
            )
        except Exception as e:
            logger.warning(f"AdvancedAnalystAgent analysis error: {e}")
            return AgentDecision(
                agent_name=self.name,
                signal='HOLD',
                confidence=0.5,
                reasoning="分析出错，建议观望"
            )
_agent_system = None

def get_agent_system() -> AgentSystem:
    """获取全局Agent系统"""
    global _agent_system
    if _agent_system is None:
        _agent_system = AgentSystem()
    return _agent_system

def analyze_market_consensus(symbol: str, data: pd.DataFrame, 
                            timeframe: str = "1d") -> ConsensusDecision:
    """执行市场共识分析"""
    system = get_agent_system()
    return system.analyze(symbol, data, timeframe)
