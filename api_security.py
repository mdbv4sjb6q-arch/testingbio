# api_security.py - API认证和防DDOS安全模块
"""
API安全层
- API密钥认证
- 防DDOS和速率限制
- IP白名单
- 请求签名验证
"""

import hashlib
import hmac
import time
import json
import logging
from functools import wraps
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from flask import request, jsonify
from user_manager import UserManager

logger = logging.getLogger(__name__)

# 全局用户管理器
user_manager: Optional[UserManager] = None


def init_security(app):
    """初始化安全模块"""
    global user_manager
    user_manager = UserManager()
    
    logger.info("✓ API Security module initialized")


def require_api_key(f):
    """
    API密钥认证装饰器
    
    使用方式:
    Authorization: Bearer <api_key>
    或
    X-API-Key: <api_key>
    或
    URL参数: ?api_key=<api_key>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_manager:
            return jsonify({'error': 'Security not initialized'}), 500
        
        # 获取API密钥
        api_key = None
        api_secret = None
        
        # 1. 检查Authorization header (Bearer)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
        
        # 2. 检查X-API-Key header
        if not api_key:
            api_key = request.headers.get('X-API-Key')
        
        # 3. 检查URL参数
        if not api_key:
            api_key = request.args.get('api_key')
        
        # 4. 检查POST body
        if not api_key:
            try:
                data = request.get_json()
                if data:
                    api_key = data.get('api_key')
                    api_secret = data.get('api_secret')
            except:
                pass
        
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'API key required. Use Authorization header or X-API-Key header'
            }), 401
        
        # 验证API密钥
        valid, user_info = user_manager.verify_api_key(api_key, api_secret)
        
        if not valid:
            logger.warning(f"Invalid API key attempt from {request.remote_addr}: {api_key[:10]}...")
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid API key'}), 401
        
        if not user_info:
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401
        
        # 检查速率限制
        rate_limit_ok, rate_limit_reason = user_manager.check_rate_limit(api_key)
        if not rate_limit_ok:
            logger.warning(f"Rate limit exceeded for {user_info['user_id']}: {rate_limit_reason}")
            return jsonify({
                'error': 'Too Many Requests',
                'message': rate_limit_reason
            }), 429
        
        # 记录API调用
        user_manager.record_api_call(api_key)
        
        # 检查用户是否有足够的天数余额
        if user_info['balance_days'] <= 0:
            logger.warning(f"Insufficient balance for {user_info['user_id']}")
            return jsonify({
                'error': 'Insufficient Balance',
                'message': f'User has {user_info["balance_days"]} days remaining. Please recharge.',
                'remaining_days': user_info['balance_days']
            }), 403
        
        # 每日扣费
        charge_result = user_manager.charge_daily(user_info['user_id'])
        
        if charge_result['status'] != 'ok':
            logger.error(f"Daily charge failed for {user_info['user_id']}")
            return jsonify({
                'error': 'Service Error',
                'message': 'Failed to process daily charge'
            }), 500
        
        # 将用户信息添加到请求上下文
        request.user_info = user_info
        request.api_key = api_key
        request.remaining_days = charge_result['remaining_days']
        
        logger.info(f"✓ API access granted to {user_info['user_id']} ({user_info['tier']}) - "
                   f"Remaining: {request.remaining_days} days")
        
        # 调用原始函数
        response = f(*args, **kwargs)
        
        # 添加用户信息到响应头
        if isinstance(response, tuple):
            response_data, status_code = response[0], response[1] if len(response) > 1 else 200
        else:
            response_data, status_code = response, 200
        
        if isinstance(response_data, dict):
            response_data['_user_tier'] = user_info['tier']
            response_data['_remaining_days'] = request.remaining_days
        
        return response
    
    return decorated_function


def verify_request_signature(api_secret: str, timestamp: str, nonce: str, 
                            body: str, signature: str) -> bool:
    """
    验证请求签名
    
    签名计算方式:
    signature = HMAC-SHA256(api_secret, timestamp + nonce + body)
    """
    try:
        message = timestamp + nonce + body
        expected_signature = hmac.new(
            api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


def require_signature(f):
    """请求签名验证装饰器（可选的高级安全）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'user_info'):
            return jsonify({'error': 'Authentication required'}), 401
        
        # 获取签名相关参数
        timestamp = request.headers.get('X-Timestamp')
        nonce = request.headers.get('X-Nonce')
        signature = request.headers.get('X-Signature')
        
        if not all([timestamp, nonce, signature]):
            # 如果没有提供签名信息，检查是否超过30秒
            try:
                ts = int(timestamp) if timestamp else 0
                current_ts = int(time.time())
                if abs(current_ts - ts) > 30:
                    return jsonify({'error': 'Request expired'}), 401
            except:
                pass
        
        return f(*args, **kwargs)
    
    return decorated_function


