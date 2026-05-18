# API 快速参考卡 (Cheat Sheet)

## 认证

```bash
# 使用Header认证
curl -H "X-API-Key: pk_your_key" http://localhost:9000/api/endpoint

# 使用Bearer Token
curl -H "Authorization: Bearer pk_your_key" http://localhost:9000/api/endpoint

# 使用URL参数
curl http://localhost:9000/api/endpoint?api_key=pk_your_key
```

## 搜索

```bash
curl "http://localhost:9000/api/search?q=BTC" -H "X-API-Key: pk_your_key"
```

## 市场数据

```bash
# 获取100天的日线数据
curl "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT&days=100" \
  -H "X-API-Key: pk_your_key"

# 获取4小时数据
curl "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT&timeframe=4h&days=100" \
  -H "X-API-Key: pk_your_key"
```

## AI分析

```bash
curl -X POST http://localhost:9000/api/analysis \
  -H "X-API-Key: pk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT"}'
```

## PRO信号

```bash
curl -X POST http://localhost:9000/api/pro/signals \
  -H "X-API-Key: pk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT","timeframe":"1d"}'
```

## AI对话

```bash
curl -X POST http://localhost:9000/api/chat \
  -H "X-API-Key: pk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"message":"BTC应该怎么操作？","symbol":"BTC/USDT"}'
```

## 管理操作

### 创建用户

```bash
curl -X POST http://localhost:9000/api/admin/create_user \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name":"Company",
    "tier":"pro",
    "initial_days":30
  }'
```

### 充值用户

```bash
curl -X POST http://localhost:9000/api/admin/recharge \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"user_xxx",
    "amount_days":30,
    "recharge_type":"monthly"
  }'
```

## Python使用

```python
import requests

API_KEY = "pk_your_key"
headers = {"X-API-Key": API_KEY}

# 搜索
r = requests.get("http://localhost:9000/api/search?q=BTC", headers=headers)
print(r.json())

# 市场数据
r = requests.get(
    "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT&days=100",
    headers=headers
)
data = r.json()
print(f"价格: {data['current_price']}")
print(f"剩余: {data['_remaining_days']} 天")

# AI分析
r = requests.post(
    "http://localhost:9000/api/analysis",
    json={"symbol": "BTC/USDT"},
    headers=headers
)
analysis = r.json()
print(f"信号: {analysis['consensus']['overall_signal']}")
print(f"信心度: {analysis['consensus']['consensus_score']*100:.0f}%")

# 对话
r = requests.post(
    "http://localhost:9000/api/chat",
    json={"message": "BTC应该怎么操作？", "symbol": "BTC/USDT"},
    headers=headers
)
print(r.json()['response'])
```

## JavaScript使用

```javascript
const API_KEY = "pk_your_key";

async function api(method, path, body = null) {
    const opts = {
        method,
        headers: {"X-API-Key": API_KEY}
    };
    if (body) {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(body);
    }
    return fetch(`http://localhost:9000${path}`, opts).then(r => r.json());
}

// 搜索
api("GET", "/api/search?q=BTC").then(console.log);

// 市场数据
api("GET", "/api/market_data?symbol=BTC%2FUSDT&days=100")
    .then(d => console.log(`价格: ${d.current_price}`));

// AI分析
api("POST", "/api/analysis", {symbol: "BTC/USDT"})
    .then(d => console.log(`信号: ${d.consensus.overall_signal}`));

// 对话
api("POST", "/api/chat", {
    message: "BTC应该怎么操作？",
    symbol: "BTC/USDT"
}).then(d => console.log(d.response));
```

## 错误处理

```python
import requests

def safe_api_call(method, url, **kwargs):
    try:
        r = requests.request(method, url, **kwargs)
        
        if r.status_code == 401:
            print("❌ API密钥无效")
            return None
        elif r.status_code == 403:
            print("❌ 余额不足，需要充值")
            return None
        elif r.status_code == 429:
            print("❌ 请求过于频繁，请稍后重试")
            return None
        elif r.status_code == 404:
            print("❌ 标的或资源不存在")
            return None
        elif r.status_code >= 500:
            print("❌ 服务器错误")
            return None
        
        return r.json()
    
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

