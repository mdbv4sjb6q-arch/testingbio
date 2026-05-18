# models.py - AI Trader Pro 数据模型
"""
完整的数据模型，支持全球市场
包含: OHLCV, 市场数据, 交易信号, Agent决策, 推理结果, 交易建议
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import pandas as pd


@dataclass
class OHLCV:
    """OHLCV K线数据"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None
    trades_count: Optional[int] = None
    vwap: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'open': self.open, 'high': self.high,
            'low': self.low, 'close': self.close,
            'volume': self.volume,
            'quote_volume': self.quote_volume,
            'trades_count': self.trades_count,
            'vwap': self.vwap
        }


@dataclass
class Instrument:
    """金融标的"""
    symbol: str
    name: str
    asset_class: str
    region: str
    exchange: Optional[str] = None
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol, 'name': self.name,
            'asset_class': self.asset_class, 'region': self.region,
            'exchange': self.exchange, 'currency': self.currency
        }


@dataclass
class TickData:
    """逐笔数据"""
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    buyer_id: Optional[str] = None
    seller_id: Optional[str] = None
    trade_id: Optional[str] = None


@dataclass
class OrderBook:
    """订单簿"""
    timestamp: datetime
    symbol: str
    bids: List[tuple]
    asks: List[tuple]

    @property
    def bid_price(self) -> float:
        return self.bids[0][0] if self.bids else 0

    @property
    def ask_price(self) -> float:
        return self.asks[0][0] if self.asks else 0

    @property
    def spread(self) -> float:
        return self.ask_price - self.bid_price if self.bid_price and self.ask_price else 0


@dataclass
class MarketData:
    """市场数据集合"""
    instrument: Instrument
    timeframe: str
    data: List[OHLCV]
    source: str = ""

    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame"""
        df = pd.DataFrame([
            {
                'timestamp': d.timestamp, 'open': d.open, 'high': d.high,
                'low': d.low, 'close': d.close, 'volume': d.volume,
                'quote_volume': d.quote_volume, 'trades_count': d.trades_count,
                'vwap': d.vwap
            }
            for d in self.data
        ])
        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
        return df

    @staticmethod
    def from_dataframe(instrument: Instrument, timeframe: str,
                       df: pd.DataFrame, source: str = "") -> 'MarketData':
        """从DataFrame创建MarketData"""
        ohlcv_list = []
        for timestamp, row in df.iterrows():
            ts = timestamp.to_pydatetime() if isinstance(timestamp, pd.Timestamp) else timestamp
            ohlcv_list.append(OHLCV(
                timestamp=ts,
                open=float(row['open']), high=float(row['high']),
                low=float(row['low']), close=float(row['close']),
                volume=float(row['volume']),
                quote_volume=float(row.get('quote_volume', 0)),
                trades_count=int(row.get('trades_count', 0)) if 'trades_count' in row else None,
                vwap=float(row['vwap']) if 'vwap' in row else None
            ))
        return MarketData(instrument=instrument, timeframe=timeframe, data=ohlcv_list, source=source)


@dataclass
class Signal:
    """交易信号"""
    timestamp: datetime
    symbol: str
    action: str  # buy, sell, hold, long, short
    confidence: float
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reason: str = ""
    indicators: Dict[str, Any] = field(default_factory=dict)
    source: str = ""


@dataclass
class IndicatorResult:
    """技术指标结果"""
    name: str
    values: Dict[str, List[float]]
    timestamps: List[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecision:
    """AI Agent决策"""
    agent_name: str
    symbol: str
    timestamp: datetime
    action: str  # buy, sell, hold, long, short
    confidence: float
    score: float
    reasoning: str
    indicators_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'agent_name': self.agent_name, 'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action, 'confidence': self.confidence,
            'score': self.score, 'reasoning': self.reasoning,
            'indicators_used': self.indicators_used
        }


@dataclass
class ConsensusDecision:
    """多Agent共识决策"""
    symbol: str
    timestamp: datetime
    consensus_action: str
    confidence: float
    individual_decisions: List[AgentDecision]
    weighted_scores: Dict[str, float]
    summary: str

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'consensus_action': self.consensus_action,
            'confidence': self.confidence,
            'individual_decisions': [d.to_dict() for d in self.individual_decisions],
            'weighted_scores': self.weighted_scores,
            'summary': self.summary
        }


@dataclass
class InferenceResult:
    """LLM推理结果"""
    final_signal: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, VETO, ERROR
    confidence: float
    aggregated_score: float
    agent_contributions: Dict[str, float]
    reasoning_chain: List[str]
    risk_assessment: Dict[str, Any]
    leviathan_applied: bool = False
    raw_model_output: str = ""

    def to_dict(self) -> Dict:
        return {
            'final_signal': self.final_signal,
            'confidence': self.confidence,
            'aggregated_score': self.aggregated_score,
            'agent_contributions': self.agent_contributions,
            'reasoning_chain': self.reasoning_chain,
            'risk_assessment': self.risk_assessment,
            'leviathan_applied': self.leviathan_applied
        }


@dataclass
class TradeRecommendation:
    """完整交易建议 - 包含做多/做空/止盈/止损"""
    symbol: str
    timestamp: datetime
    action: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL, LONG, SHORT
    direction: str  # long, short, neutral
    confidence: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: str = "moderate"  # conservative, moderate, aggressive
    risk_reward_ratio: Optional[float] = None
    reasoning: str = ""
    agent_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    indicators_summary: Dict[str, Any] = field(default_factory=dict)
    override_active: bool = False

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'direction': self.direction,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'risk_reward_ratio': self.risk_reward_ratio,
            'reasoning': self.reasoning,
            'agent_breakdown': self.agent_breakdown,
            'indicators_summary': self.indicators_summary,
            'override_active': self.override_active
        }


@dataclass
class UserQuery:
    """用户查询"""
    user_id: str
    query_text: str
    symbol: Optional[str] = None
    asset_class: Optional[str] = None
    region: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id, 'query_text': self.query_text,
            'symbol': self.symbol, 'asset_class': self.asset_class,
            'region': self.region, 'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AIResponse:
    """AI回复"""
    user_id: str
    query_id: str
    response_text: str
    consensus_decision: Optional[ConsensusDecision] = None
    trade_recommendation: Optional[TradeRecommendation] = None
    market_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id, 'query_id': self.query_id,
            'response_text': self.response_text,
            'consensus_decision': self.consensus_decision.to_dict() if self.consensus_decision else None,
            'trade_recommendation': self.trade_recommendation.to_dict() if self.trade_recommendation else None,
            'market_data': self.market_data,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence
        }