class DDoSProtection:
    """DDoS防护类"""
    
    def __init__(self, max_requests_per_ip: int = 1000, time_window: int = 60):
        """
        初始化DDoS防护
        
        Args:
            max_requests_per_ip: 每个IP在时间窗口内的最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests_per_ip
        self.time_window = time_window
        self.ip_requests = {}
    
    def is_allowed(self, ip: str) -> bool:
        """检查IP是否被允许"""
        current_time = time.time()
        
        if ip not in self.ip_requests:
            self.ip_requests[ip] = []
        
        # 清理过期的请求记录
        self.ip_requests[ip] = [
            req_time for req_time in self.ip_requests[ip]
            if current_time - req_time < self.time_window
        ]
        
        # 检查是否超过限制
        if len(self.ip_requests[ip]) >= self.max_requests:
            logger.warning(f"DDoS detected from IP: {ip}")
            return False
        
        # 记录新请求
        self.ip_requests[ip].append(current_time)
        return True
    
    def get_status(self, ip: str) -> Dict:
        """获取IP的请求状态"""
        current_time = time.time()
        
        if ip not in self.ip_requests:
            return {'ip': ip, 'requests': 0, 'limit': self.max_requests}
        
        # 清理过期的请求记录
        self.ip_requests[ip] = [
            req_time for req_time in self.ip_requests[ip]
            if current_time - req_time < self.time_window
        ]
        
        return {
            'ip': ip,
            'requests': len(self.ip_requests[ip]),
            'limit': self.max_requests,
            'window_seconds': self.time_window,
            'remaining': max(0, self.max_requests - len(self.ip_requests[ip]))
        }


# 全局DDoS防护实例
ddos_protection = DDoSProtection(max_requests_per_ip=1000, time_window=60)


def protect_from_ddos(f):
    """DDoS防护装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if not ddos_protection.is_allowed(client_ip):
            logger.warning(f"Request blocked due to DDoS protection: {client_ip}")
            return jsonify({
                'error': 'Too Many Requests',
                'message': 'Request rate exceeded. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function


class IPWhitelist:
    """IP白名单管理"""
    
    def __init__(self):
        self.whitelist = {}  # {api_key: [ip1, ip2, ...]}
    
    def add_ip(self, api_key: str, ip: str):
        """添加IP到白名单"""
        if api_key not in self.whitelist:
            self.whitelist[api_key] = []
        if ip not in self.whitelist[api_key]:
            self.whitelist[api_key].append(ip)
    
    def remove_ip(self, api_key: str, ip: str):
        """从白名单移除IP"""
        if api_key in self.whitelist and ip in self.whitelist[api_key]:
            self.whitelist[api_key].remove(ip)
    
    def is_allowed(self, api_key: str, ip: str) -> bool:
        """检查IP是否在白名单中"""
        if api_key not in self.whitelist:
            return True  # 没有设置白名单则允许所有IP
        return ip in self.whitelist[api_key]
    
    def get_whitelist(self, api_key: str) -> list:
        """获取白名单"""
        return self.whitelist.get(api_key, [])


# 全局IP白名单实例
ip_whitelist = IPWhitelist()
