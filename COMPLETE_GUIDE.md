# XBIT AI 投资系统 - 完整指南

## 🎯 项目概述

XBIT AI 投资系统是一个专业的量化交易分析平台，支持向全球金融市场分析能力授权给商业合作伙伴。系统采用本地LLM（Deep Mind Trading Model）和多Agent共识决策，提供专业级的市场分析和交易信号。

### 核心特性

✅ **多市场支持** - 外汇、美股、港股、数字货币、指数、大宗商品  
✅ **AI分析** - 本地LLM + 10个专业Agent的共识决策  
✅ **K线可视化** - 实时K线、均线、指标、交易信号标注  
✅ **用户等级** - FREE (免费) / PRO (按天计费) / SVIP (按天计费)  
✅ **会员系统** - 灵活的充值机制，支持月度/季度/年度/永久  
✅ **API服务** - 完整的RESTful API供合作商集成  
✅ **安全认证** - API密钥认证、签名验证、防DDOS保护  
✅ **管理后台** - 用户管理、充值管理、数据分析  

---

## 📁 项目结构

```
AI/
├── app.py                          # 主应用程序
├── user_manager.py                 # 用户会员管理系统 ⭐ NEW
├── api_security.py                 # API安全认证模块 ⭐ NEW
├── technical_indicators.py         # 技术指标计算
├── technical_indicators.py         # 技术指标计算
├── ai_agents.py                    # 多Agent决策系统
├── llama_wrapper.py                # 本地LLM接口
├── models.py                       # 数据模型
├── config.py                       # 配置文件
├── *.py                            # 数据提供者 (CCXT, Yfinance, iTick等)
│
├── templates/
│   ├── index.html                  # 免费版首页
│   ├── pro.html                    # PRO版 ⭐ FIXED
│   └── svip.html                   # SVIP版
│
├── core/
│   ├── orchestrator.py             # Agent编排器
│   ├── agents/                     # Agent实现
│   ├── data/                       # 数据层
│   ├── config/                     # 配置文件
│   ├── dmind-trading-merged/       # 本地LLM模型
│   └── llama.cpp/                  # LLM推理引擎
│
├── bridge/
│   └── typescript/                 # TypeScript桥接
│
├── 文档/ ⭐ NEW
│   ├── API_DOCUMENTATION.md        # API参考手册
│   ├── SECURITY_INTEGRATION_GUIDE.md # 安全集成指南
│   ├── DEPLOYMENT_GUIDE.md         # 部署和运行指南
│   ├── UPDATES_SUMMARY.md          # 本次更新汇总
│   └── .env.example                # 环境配置示例
│
├── requirements.txt                # Python依赖
├── Dockerfile                      # Docker镜像
├── docker-compose.yml              # Docker Compose配置
└── README.md                       # 项目说明
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 如需Excel支持（鲸鱼数据）
pip install openpyxl
```

### 2. 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件（修改管理员令牌等）
nano .env
```

### 3. 启动系统

```bash
# 运行Flask应用
python app.py

# 或使用Gunicorn（生产环境）
gunicorn -w 4 -b 0.0.0.0:9000 app:app
```

系统会在 `http://localhost:9000` 启动

### 4. 验证系统

```bash
# 检查系统健康状态
curl http://localhost:9000/health

# 访问首页
curl http://localhost:9000/
```

---

## 👤 用户系统

### 用户等级对比

| 功能 | FREE | PRO | SVIP |
|------|------|-----|------|
| K线数据 | ✅ | ✅ | ✅ |
| 技术指标 | ❌ | ✅ | ✅ |
| AI分析 | ❌ | ✅ | ✅ |
| AI对话 | ❌ | ✅ | ✅ |
| 鲸鱼监控 | ❌ | ❌ | ✅ |
| 每日调用限制 | 100 | 500 | 1000 |
| 每分钟限制 | 30 | 60 | 120 |
| 价格 | 免费 | 按天计费 | 按天计费 |

### 创建用户

```bash
# 创建PRO用户
curl -X POST http://localhost:9000/api/admin/create_user \
  -H "Authorization: Bearer admin_token_default" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Partner Name",
    "tier": "pro",
    "email": "contact@partner.com",
    "initial_days": 30,
    "recharge_type": "monthly"
  }'

# 响应包含API密钥
{
  "status": "ok",
  "user_id": "user_a1b2c3d4e5f6",
  "api_key": "pk_1234567890abcdef...",
  "api_secret": "abcdef1234567890...",
  "balance_days": 30
}
```

### 充值用户

