# XBIT AI 投资系统 - 更新汇总

## 概述

本次更新包括完整的用户会员系统、API安全认证、防DDOS保护，以及修复了PRO版本的K线显示问题。系统现已支持向合作商提供完整的API服务。

---

## ✅ 已完成的改进

### 1. 用户会员系统 (`user_manager.py`)

**功能:**
- ✅ PRO和SVIP用户等级管理
- ✅ 按天数计算的充值机制（支持月度、季度、年度、永久充值）
- ✅ 自动每日扣费系统
- ✅ API密钥生成和管理
- ✅ 数据库持久化（SQLite）
- ✅ 用户激活/禁用功能

**关键表:**
- `users` - 用户信息和API密钥
- `balance` - 用户余额和充值统计
- `recharge_log` - 充值记录（支持不同充值类型）
- `usage_log` - 每日使用记录（自动扣费）
- `api_access_control` - API访问控制和速率限制

**用法:**
```python
from user_manager import UserManager

manager = UserManager()

# 创建PRO用户（初始30天）
user = manager.create_user(
    partner_name="Company Name",
    tier="pro",
    email="contact@company.com",
    initial_days=30,
    recharge_type="monthly"
)

# 充值用户
manager.recharge_user(user_id, amount_days=30, recharge_type="monthly")

# 获取用户信息
info = manager.get_user_info(user_id)
```

---

### 2. API安全认证 (`api_security.py`)

**功能:**
- ✅ 多种认证方式支持
  - Authorization: Bearer {api_key}
  - X-API-Key: {api_key}
  - URL参数: ?api_key={api_key}
  - POST Body中的api_key
- ✅ 请求签名验证（可选）
- ✅ 用户余额检查和自动扣费
- ✅ DDoS防护和IP级别限流
- ✅ 速率限制（分钟级别）
- ✅ IP白名单管理
- ✅ 自动黑名单机制

**认证装饰器:**
```python
@app.route('/api/endpoint', methods=['GET'])
@protect_from_ddos          # DDoS防护
@require_api_key            # API密钥认证
def api_endpoint():
    # 自动处理:
    # - 验证API密钥
    # - 检查用户余额
    # - 每日扣费
    # - 速率限制检查
    
    # 获取用户信息
    user_tier = request.user_info['tier']
    remaining_days = request.remaining_days
    
    return jsonify({...})
```

**防DDOS配置:**
```python
ddos_protection = DDoSProtection(
    max_requests_per_ip=1000,  # 每分钟最多1000请求
    time_window=60             # 时间窗口60秒
)
```

---

### 3. 修复PRO版K线显示 (`templates/pro.html`)

**问题修复:**
- ✅ 修正了K线数据接口：从 `/api/pro/signals` 改为先调用 `/api/market_data` 获取K线
- ✅ 统一了K线显示格式，与 `index.html` 保持一致
- ✅ 修复了收盘价、MA5/MA10/MA20显示
- ✅ 改进了信号卡片的格式和显示
- ✅ 修复了信号统计统计逻辑

**K线数据流程:**
```
1. 用户搜索标的 (searchInstruments)
   ↓
2. 获取市场数据 (/api/market_data) - 获取K线和指标
   ↓
3. 获取指标信号 (/api/pro/signals) - 获取信号点位
   ↓
4. 绘制K线图表和显示信号
```

**修复前后对比:**
```javascript
// ❌ 之前（错误）
drawKlineChart(signalData) {
    // 使用indicators中的指标数据作为价格数据，完全错误
    datasets.data = data.indicators.MA4.map((_, i) => i);
}

// ✅ 之后（正确）
drawKlineChart(chartData) {
    // 使用OHLCV中的收盘价作为主线
    datasets.data = chartData.ohlcv.map(c => c[4]); // c[4]是收盘价
}
```

---

### 4. API技术文档 (`API_DOCUMENTATION.md`)

**内容:**
- ✅ 完整的API参考手册
- ✅ 认证方式详解
- ✅ 所有API端点文档
  - `/api/search` - 搜索标的
  - `/api/market_data` - 获取K线和指标
  - `/api/analysis` - AI分析
  - `/api/pro/signals` - PRO指标信号
  - `/api/chat` - AI对话
  - `/api/svip/whale_data` - SVIP鲸鱼数据
  - `/api/admin/*` - 管理员接口
- ✅ 防DDOS和速率限制说明
- ✅ 错误处理文档
- ✅ Python/JavaScript/cURL示例
- ✅ 常见问题解答

**文档结构:**
```
API 技术文档
├── 概述 - 基础信息和支持市场
├── 认证与授权 - 4种认证方式
├── API密钥管理 - 创建、安全、轮换
├── 防DDOS和速率限制 - 保护机制
├── 数据接口 - 搜索、市场数据
├── 分析接口 - AI分析、信号、对话
├── 用户管理接口 - 创建用户、充值
├── 错误处理 - HTTP状态码和错误消息
├── 使用示例 - Python/JS/cURL
└── FAQ - 常见问题
```

---

### 5. 安全集成指南 (`SECURITY_INTEGRATION_GUIDE.md`)