# 使用
data = safe_api_call("GET", 
    "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT",
    headers={"X-API-Key": "pk_your_key"}
)
if data:
    print(f"成功: {data}")
```

## 数据库查询

```bash
# 所有用户
sqlite3 users.db "SELECT user_id, partner_name, tier, balance_days FROM users;"

# 单个用户
sqlite3 users.db "SELECT * FROM users WHERE api_key='pk_xxx';"

# 充值记录
sqlite3 users.db "SELECT * FROM recharge_log WHERE user_id='user_xxx' ORDER BY recharge_date DESC;"

# 使用日志
sqlite3 users.db "SELECT * FROM usage_log WHERE user_id='user_xxx' ORDER BY created_at DESC LIMIT 10;"

# 更新用户余额
sqlite3 users.db "UPDATE balance SET balance_days=100 WHERE user_id='user_xxx';"

# 激活/禁用用户
sqlite3 users.db "UPDATE users SET is_active=1 WHERE user_id='user_xxx';"
```

## 常见问题快速答案

| 问题 | 答案 |
|------|------|
| 如何创建用户？ | 使用 `/api/admin/create_user` 端点 |
| API密钥在哪里？ | 创建用户时返回 |
| 如何充值？ | 使用 `/api/admin/recharge` 端点 |
| 为什么被拒绝？ | 检查密钥、余额、速率限制 |
| 如何查看剩余天数？ | 响应中的 `_remaining_days` |
| 支持哪些市场？ | 外汇、美股、港股、数字货币等 |
| 如何获取信号？ | 使用 `/api/pro/signals` 端点 |
| 如何进行AI对话？ | 使用 `/api/chat` 端点 |

## 信号说明

### 信号类型

- **BUY** - 买入信号（做多）
- **SELL** - 卖出信号（做空）
- **HOLD** - 观望信号（不交易）

### 信心度

- 🟢 80-100% - 强信号
- 🟡 60-80% - 中等信号
- 🔴 40-60% - 弱信号
- ⚫ <40% - 不确定

## 用户等级限制

| 限制 | FREE | PRO | SVIP |
|------|------|-----|------|
| 每分钟请求 | 30 | 60 | 120 |
| 每天调用 | 100 | 500 | 1000 |
| 并发连接 | 5 | 10 | 30 |
| 扣费 | 否 | 是 | 是 |

## 调试命令

```bash
# 检查系统状态
curl http://localhost:9000/health

# 测试API密钥
curl -H "X-API-Key: pk_your_key" http://localhost:9000/api/search?q=BTC

# 查看日志
tail -f investment_ai.log

# 查看数据库
sqlite3 users.db ".tables"

# 备份数据库
cp users.db users.db.backup.$(date +%Y%m%d)
```

## 环境变量

```bash
# 管理员令牌
export ADMIN_TOKEN=your_token

# Flask密钥
export SECRET_KEY=your_key

# 数据库路径
export USER_DB_PATH=./users.db

# 服务器配置
export SERVER_HOST=0.0.0.0
export SERVER_PORT=9000
```

## 时间周期

```
1m   - 1分钟
5m   - 5分钟
15m  - 15分钟
1h   - 1小时
4h   - 4小时
1d   - 1天（日线）
1w   - 1周（周线）
1M   - 1个月（月线）
```

## 市场代码示例

```
美股:    AAPL, MSFT, GOOGL, AMZN, TSLA
港股:    0700.HK (腾讯), 9988.HK (阿里)
数字货币: BTC/USDT, ETH/USDT, XRP/USDT
外汇:    EURUSD, GBPUSD, USDJPY
商品:    GOLD, OIL, SILVER
指数:    SPX500, HSI, SSE
```

---

快速参考完成！打印此页面或收藏以供快速查阅。📋
