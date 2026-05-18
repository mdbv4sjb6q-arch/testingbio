# API 技术文档
## XBIT AI 投资系统 - RESTful API 参考手册

**版本**: 1.0.0  
**最后更新**: 2026年3月11日  
**系统**: 投资AI系统（本地LLM + 多Agent共识）

---

## 目录
1. [概述](#概述)
2. [认证与授权](#认证与授权)
3. [API密钥管理](#api密钥管理)
4. [防DDOS和速率限制](#防ddos和速率限制)
5. [数据接口](#数据接口)
6. [分析接口](#分析接口)
7. [用户管理接口](#用户管理接口)
8. [错误处理](#错误处理)
9. [使用示例](#使用示例)

---

## 概述

### 基础信息
- **基础URL**: `http://localhost:9000` 或 `http://{服务器IP}:9000`
- **协议**: HTTP / HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

### 支持的市场
- **外汇 (Forex)**: EURUSD, GBPUSD, USDJPY 等
- **美股 (US Stocks)**: AAPL, MSFT, GOOGL, AMZN, TSLA 等
- **港股 (HK Stocks)**: 0700.HK, 9988.HK 等
- **数字货币 (Crypto)**: BTC/USDT, ETH/USDT, XRP/USDT 等
- **大宗商品 (Commodities)**: GOLD, OIL, SILVER 等
- **指数**: SPX500, HSI, SSE 等

### 用户等级与功能
| 等级 | 价格模式 | 日API调用限制 | 说明 |
|------|---------|-------------|------|
| FREE | 免费 | 100次/天 | 基础功能，市场搜索和K线 |
| PRO | 按天计费 | 500次/天 | 专业指标、K线信号 |
| SVIP | 按天计费 | 1000次/天 | 完整功能、AI分析、鲸鱼监控 |

---

## 认证与授权

### 认证方式

所有API请求（除了公开端点）都需要提供有效的API密钥。支持以下认证方式：

#### 方式1：Authorization Header (推荐)
```
Authorization: Bearer pk_xxxxxxxxxxxxxxxxxxxxxxxx
```

#### 方式2：X-API-Key Header
```
X-API-Key: pk_xxxxxxxxxxxxxxxxxxxxxxxx
```

#### 方式3：URL参数
```
GET /api/market_data?symbol=AAPL&api_key=pk_xxxxxxxxxxxxxxxxxxxxxxxx
```

#### 方式4：POST Body
```json
{
  "symbol": "AAPL",
  "api_key": "pk_xxxxxxxxxxxxxxxxxxxxxxxx",
  "api_secret": "your_api_secret"
}
```

### 签名验证 (可选的高级安全)

对于高安全性需求，可以使用请求签名：

**签名计算方式:**
```
signature = HMAC-SHA256(api_secret, timestamp + nonce + request_body)
```

**请求头:**
```
X-Timestamp: 1710115200
X-Nonce: a1b2c3d4e5f6
X-Signature: 3a4b5c6d7e8f...
```

**有效期:** 请求时间戳必须在当前时间的30秒内

---

## API密钥管理

### 获取API密钥

合作商首先需要创建账户并获取API密钥。

**密钥格式:**
- **API Key**: `pk_` 前缀，32个十六进制字符
- **API Secret**: 32个十六进制字符（保管好，用于签名验证）

**创建API密钥 (由系统管理员执行):**

```bash
# 创建新用户
curl -X POST http://localhost:9000/api/admin/create_user \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Partner Name",
    "tier": "pro",
    "email": "contact@partner.com",
    "initial_days": 30,
    "recharge_type": "monthly"
  }'
```

**响应示例:**
```json
{
  "status": "ok",
  "user_id": "user_a1b2c3d4e5f6",
  "api_key": "pk_1234567890abcdef1234567890abcdef",
  "api_secret": "abcdef1234567890abcdef1234567890",
  "partner_name": "Partner Name",
  "tier": "pro",
  "balance_days": 30,
  "created_at": "2026-03-11T10:30:00"
}
```

### 密钥安全建议

1. **保管好API Secret**: 不要在代码中硬编码，使用环境变量
2. **定期轮换**: 建议每90天轮换一次密钥
3. **使用IP白名单**: 为高度敏感操作设置IP限制
4. **监控使用**: 定期检查API访问日志
5. **吊销废弃密钥**: 不再使用的密钥应立即吊销

---

## 防DDOS和速率限制

### 速率限制规则

系统采用分层速率限制策略：

| 级别 | PRO | SVIP |
|------|-----|------|
| 每秒请求数 | 10 req/s | 30 req/s |
| 每分钟请求数 | 60 req/min | 120 req/min |
| 并发连接数 | 10 | 30 |
| 每日调用限制 | 500 | 1000 |

### 限流响应

当超过速率限制时，系统返回 429 状态码：

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded: 60 requests per minute",
  "retry_after": 30
}
```

### DDoS防护

系统采用以下防护措施：

1. **IP级别的请求限制**: 每个IP地址单位时间内的最大请求数
2. **连接池管理**: 限制单个客户端的并发连接数
3. **请求签名验证**: 防止请求伪造
4. **自动黑名单**: 检测到异常行为时自动IP黑名单
5. **时间戳验证**: 防止请求重放攻击

### 处理限流

**最佳实践:**
```javascript
// JavaScript 示例
async function makeRequestWithRetry(url, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        const response = await fetch(url, {
            headers: {
                'X-API-Key': 'pk_your_api_key'
            }
        });
        
        if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After') || 30;
            console.log(`Rate limited. Waiting ${retryAfter}s...`);
            await new Promise(r => setTimeout(r, retryAfter * 1000));
            continue;
        }
        
        return response;
    }
}
```

---

## 数据接口

### 1. 搜索标的

**端点:**
```
GET /api/search?q={query}
```

**参数:**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键字（代码或名称） |
| api_key | string | 是 | API密钥 |

**示例:**
```bash
curl -X GET "http://localhost:9000/api/search?q=AAPL&api_key=pk_your_key" \
  -H "X-API-Key: pk_your_key"
```

**成功响应 (200):**
```json
{
  "status": "ok",
  "query": "AAPL",
  "results": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "type": "STOCK",
      "currency": "USD",
      "sector": "Technology"
    },
    {
      "symbol": "AAPL.L",
      "name": "Apple Inc.",
      "exchange": "LSE",
      "type": "STOCK",
      "currency": "GBP"
    }
  ],
  "count": 2
}
```

**错误响应 (400):**
```json
{
  "error": "Query required"
}
```

### 2. 获取市场数据

**端点:**
```
GET /api/market_data?symbol={symbol}&timeframe={timeframe}&days={days}
```

**参数:**
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | string | 是 | - | 标的代码（如：AAPL, BTC/USDT） |
| timeframe | string | 否 | 1d | 时间周期：1d, 4h, 1h, 15m |
| days | integer | 否 | 100 | 获取数据天数（1-365） |
| api_key | string | 是 | - | API密钥 |

**示例:**
```bash
curl -X GET "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT&timeframe=1d&days=100" \
  -H "X-API-Key: pk_your_key"
```

**成功响应 (200):**
```json
{
  "status": "ok",
  "symbol": "BTC/USDT",
  "instrument": {
    "symbol": "BTC/USDT",
    "name": "Bitcoin",
    "type": "CRYPTO",
    "exchange": "BINANCE",
    "currency": "USDT"
  },
  "current_price": 45230.50,
  "chart_data": {
    "timestamps": ["0", "1", "2", ...],
    "ohlcv": [
      ["0", 44890.0, 45120.0, 44850.0, 45100.0, 1230450000.0],
      ...
    ],
    "ma1": [null, null, 45000.5, 45020.3, ...],
    "ma2": [null, null, null, null, 44950.2, ...],
    "ma3": [null, null, null, null, null, 44900.1, ...],
    "volume": [1230450000, 1234560000, ...]
  },
  "indicators": {
    "MA1": 45020.30,
    "MA2": 44950.20,
    "MA3": 44900.10,
    "MA4": 44850.00,
    "VAR3": 65.5,
    "VAR4": 45.3
  },
  "signal": {
    "buy": false,
    "sell": true
  },
  "data_points": 100,
  "_user_tier": "pro",
  "_remaining_days": 29
}
```

**数据说明:**
- **OHLCV**: [时间戳, 开价, 最高, 最低, 收盘, 成交量]
- **MA1/MA2/MA3/MA4**: 5日/10日/20日/60日移动平均线
- **VAR3/VAR4**: 自适应波段指标（Variance Ratio）
- **signal**: 基于指标的交易信号

---

## 分析接口

### 1. 获取AI分析

**端点:**
```
POST /api/analysis
```

**请求体:**
```json
{
  "symbol": "BTC/USDT",
  "api_key": "pk_your_key"
}
```

**成功响应 (200):**
```json
{
  "status": "ok",
  "symbol": "BTC/USDT",
  "current_price": 45230.50,
  "consensus": {
    "overall_signal": "BUY",
    "consensus_score": 0.85,
    "timestamp": "2026-03-11T10:30:00",
    "entry_price": 45230.50,
    "stop_loss": 44778.00,
    "take_profit": 45537.00,
    "leverage": 5
  },
  "agents": [
    {
      "agent_name": "TechnicalAnalystAgent",
      "signal": "BUY",
      "confidence": 0.92,
      "reasoning": "短期突破向上，MA5上穿MA10，形成看涨信号"
    },
    {
      "agent_name": "MomentumAgent",
      "signal": "BUY",
      "confidence": 0.87,
      "reasoning": "RSI从超卖区反弹，MACD 柱状图转正"
    },
    {
      "agent_name": "RiskManagementAgent",
      "signal": "HOLD",
      "confidence": 0.75,
      "reasoning": "波动率处于高位，建议缩小仓位"
    }
  ],
  "agent_count": 10,
  "_user_tier": "pro",
  "_remaining_days": 29
}
```

**信号含义:**
- **BUY**: 买入信号（做多）
- **SELL**: 卖出信号（做空）
- **HOLD**: 观望信号（不交易）

**共识分数 (consensus_score):**
- 0.8-1.0: 强信号，高置信度
- 0.6-0.8: 中等信号，中等置信度
- 0.4-0.6: 弱信号，低置信度
- <0.4: 不确定，不建议交易

### 2. PRO/SVIP - 获取指标信号

**端点:**
```
POST /api/pro/signals
```

**请求体:**
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1d",
  "api_key": "pk_your_key"
}
```

**成功响应 (200):**
```json
{
  "status": "ok",
  "symbol": "BTC/USDT",
  "timeframe": "1d",
  "signal_count": 45,
  "signals": [
    {
      "time": 1710115200000,
      "price": 45120.50,
      "type": "buy",
      "text": "短买",
      "color": "#FFFF00",
      "icon": 1
    },
    {
      "time": 1710024000000,
      "price": 44890.30,
      "type": "sell_short",
      "text": "短卖",
      "color": "#00FF00",
      "icon": 2
    },
    {
      "time": 1709932800000,
      "price": 44950.00,
      "type": "stop_loss",
      "text": "止损",
      "color": "#FFFFFF",
      "icon": 2
    }
  ],
  "_user_tier": "pro",
  "_remaining_days": 29
}
```

**信号类型:**
| 类型 | 说明 | 颜色 | 图标 |
|------|------|------|------|
| buy | 买入点位 | 黄色 | ▲ |
| sell_short | 卖出点位 | 绿色 | ▼ |
| stop_loss | 止损点位 | 白色 | × |

### 3. AI对话

**端点:**
```
POST /api/chat
```

**请求体:**
```json
{
  "message": "BTC/USDT目前应该怎么操作？",
  "symbol": "BTC/USDT",
  "api_key": "pk_your_key"
}
```

**成功响应 (200):**
```json
{
  "status": "ok",
  "response": "基于当前的共识分析，BTC/USDT 显示强劲的买入信号...",
  "symbols": ["BTC/USDT"],
  "timestamp": "2026-03-11T10:30:00",
  "_user_tier": "pro",
  "_remaining_days": 29
}
```

### 4. SVIP - 鲸鱼交易监控

**端点:**
```
POST /api/svip/whale_data
```

**请求体:**
```json
{
  "symbol": "BTC/USDT",
  "top_n": 20,
  "api_key": "pk_your_key"
}
```

**成功响应 (200):**
```json
{
  "status": "ok",
  "symbol": "BTC/USDT",
  "top_traders": [
    {
      "rank": 1,
      "wallet": "3J98t1W...",
      "profit_loss": 2345000.50,
      "profit_ratio": 125.50,
      "win_rate": 68.5,
      "total_trades": 234
    }
  ],
  "whale_data": {
    "large_buy_orders": 12,
    "large_sell_orders": 8,
    "net_whale_position": "LONG",
    "long_ratio": 60.0
  },
  "timestamp": "2026-03-11T10:30:00",
  "_user_tier": "svip",
  "_remaining_days": 29
}
```

---

## 用户管理接口

### 1. 创建用户 (管理员)

**端点:**
```
POST /api/admin/create_user
```

**请求头:**
```
Authorization: Bearer admin_token
Content-Type: application/json
```

**请求体:**
```json
{
  "partner_name": "Crypto Trading Co.",
  "tier": "pro",
  "email": "api@partner.com",
  "initial_days": 30,
  "recharge_type": "monthly"
}
```

**参数说明:**
| 参数 | 值 | 说明 |
|------|-----|------|
| tier | free, pro, svip | 用户等级 |
| recharge_type | monthly, quarterly, yearly, permanent | 充值周期 |

**响应:**
```json
{
  "status": "ok",
  "user_id": "user_a1b2c3d4e5f6",
  "api_key": "pk_1234567890abcdef1234567890abcdef",
  "api_secret": "abcdef1234567890abcdef1234567890",
  "partner_name": "Crypto Trading Co.",
  "tier": "pro",
  "balance_days": 30,
  "created_at": "2026-03-11T10:30:00"
}
```

### 2. 充值用户余额

**端点:**
```
POST /api/admin/recharge
```

**请求体:**
```json
{
  "user_id": "user_a1b2c3d4e5f6",
  "amount_days": 30,
  "recharge_type": "monthly",
  "payment_method": "transfer"
}
```

**响应:**
```json
{
  "status": "ok",
  "user_id": "user_a1b2c3d4e5f6",
  "previous_balance": 5,
  "new_balance": 35,
  "amount_days": 30,
  "recharge_type": "monthly",
  "expiry_date": "2026-04-11T10:30:00",
  "record_id": "recharge_1234567890"
}
```

### 3. 查询用户信息

**端点:**
```
GET /api/user/info
```

**响应:**
```json
{
  "status": "ok",
  "user_id": "user_a1b2c3d4e5f6",
  "partner_name": "Crypto Trading Co.",
  "tier": "pro",
  "email": "api@partner.com",
  "is_active": true,
  "balance_days": 25,
  "total_charged_days": 120,
  "daily_charge_count": 95,
  "last_charge_date": "2026-03-11T10:30:00",
  "total_api_calls": 12500
}
```

---

## 错误处理

### HTTP状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | API密钥无效或缺失 |
| 403 | Forbidden | 无权限访问或余额不足 |
| 404 | Not Found | 资源不存在 |
| 429 | Too Many Requests | 超过速率限制 |
| 500 | Internal Server Error | 服务器错误 |

### 错误响应示例

**缺失API密钥 (401):**
```json
{
  "error": "Unauthorized",
  "message": "API key required. Use Authorization header or X-API-Key header"
}
```

**无效的API密钥 (401):**
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key"
}
```

**超过速率限制 (429):**
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded: 60 requests per minute",
  "retry_after": 30
}
```

**余额不足 (403):**
```json
{
  "error": "Insufficient Balance",
  "message": "User has 0 days remaining. Please recharge.",
  "remaining_days": 0
}
```

**标的不存在 (404):**
```json
{
  "error": "Could not fetch data for INVALID_SYMBOL"
}
```

---

## 使用示例

### Python 示例

```python
import requests
import json
from datetime import datetime

# API配置
API_BASE_URL = "http://localhost:9000"
API_KEY = "pk_your_api_key"

# 1. 搜索标的
def search_instruments(query):
    response = requests.get(
        f"{API_BASE_URL}/api/search",
        params={"q": query},
        headers={"X-API-Key": API_KEY}
    )
    return response.json()

# 2. 获取市场数据
def get_market_data(symbol, timeframe="1d", days=100):
    response = requests.get(
        f"{API_BASE_URL}/api/market_data",
        params={
            "symbol": symbol,
            "timeframe": timeframe,
            "days": days
        },
        headers={"X-API-Key": API_KEY}
    )
    return response.json()

# 3. 获取AI分析
def get_ai_analysis(symbol):
    response = requests.post(
        f"{API_BASE_URL}/api/analysis",
        json={"symbol": symbol},
        headers={"X-API-Key": API_KEY}
    )
    return response.json()

# 4. AI对话
def ai_chat(message, symbol):
    response = requests.post(
        f"{API_BASE_URL}/api/chat",
        json={
            "message": message,
            "symbol": symbol
        },
        headers={"X-API-Key": API_KEY}
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 搜索
    results = search_instruments("BTC")
    print(f"搜索结果: {results}")
    
    # 获取市场数据
    market_data = get_market_data("BTC/USDT")
    print(f"当前价格: {market_data['current_price']}")
    
    # 获取分析
    analysis = get_ai_analysis("BTC/USDT")
    print(f"分析信号: {analysis['consensus']['overall_signal']}")
    
    # AI对话
    response = ai_chat("BTC应该怎么操作？", "BTC/USDT")
    print(f"AI回复: {response['response']}")
```

### JavaScript 示例

```javascript
// API配置
const API_BASE_URL = "http://localhost:9000";
const API_KEY = "pk_your_api_key";

// 1. 搜索标的
async function searchInstruments(query) {
    const response = await fetch(`${API_BASE_URL}/api/search?q=${query}`, {
        headers: { "X-API-Key": API_KEY }
    });
    return response.json();
}

// 2. 获取市场数据
async function getMarketData(symbol, timeframe = "1d", days = 100) {
    const params = new URLSearchParams({
        symbol,
        timeframe,
        days
    });
    const response = await fetch(
        `${API_BASE_URL}/api/market_data?${params}`,
        { headers: { "X-API-Key": API_KEY } }
    );
    return response.json();
}

// 3. 获取AI分析
async function getAIAnalysis(symbol) {
    const response = await fetch(`${API_BASE_URL}/api/analysis`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        body: JSON.stringify({ symbol })
    });
    return response.json();
}

// 4. AI对话
async function aiChat(message, symbol) {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        body: JSON.stringify({ message, symbol })
    });
    return response.json();
}

// 使用示例
(async () => {
    // 搜索
    const results = await searchInstruments("BTC");
    console.log("搜索结果:", results);
    
    // 获取市场数据
    const marketData = await getMarketData("BTC/USDT");
    console.log("当前价格:", marketData.current_price);
    
    // 获取分析
    const analysis = await getAIAnalysis("BTC/USDT");
    console.log("分析信号:", analysis.consensus.overall_signal);
    
    // AI对话
    const response = await aiChat("BTC应该怎么操作？", "BTC/USDT");
    console.log("AI回复:", response.response);
})();
```

### cURL 示例

```bash
# 搜索标的
curl -X GET "http://localhost:9000/api/search?q=AAPL" \
  -H "X-API-Key: pk_your_key"

# 获取市场数据
curl -X GET "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT&timeframe=1d&days=100" \
  -H "X-API-Key: pk_your_key"

# 获取AI分析
curl -X POST "http://localhost:9000/api/analysis" \
  -H "X-API-Key: pk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT"}'

# AI对话
curl -X POST "http://localhost:9000/api/chat" \
  -H "X-API-Key: pk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"message":"BTC应该怎么操作？","symbol":"BTC/USDT"}'

# 创建用户 (需要admin_token)
curl -X POST "http://localhost:9000/api/admin/create_user" \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Partner Co.",
    "tier": "pro",
    "email": "api@partner.com",
    "initial_days": 30,
    "recharge_type": "monthly"
  }'
```

---

## 常见问题 (FAQ)

### Q: 如何处理API限流？
A: 当收到429状态码时，根据`Retry-After`头信息等待指定秒数后重试。建议实现指数退避算法。

### Q: API密钥泄露了怎么办？
A: 立即联系系统管理员撤销旧密钥并生成新密钥。旧密钥应立即失效。

### Q: 为什么获取某个标的的数据失败？
A: 可能原因：
1. 标的代码错误（例如：应为 BTC/USDT 而非 BTC）
2. 该标的不支持（检查支持的市场列表）
3. 数据源暂时不可用（稍后重试）

### Q: 如何优化API调用速度？
A: 
1. 使用连接池和HTTP/2
2. 批量请求而不是逐个请求
3. 启用本地缓存机制
4. 使用异步调用

### Q: 支持跨域请求吗？
A: 是的，服务器已配置CORS支持，允许浏览器跨域调用。

---

## 支持与联系

- **技术支持**: support@example.com
- **商务合作**: business@example.com
- **系统状态**: https://status.example.com
- **API更新日志**: https://changelog.example.com

---

**文档版本**: 1.0.0  
**最后更新**: 2026年3月11日  
**下一个更新**: 2026年4月11日
