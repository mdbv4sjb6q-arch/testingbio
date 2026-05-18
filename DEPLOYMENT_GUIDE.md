# 部署和运行指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install openpyxl  # 用于Excel数据处理
```

### 2. 配置环境

复制配置文件模板并修改：

```bash
cp .env.example .env
# 编辑 .env 文件，修改管理员令牌和其他配置
```

### 3. 启动系统

```bash
python app.py
```

系统会在 `http://localhost:9000` 启动

### 4. 创建第一个用户

```bash
# 使用默认管理员令牌创建PRO用户
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

---

## 详细配置

### 修改管理员令牌

**重要**: 部署前必须修改默认管理员令牌！

```bash
# 在 .env 中修改
ADMIN_TOKEN=your_very_secure_token_12345678901234567890

# 或在代码中修改（api_security.py）
def verify_admin_token(token):
    admin_token = os.environ.get('ADMIN_TOKEN', 'your_new_secure_token')
    return token == admin_token
```

### 修改Flask密钥

```bash
# 生成安全的密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 在 .env 中设置
SECRET_KEY=生成的密钥值
```

### 修改数据库路径

```bash
# 默认：当前目录下的 users.db
# 可以修改为：
USER_DB_PATH=/var/lib/ai_system/users.db
```

---

## 运行模式

### 开发环境

```bash
# 开启调试模式
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### 生产环境

```bash
# 使用Gunicorn运行
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:9000 app:app

# 或使用uWSGI
pip install uwsgi
uwsgi --http :9000 --wsgi-file app.py --callable app --processes 4
```

### Docker运行

```bash
# 构建镜像
docker build -t ai-system:latest .

# 运行容器
docker run -d \
  -p 9000:9000 \
  -e ADMIN_TOKEN=your_token \
  -v $(pwd)/users.db:/app/users.db \
  ai-system:latest
```

---

## 用户管理

### 创建用户

```python
from user_manager import UserManager

manager = UserManager()

# 创建PRO用户
user = manager.create_user(
    partner_name="Company Name",
    tier="pro",
    email="contact@company.com",
    initial_days=30,
    recharge_type="monthly"
)

print(f"User ID: {user['user_id']}")
print(f"API Key: {user['api_key']}")
print(f"API Secret: {user['api_secret']}")
```

### 充值用户

```python
# 充值30天
result = manager.recharge_user(
    user_id="user_a1b2c3d4e5f6",
    amount_days=30,
    recharge_type="monthly",
    payment_method="transfer"
)

print(f"新余额: {result['new_balance']} 天")
```

### 查询用户信息

```python
user_info = manager.get_user_info("user_a1b2c3d4e5f6")

print(f"用户: {user_info['partner_name']}")
print(f"等级: {user_info['tier']}")
print(f"余额: {user_info['balance_days']} 天")
print(f"总充值: {user_info['total_charged_days']} 天")
```

---

## API使用

### Python客户端示例

```python
import requests
import os

# 配置
API_URL = "http://localhost:9000"
API_KEY = "pk_your_api_key"

def search(query):
    """搜索标的"""
    resp = requests.get(
        f"{API_URL}/api/search?q={query}",
        headers={"X-API-Key": API_KEY}
    )
    return resp.json()

def get_market_data(symbol):
    """获取市场数据"""
    resp = requests.get(
        f"{API_URL}/api/market_data?symbol={symbol}&days=100",
        headers={"X-API-Key": API_KEY}
    )
    return resp.json()

def get_analysis(symbol):
    """获取AI分析"""
    resp = requests.post(
        f"{API_URL}/api/analysis",
        json={"symbol": symbol},
        headers={"X-API-Key": API_KEY}
    )
    return resp.json()

def chat(message, symbol):
    """AI对话"""
    resp = requests.post(
        f"{API_URL}/api/chat",
        json={"message": message, "symbol": symbol},
        headers={"X-API-Key": API_KEY}
    )
    return resp.json()

# 使用
if __name__ == "__main__":
    # 搜索
    results = search("BTC")
    print(f"搜索结果: {results}")
    
    # 获取市场数据
    data = get_market_data("BTC/USDT")
    print(f"当前价格: {data['current_price']}")
    
    # 获取分析
    analysis = get_analysis("BTC/USDT")
    print(f"信号: {analysis['consensus']['overall_signal']}")
    
    # AI对话
    response = chat("BTC应该怎么操作？", "BTC/USDT")
    print(f"AI: {response['response']}")
```

### JavaScript客户端示例