**内容:**
- ✅ 完整的集成步骤
- ✅ 如何在app.py中添加认证
- ✅ 管理员接口示例代码
- ✅ 用户认证流程说明
- ✅ 数据库结构和操作
- ✅ 测试方法
- ✅ 安全最佳实践
- ✅ 故障排除指南

**关键章节:**
```
安全集成指南
├── 集成步骤 - 4个简单步骤
├── 用户认证流程 - 端到端流程
├── 配置参数 - 环境变量和配置
├── 数据库 - 表结构和查询
├── 测试 - 创建用户和测试API
├── 安全最佳实践 - 密钥管理、防DDOS等
└── 故障排除 - 常见问题解决
```

---

### 6. 部署指南 (`DEPLOYMENT_GUIDE.md`)

**内容:**
- ✅ 快速开始（4步启动）
- ✅ 详细配置说明
- ✅ 多种运行模式（开发、生产、Docker）
- ✅ 用户管理示例代码
- ✅ API客户端代码（Python和JavaScript）
- ✅ 监控和维护
- ✅ 性能优化建议
- ✅ 故障排除
- ✅ 升级和更新
- ✅ 安全检查清单

**快速开始:**
```bash
1. 安装依赖: pip install -r requirements.txt
2. 配置环境: cp .env.example .env
3. 启动系统: python app.py
4. 创建用户: curl -X POST ... (见文档)
```

---

### 7. 环境配置文件 (`.env.example`)

**包含项:**
- Flask配置（密钥、调试模式）
- API安全配置（管理员令牌、数据库路径）
- 服务器配置（地址、端口）
- 速率限制配置（各用户等级的限制）
- 充值配置（月度、季度、年度天数）
- 日志配置
- 数据提供者API密钥
- LLM配置
- 可选的邮件和监控配置

---

## 📊 功能对比

### 用户等级

| 功能 | FREE | PRO | SVIP |
|------|------|-----|------|
| K线数据 | ✅ | ✅ | ✅ |
| 指标信号 | ❌ | ✅ | ✅ |
| AI分析 | ❌ | ✅ | ✅ |
| AI对话 | ❌ | ✅ | ✅ |
| 鲸鱼监控 | ❌ | ❌ | ✅ |
| 每日调用限制 | 100 | 500 | 1000 |
| 每分钟限制 | 30 | 60 | 120 |
| 价格 | 免费 | 按天计费 | 按天计费 |

### 充值机制

| 类型 | 周期 | 天数 | 说明 |
|------|------|------|------|
| Monthly | 30天 | 30 | 按月充值 |
| Quarterly | 90天 | 90 | 按季度充值 |
| Yearly | 365天 | 365 | 按年充值 |
| Permanent | 永久 | 99999 | 永久会员 |
| Custom | 自定义 | N | 自定义天数 |

**扣费机制:**
- 每天自动扣费1天（无论是否使用API）
- 当用户余额≤0时，拒绝API请求
- 支持多种充值方式：转账、微信、支付宝、加密货币

---

## 🔒 安全特性

### 认证方式（4种）

1. **Bearer Token**
   ```
   Authorization: Bearer pk_xxxxx
   ```

2. **API Key Header**
   ```
   X-API-Key: pk_xxxxx
   ```

3. **URL参数**
   ```
   GET /api/endpoint?api_key=pk_xxxxx
   ```

4. **POST Body**
   ```json
   { "api_key": "pk_xxxxx" }
   ```

### 防DDOS防护（5层）

1. **IP级别限制** - 每个IP每分钟最多1000请求
2. **用户级别限制** - 按用户等级限制（PRO: 60 req/min, SVIP: 120 req/min）
3. **请求签名验证** - HMAC-SHA256签名
4. **自动黑名单** - 异常行为自动IP黑名单
5. **时间戳验证** - 防止请求重放

### 数据安全

- ✅ API Secret不会返回给客户端（仅创建时返回一次）
- ✅ 所有密钥使用SHA256加密存储
- ✅ 支持IP白名单配置
- ✅ 完整的审计日志

---

## 📝 数据库设计

### 表结构

**users** - 用户信息
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    api_key TEXT UNIQUE NOT NULL,
    api_secret TEXT NOT NULL,
    partner_name TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    email TEXT,
    created_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

**balance** - 用户余额
```sql
CREATE TABLE balance (
    balance_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    balance_days INTEGER DEFAULT 0,
    total_charged_days INTEGER DEFAULT 0,
    daily_charge_count INTEGER DEFAULT 0,
    last_charge_date TEXT
);
```

**recharge_log** - 充值记录
```sql
CREATE TABLE recharge_log (
    record_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    amount_days INTEGER NOT NULL,
    recharge_type TEXT NOT NULL,
    recharge_date TEXT NOT NULL,
    expiry_date TEXT,
    payment_method TEXT,
    status TEXT DEFAULT 'completed'
);
```

**usage_log** - 使用日志（每日扣费）
```sql
CREATE TABLE usage_log (
    usage_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    days_charged INTEGER DEFAULT 1,
    usage_date TEXT NOT NULL,
    api_calls INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP
);
```