```bash
# 充值30天
curl -X POST http://localhost:9000/api/admin/recharge \
  -H "Authorization: Bearer admin_token_default" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_a1b2c3d4e5f6",
    "amount_days": 30,
    "recharge_type": "monthly",
    "payment_method": "transfer"
  }'
```

---

## 🔐 API认证

### 认证方式

四种支持的认证方式：

#### 1. Bearer Token (推荐)
```bash
curl -H "Authorization: Bearer pk_your_api_key" \
  http://localhost:9000/api/market_data?symbol=AAPL
```

#### 2. API Key Header
```bash
curl -H "X-API-Key: pk_your_api_key" \
  http://localhost:9000/api/market_data?symbol=AAPL
```

#### 3. URL参数
```bash
curl http://localhost:9000/api/market_data?symbol=AAPL&api_key=pk_your_api_key
```

#### 4. POST Body
```bash
curl -X POST http://localhost:9000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "api_key": "pk_your_api_key"
  }'
```

### 自动功能

当使用API密钥进行请求时，系统自动执行：

1. ✅ **验证密钥** - 检查API密钥的有效性
2. ✅ **检查余额** - 确保用户有足够的天数
3. ✅ **DDoS防护** - 检查请求频率是否超限
4. ✅ **速率限制** - 按用户等级限制请求速度
5. ✅ **每日扣费** - 每天自动扣1天（如未扣过）
6. ✅ **返回剩余信息** - 响应中包含剩余天数和用户等级

---

## 📚 API接口

### 搜索接口

```bash
GET /api/search?q=AAPL
```

### 市场数据

```bash
GET /api/market_data?symbol=BTC/USDT&timeframe=1d&days=100
```

**返回:** K线数据、指标、当前价格

### AI分析

```bash
POST /api/analysis
{ "symbol": "BTC/USDT" }
```

**返回:** 10个Agent的分析、综合信号、信心度、交易参数

### PRO - 指标信号

```bash
POST /api/pro/signals
{ "symbol": "BTC/USDT", "timeframe": "1d" }
```

**返回:** K线上的买卖点、止损点、信号统计

### AI对话

```bash
POST /api/chat
{ "message": "BTC应该怎么操作？", "symbol": "BTC/USDT" }
```

**返回:** AI回复（基于实时市场分析）

### SVIP - 鲸鱼监控

```bash
POST /api/svip/whale_data
{ "symbol": "BTC/USDT" }
```

**返回:** 大户交易数据、赚钱排行、多空比例

---

## 🧪 测试

### Python示例

```python
import requests

API_KEY = "pk_your_api_key"
headers = {"X-API-Key": API_KEY}

# 搜索
r = requests.get("http://localhost:9000/api/search?q=BTC", headers=headers)
print(r.json())

# 获取市场数据
r = requests.get(
    "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT&days=100",
    headers=headers
)
print(f"Current price: {r.json()['current_price']}")

# 获取AI分析
r = requests.post(
    "http://localhost:9000/api/analysis",
    json={"symbol": "BTC/USDT"},
    headers=headers
)
print(f"Signal: {r.json()['consensus']['overall_signal']}")
```

### JavaScript示例

```javascript
const API_KEY = "pk_your_api_key";

async function fetchAPI(method, endpoint, body = null) {
    const options = {
        method,
        headers: {"X-API-Key": API_KEY}
    };
    if (body) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }
    return fetch(`http://localhost:9000${endpoint}`, options)
        .then(r => r.json());
}

// 搜索
fetchAPI("GET", "/api/search?q=BTC").then(console.log);

// 市场数据
fetchAPI("GET", "/api/market_data?symbol=BTC%2FUSDT")
    .then(d => console.log(`Price: ${d.current_price}`));

// AI分析
fetchAPI("POST", "/api/analysis", {symbol: "BTC/USDT"})
    .then(d => console.log(`Signal: ${d.consensus.overall_signal}`));
```

---

## 📖 完整文档

### 给开发者

**API_DOCUMENTATION.md** - 完整的API参考手册
- 所有API端点详细说明
- 请求和响应示例
- 错误处理
- Python/JavaScript/cURL示例
- FAQ

### 给系统管理员

**SECURITY_INTEGRATION_GUIDE.md** - 安全集成指南
- 如何在app.py中添加认证
- 用户认证流程
- 数据库操作
- 测试方法
- 安全最佳实践

**DEPLOYMENT_GUIDE.md** - 部署和运行指南
- 快速开始
- 详细配置
- 多种运行模式（开发、生产、Docker）
- 用户管理示例
- 监控和维护
- 故障排除

### 给所有人

**UPDATES_SUMMARY.md** - 本次更新汇总
- 完成的改进清单
- 功能对比
- 数据库设计
- 文档清单
- 检查清单

---

## 🔧 故障排除

### API密钥无效

```python
from user_manager import UserManager

