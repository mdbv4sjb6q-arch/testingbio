# 安全集成指南

## 概述

本项目已创建了完整的用户会员系统和API安全认证模块：
- `user_manager.py`: 用户会员管理系统
- `api_security.py`: API认证和防DDOS模块

本文档说明如何在 `app.py` 中集成这些模块。

---

## 集成步骤

### 1. 在app.py中添加导入

在 `app.py` 的导入部分（约第35行）添加：

```python
from user_manager import UserManager
from api_security import init_security, require_api_key, protect_from_ddos, DDoSProtection
```

### 2. 初始化安全模块

在 `app = Flask(__name__)` 后添加（约第47行）：

```python
# 初始化安全模块
init_security(app)
logger.info("✓ API security initialized")
```

### 3. 为现有API端点添加认证

#### 示例1：需要认证的数据接口

```python
@app.route('/api/market_data', methods=['GET'])
@protect_from_ddos  # 防DDOS
@require_api_key    # 需要API密钥认证
def api_market_data():
    """获取市场数据"""
    # 现有代码保持不变
    # request.user_info 包含用户信息
    # request.remaining_days 包含剩余天数
    ...
```

#### 示例2：分析接口

```python
@app.route('/api/analysis', methods=['POST'])
@protect_from_ddos
@require_api_key
def api_analysis():
    """获取AI分析"""
    ...
```

### 4. 添加新的管理员接口

在app.py末尾（在 `if __name__ == '__main__':` 之前）添加：

```python
# ==================== 管理员接口 ====================

def verify_admin_token(token):
    """验证管理员令牌"""
    # 从环境变量或配置读取
    admin_token = os.environ.get('ADMIN_TOKEN', 'admin_token_default')
    return token == admin_token

@app.route('/api/admin/create_user', methods=['POST'])
def admin_create_user():
    """创建新用户"""
    # 验证管理员令牌
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Admin token required'}), 401
    
    token = auth_header[7:]
    if not verify_admin_token(token):
        return jsonify({'error': 'Invalid admin token'}), 401
    
    try:
        data = request.get_json()
        partner_name = data.get('partner_name')
        tier = data.get('tier', 'pro')
        email = data.get('email')
        initial_days = data.get('initial_days', 30)
        recharge_type = data.get('recharge_type', 'monthly')
        
        if not partner_name:
            return jsonify({'error': 'partner_name required'}), 400
        
        user_manager = UserManager()
        result = user_manager.create_user(
            partner_name=partner_name,
            tier=tier,
            email=email,
            initial_days=initial_days,
            recharge_type=recharge_type
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/recharge', methods=['POST'])
def admin_recharge():
    """充值用户余额"""
    # 验证管理员令牌
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Admin token required'}), 401
    
    token = auth_header[7:]
    if not verify_admin_token(token):
        return jsonify({'error': 'Invalid admin token'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        amount_days = data.get('amount_days')
        recharge_type = data.get('recharge_type', 'manual')
        payment_method = data.get('payment_method', 'transfer')
        
        if not user_id or not amount_days:
            return jsonify({'error': 'user_id and amount_days required'}), 400
        
        user_manager = UserManager()
        result = user_manager.recharge_user(
            user_id=user_id,
            amount_days=amount_days,
            recharge_type=recharge_type,
            payment_method=payment_method
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Failed to recharge user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/info', methods=['GET'])
@require_api_key
def user_info():
    """获取用户信息"""
    try:
        user_manager = UserManager()
        user_info = user_manager.get_user_info(request.user_info['user_id'])
        
        if not user_info:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'status': 'ok',
            **user_info,
            '_user_tier': request.user_info['tier'],
            '_remaining_days': request.remaining_days
        })
    
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## 用户认证流程

### 1. 合作商获取API密钥

**管理员操作:**
```bash
curl -X POST http://localhost:9000/api/admin/create_user \
  -H "Authorization: Bearer admin_token_default" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Partner Trading Co.",
    "tier": "pro",
    "email": "api@partner.com",
    "initial_days": 30,
    "recharge_type": "monthly"
  }'
```

**返回结果:**
```json
{
  "status": "ok",
  "user_id": "user_a1b2c3d4e5f6",
  "api_key": "pk_1234567890abcdef1234567890abcdef",
  "api_secret": "abcdef1234567890abcdef1234567890",
  "partner_name": "Partner Trading Co.",
  "tier": "pro",
  "balance_days": 30,
  "created_at": "2026-03-11T10:30:00"
}
```

### 2. 合作商使用API

```bash
# 使用Header认证
curl -X GET "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT" \
  -H "X-API-Key: pk_1234567890abcdef1234567890abcdef"
```

### 3. 系统自动扣费

当合作商调用API时，系统会：
1. 验证API密钥
2. 检查用户余额
3. 检查速率限制
4. **每天自动扣费1天**（如果还没有扣过）
5. 返回API响应和剩余天数

### 4. 充值管理

**管理员充值:**
```bash
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