```javascript
const API_URL = "http://localhost:9000";
const API_KEY = "pk_your_api_key";

// 通用的API调用函数
async function apiCall(method, endpoint, body = null) {
    const options = {
        method,
        headers: {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, options);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "API call failed");
    }
    
    return response.json();
}

// API功能函数
async function search(query) {
    return apiCall("GET", `/api/search?q=${query}`);
}

async function getMarketData(symbol) {
    return apiCall("GET", `/api/market_data?symbol=${symbol}&days=100`);
}

async function getAnalysis(symbol) {
    return apiCall("POST", "/api/analysis", { symbol });
}

async function chat(message, symbol) {
    return apiCall("POST", "/api/chat", { message, symbol });
}

// 使用示例
(async () => {
    try {
        // 搜索
        const results = await search("BTC");
        console.log("搜索结果:", results);
        
        // 获取市场数据
        const data = await getMarketData("BTC/USDT");
        console.log("当前价格:", data.current_price);
        
        // 获取分析
        const analysis = await getAnalysis("BTC/USDT");
        console.log("信号:", analysis.consensus.overall_signal);
        
        // AI对话
        const response = await chat("BTC应该怎么操作？", "BTC/USDT");
        console.log("AI:", response.response);
    } catch (error) {
        console.error("Error:", error.message);
    }
})();
```

---

## 监控和维护

### 检查系统健康状态

```bash
curl http://localhost:9000/health
```

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-11T10:30:00",
  "providers": ["itick", "yfinance", "ccxt_binance", "cmc", "massive"],
  "llm": "initialized"
}
```

### 查看日志

```bash
# 实时日志
tail -f investment_ai.log

# 最后100行
tail -100 investment_ai.log

# 搜索错误
grep ERROR investment_ai.log

# 搜索警告
grep WARNING investment_ai.log
```

### 数据库维护

```bash
# 备份数据库
cp users.db users.db.backup.$(date +%Y%m%d)

# 查看用户列表
sqlite3 users.db "SELECT user_id, partner_name, tier, is_active, balance_days FROM users;"

# 查看使用情况
sqlite3 users.db "SELECT DATE(created_at), COUNT(*) FROM usage_log GROUP BY DATE(created_at);"

# 清理旧数据（保留90天）
sqlite3 users.db "DELETE FROM usage_log WHERE created_at < datetime('now', '-90 days');"
```

---

## 性能优化

### 1. 启用缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_market_data_cached(symbol, timeframe):
    # 缓存市场数据
    pass
```

### 2. 异步处理

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

# 异步获取多个标的的数据
futures = [executor.submit(get_market_data, symbol) for symbol in symbols]
results = [f.result() for f in futures]
```

### 3. 数据库连接池

```python
import sqlite3

class DBConnectionPool:
    def __init__(self, db_path, pool_size=5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = [
            sqlite3.connect(db_path) 
            for _ in range(pool_size)
        ]
        self.index = 0
    
    def get_connection(self):
        conn = self.connections[self.index % self.pool_size]
        self.index += 1
        return conn
```

---

## 故障排除

### 问题：无法连接到数据库

```bash
# 检查数据库文件
ls -la users.db

# 检查权限
chmod 644 users.db

# 重新初始化
rm users.db  # 警告：会删除所有用户数据
python -c "from user_manager import UserManager; UserManager()"
```

### 问题：API密钥无效

```bash
# 检查用户
sqlite3 users.db "SELECT user_id, is_active, api_key FROM users WHERE api_key='pk_your_key';"

# 如果用户不活跃，激活它
sqlite3 users.db "UPDATE users SET is_active=1 WHERE user_id='user_xxx';"
```

### 问题：速度很慢

```bash
# 检查日志中的性能警告
grep "slow\|timeout" investment_ai.log

# 检查数据库连接
sqlite3 users.db ".tables"

# 优化查询（添加索引）
sqlite3 users.db "CREATE INDEX idx_user_api_key ON users(api_key);"
sqlite3 users.db "CREATE INDEX idx_usage_user ON usage_log(user_id, usage_date);"
```

---

## 升级和更新

### 备份现有数据

```bash
# 完整备份
cp users.db users.db.backup.latest

# 导出用户数据
sqlite3 users.db ".mode csv" ".output users_backup.csv" "SELECT * FROM users;"
```

### 更新代码

```bash
# 从Git拉取最新代码
git pull origin main

# 安装新的依赖
pip install -r requirements.txt --upgrade

# 重启系统
# 如果使用Gunicorn: supervisorctl restart ai_system
# 如果使用Docker: docker restart ai-system-container
```

### 数据库升级

```bash
# 检查当前数据库版本
sqlite3 users.db "PRAGMA user_version;"

# 如需升级，先备份
cp users.db users.db.backup

# 运行迁移脚本（如果有）
python db_migration.py
```

---

## 安全检查清单

- [ ] 修改了默认管理员令牌
- [ ] 修改了Flask SECRET_KEY
- [ ] 生成了安全的API密钥
- [ ] 配置了HTTPS/TLS
- [ ] 启用了日志审计
- [ ] 定期备份数据库
- [ ] 监控API使用情况
- [ ] 实施了IP白名单（如需要）
- [ ] 定期更新依赖

---

## 联系支持

如有问题，请：
1. 查看 `investment_ai.log`
2. 阅读 `API_DOCUMENTATION.md`
3. 参考 `SECURITY_INTEGRATION_GUIDE.md`
4. 检查本文档的故障排除部分

---

**文档版本**: 1.0.0  
**最后更新**: 2026年3月11日