manager = UserManager()
valid, user_info = manager.verify_api_key("pk_your_key")
print(f"Valid: {valid}")
print(f"User: {user_info}")
```

### 查看用户信息

```bash
sqlite3 users.db "SELECT user_id, partner_name, tier, balance_days FROM users;"
```

### 查看使用日志

```bash
sqlite3 users.db "SELECT * FROM usage_log ORDER BY created_at DESC LIMIT 20;"
```

### 重置数据库

```bash
# 备份现有数据库
cp users.db users.db.backup

# 删除并重新初始化
rm users.db
python -c "from user_manager import UserManager; UserManager()"
```

---

## ⚙️ 配置参数

关键配置在 `.env` 文件中：

```bash
# 管理员令牌（用于创建用户、充值）
ADMIN_TOKEN=your_secure_token

# Flask密钥
SECRET_KEY=your_secret_key

# 数据库
USER_DB_PATH=./users.db

# 服务器
SERVER_HOST=0.0.0.0
SERVER_PORT=9000

# 速率限制
RATE_LIMIT_PRO=60
RATE_LIMIT_SVIP=120
```

详见 `.env.example`

---

## 🔒 安全建议

✅ **必须做:**
- 修改默认管理员令牌
- 修改Flask SECRET_KEY
- 为每个合作商创建单独的API密钥
- 定期备份数据库
- 监控API使用日志

❌ **不应该做:**
- 在代码中硬编码API密钥
- 在Git中提交 `.env` 文件
- 将API Secret分享给不信任的第三方
- 使用简单的管理员令牌

---

## 📞 技术支持

### 查看日志

```bash
tail -f investment_ai.log
```

### 检查系统状态

```bash
curl http://localhost:9000/health
```

### 常见问题

**Q: 如何处理API限流？**  
A: 根据响应头的 `Retry-After` 等待后重试

**Q: API密钥泄露了怎么办？**  
A: 立即联系管理员，吊销旧密钥生成新密钥

**Q: 支持哪些市场？**  
A: 外汇、美股、港股、数字货币、指数、大宗商品

**Q: 如何优化API性能？**  
A: 使用连接池、异步调用、本地缓存

---

## 📝 更新历史

### v1.0.0 (2026-03-11) ⭐ 当前版本

**新增功能:**
- ✅ 完整的用户会员系统 (PRO/SVIP)
- ✅ API密钥认证系统
- ✅ 防DDOS和速率限制
- ✅ 自动每日扣费
- ✅ 灵活的充值机制

**修复问题:**
- ✅ PRO版K线显示错误
- ✅ 信号统计计算错误
- ✅ API文档缺失

**新增文档:**
- ✅ API_DOCUMENTATION.md
- ✅ SECURITY_INTEGRATION_GUIDE.md
- ✅ DEPLOYMENT_GUIDE.md
- ✅ UPDATES_SUMMARY.md

---

## 📦 依赖

### 核心依赖
- Flask 2.0+
- pandas
- numpy
- requests

### 数据提供者
- CCXT - 加密货币交易所
- yfinance - Yahoo Finance
- iTick - 行情数据
- CoinMarketCap API

### LLM
- llama-cpp-python - LLM推理

详见 `requirements.txt`

---

## 👥 角色和权限

| 角色 | 权限 | 主要接口 |
|------|------|---------|
| **自由用户** | 搜索、K线数据 | `/api/search`, `/api/market_data` |
| **PRO用户** | + 指标信号、AI分析、对话 | + `/api/pro/signals`, `/api/analysis`, `/api/chat` |
| **SVIP用户** | + 鲸鱼监控 | + `/api/svip/whale_data` |
| **管理员** | 用户管理、充值 | `/api/admin/*` |

---

## 🎓 学习资源

1. **快速了解** → 本README
2. **API使用** → `API_DOCUMENTATION.md`
3. **系统集成** → `SECURITY_INTEGRATION_GUIDE.md`
4. **部署运维** → `DEPLOYMENT_GUIDE.md`
5. **更新信息** → `UPDATES_SUMMARY.md`

---

## 📄 许可证

内部使用，版权所有。

---

## 📞 联系方式

- 技术支持: support@example.com
- 商务合作: business@example.com
- 系统状态: https://status.example.com

---

**系统已准备好投入生产！** 🚀

最后更新: 2026年3月11日  
版本: 1.0.0