## 配置参数

### 环境变量

在`.env`或系统环境变量中设置：

```bash
# 管理员令牌（用于创建用户和充值）
ADMIN_TOKEN=your_secure_admin_token_here

# 数据库路径
USER_DB_PATH=./users.db

# Flask安全密钥
SECRET_KEY=your_flask_secret_key_here
```

### 速率限制配置

在`api_security.py`中修改：

```python
# DDoS防护配置
ddos_protection = DDoSProtection(
    max_requests_per_ip=1000,  # 每IP每分钟最大请求数
    time_window=60              # 时间窗口（秒）
)
```

---

## 数据库

### 自动创建的表

运行系统时，`UserManager`会自动创建以下表：

1. **users** - 用户信息
2. **balance** - 用户余额和充值信息
3. **recharge_log** - 充值记录
4. **usage_log** - 每日使用记录（用于扣费）
5. **api_access_control** - API访问控制（速率限制）

### 查看数据库

```bash
# 查看用户信息
sqlite3 users.db "SELECT user_id, partner_name, tier, is_active FROM users;"

# 查看余额
sqlite3 users.db "SELECT user_id, tier, balance_days, last_charge_date FROM balance;"

# 查看充值记录
sqlite3 users.db "SELECT * FROM recharge_log ORDER BY recharge_date DESC LIMIT 10;"

# 查看使用日志
sqlite3 users.db "SELECT * FROM usage_log ORDER BY created_at DESC LIMIT 10;"
```

---

## 测试

### 1. 创建测试用户

```python
from user_manager import UserManager

manager = UserManager()

# 创建PRO用户
result = manager.create_user(
    partner_name="Test Partner",
    tier="pro",
    email="test@partner.com",
    initial_days=30,
    recharge_type="monthly"
)

print(f"API Key: {result['api_key']}")
print(f"API Secret: {result['api_secret']}")
```

### 2. 测试API调用

```python
import requests

API_KEY = "pk_your_test_key"

# 测试搜索
response = requests.get(
    "http://localhost:9000/api/search?q=BTC",
    headers={"X-API-Key": API_KEY}
)
print(response.json())

# 测试市场数据
response = requests.get(
    "http://localhost:9000/api/market_data?symbol=BTC%2FUSDT",
    headers={"X-API-Key": API_KEY}
)
print(response.json())
```

### 3. 测试认证失败

```bash
# 没有API密钥
curl http://localhost:9000/api/market_data?symbol=BTC%2FUSDT

# 无效的API密钥
curl -H "X-API-Key: invalid_key" http://localhost:9000/api/market_data?symbol=BTC%2FUSDT
```

---

## 安全最佳实践

### 1. API密钥管理

✅ **应该做:**
- 在环境变量中存储API密钥
- 为不同的应用创建不同的密钥
- 定期轮换密钥（建议每90天）
- 为重要操作启用签名验证

❌ **不应该做:**
- 在代码中硬编码API密钥
- 在日志中记录完整的API密钥
- 通过不安全的渠道共享API密钥
- 使用过期的或已泄露的密钥

### 2. 防DDOS

系统采用多层防护：

1. **IP级别限制**: 每个IP每分钟最多1000请求
2. **用户级别限制**: 按用户等级限制（PRO: 60 req/min, SVIP: 120 req/min）
3. **请求签名**: 防止请求伪造
4. **自动黑名单**: 异常行为自动IP黑名单

### 3. 日志审计

系统记录所有重要操作：
- 用户创建和修改
- API密钥生成和吊销
- 充值和扣费记录
- 异常访问尝试

查看日志：
```bash
grep "Failed\|Warning\|Error" investment_ai.log
```

---

## 故障排除

### 问题1: API密钥无法识别

**可能原因:**
- 用户已被禁用
- 密钥格式不正确
- 用户余额为0

**解决方案:**
```python
from user_manager import UserManager

manager = UserManager()
valid, user_info = manager.verify_api_key("pk_your_key")
print(f"Valid: {valid}")
print(f"User: {user_info}")
```

### 问题2: 被速率限制

**可能原因:**
- 请求过于频繁
- 多个应用共享一个密钥
- 网络异常导致重复请求

**解决方案:**
- 降低请求频率
- 为每个应用使用不同的密钥
- 实现指数退避算法

### 问题3: 余额快速消耗

**检查日志:**
```bash
sqlite3 users.db "SELECT * FROM usage_log WHERE user_id='user_xxx' ORDER BY created_at DESC LIMIT 20;"
```

**注意:** 系统每日自动扣费（无论是否使用API），这是设计的一部分。

---

## 支持

如有问题，请：
1. 查看 `investment_ai.log` 日志文件
2. 参考 `API_DOCUMENTATION.md` 文档
3. 检查用户管理器的返回结果

---

**文档版本**: 1.0.0  
**最后更新**: 2026年3月11日