**api_access_control** - 访问控制
```sql
CREATE TABLE api_access_control (
    control_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    api_key TEXT NOT NULL,
    ip_whitelist TEXT,
    rate_limit INTEGER DEFAULT 100,
    requests_per_minute INTEGER DEFAULT 60,
    blocked BOOLEAN DEFAULT 0,
    blocked_until TIMESTAMP
);
```

---

## 🚀 集成步骤

### 简化版（3步）

1. **导入模块**
   ```python
   from user_manager import UserManager
   from api_security import init_security, require_api_key, protect_from_ddos
   ```

2. **初始化**
   ```python
   init_security(app)
   ```

3. **添加装饰器**
   ```python
   @app.route('/api/endpoint', methods=['GET'])
   @protect_from_ddos
   @require_api_key
   def api_endpoint():
       pass
   ```

### 详细版（见 `SECURITY_INTEGRATION_GUIDE.md`）

---

## 📚 文档清单

| 文件 | 用途 | 读者 |
|------|------|------|
| `API_DOCUMENTATION.md` | API参考手册 | 开发者、合作商 |
| `SECURITY_INTEGRATION_GUIDE.md` | 安全集成指南 | 开发者、系统管理员 |
| `DEPLOYMENT_GUIDE.md` | 部署和运行指南 | 运维、系统管理员 |
| `.env.example` | 环境配置示例 | 运维 |
| 本文档 | 更新汇总 | 所有人 |

---

## 🔄 API数据流

### 典型的API调用流程

```
用户请求
  ↓
DDoS防护检查 (protect_from_ddos)
  ↓
API密钥认证 (require_api_key)
  ├─ 获取API密钥
  ├─ 验证密钥有效性
  ├─ 检查用户是否活跃
  └─ 检查用户余额
  ↓
速率限制检查 (rate_limit_check)
  ├─ 检查IP级别限制
  ├─ 检查用户级别限制
  └─ 检查并发连接数
  ↓
记录API调用 (record_api_call)
  ↓
每日扣费 (charge_daily)
  ├─ 检查是否已扣过费
  ├─ 从余额扣1天
  └─ 记录使用日志
  ↓
执行业务逻辑
  ├─ 搜索、获取数据、分析等
  └─ 返回响应数据
  ↓
响应添加用户信息
  ├─ _user_tier: 用户等级
  └─ _remaining_days: 剩余天数
  ↓
返回给用户
```

---

## 🧪 测试清单

### 创建测试用户

```bash
curl -X POST http://localhost:9000/api/admin/create_user \
  -H "Authorization: Bearer admin_token_default" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Test Partner",
    "tier": "pro",
    "email": "test@partner.com",
    "initial_days": 30,
    "recharge_type": "monthly"
  }'
```

### 测试API调用

- [ ] 使用API密钥搜索标的
- [ ] 使用API密钥获取市场数据
- [ ] 使用API密钥获取AI分析
- [ ] 验证速率限制（超过限制）
- [ ] 验证无效密钥被拒绝
- [ ] 验证余额不足被拒绝
- [ ] 验证每日自动扣费
- [ ] 验证充值功能
- [ ] 验证用户禁用后被拒绝

---

## ⚠️ 重要提醒

### 生产部署前检查清单

- [ ] 修改了默认管理员令牌（ADMIN_TOKEN）
- [ ] 修改了Flask SECRET_KEY
- [ ] 配置了HTTPS/TLS
- [ ] 修改了数据库路径到安全位置
- [ ] 备份了初始数据库
- [ ] 配置了日志轮转
- [ ] 设置了监控告警
- [ ] 测试了所有API端点
- [ ] 配置了自动备份
- [ ] 审查了所有用户权限

---

## 📞 技术支持

### 遇到问题时

1. **查看日志**
   ```bash
   tail -f investment_ai.log
   ```

2. **查看文档**
   - API文档: `API_DOCUMENTATION.md`
   - 集成指南: `SECURITY_INTEGRATION_GUIDE.md`
   - 部署指南: `DEPLOYMENT_GUIDE.md`

3. **检查数据库**
   ```bash
   sqlite3 users.db
   ```

4. **测试API**
   ```bash
   curl http://localhost:9000/health
   ```

---

## 版本信息

- **系统版本**: 1.0.0
- **更新日期**: 2026年3月11日
- **Python版本**: 3.8+
- **Flask版本**: 2.0+
- **数据库**: SQLite3

---

## 👥 相关角色

### 系统管理员
- 负责部署和运维
- 参考: `DEPLOYMENT_GUIDE.md`

### 开发者
- 集成API到应用
- 参考: `API_DOCUMENTATION.md`、`DEPLOYMENT_GUIDE.md`

### 合作商
- 使用API调用系统
- 参考: `API_DOCUMENTATION.md`

### 财务
- 管理用户充值和扣费
- 使用: `/api/admin/recharge` 端点和 `SECURITY_INTEGRATION_GUIDE.md`

---

**文档完整，系统已就绪！** ✨

如有任何问题或建议，请参考相关文档或联系技术支持。
