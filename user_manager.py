# user_manager.py - 用户会员管理系统
"""
支持PRO和SVIP用户的会员管理系统
- 用户认证和授权
- 按天数计算的充值机制
- 自动扣费系统
- 数据库持久化
"""

import sqlite3
import json
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import logging
import os

logger = logging.getLogger(__name__)


class UserManager:
    """用户会员管理系统"""
    
    def __init__(self, db_path: str = 'users.db'):
        """初始化用户管理系统"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    api_key TEXT UNIQUE NOT NULL,
                    api_secret TEXT NOT NULL,
                    partner_name TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'free',
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    remark TEXT
                )
            ''')
            
            # 余额和充值表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balance (
                    balance_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    balance_days INTEGER DEFAULT 0,
                    total_charged_days INTEGER DEFAULT 0,
                    daily_charge_count INTEGER DEFAULT 0,
                    last_charge_date TEXT,
                    last_charge_amount INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 充值记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recharge_log (
                    record_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    amount_days INTEGER NOT NULL,
                    recharge_type TEXT NOT NULL,
                    recharge_date TEXT NOT NULL,
                    expiry_date TEXT,
                    payment_method TEXT,
                    transaction_id TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    remark TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # 使用记录表（每日扣费）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_log (
                    usage_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    days_charged INTEGER DEFAULT 1,
                    usage_date TEXT NOT NULL,
                    api_calls INTEGER DEFAULT 0,
                    data_points INTEGER DEFAULT 0,
                    request_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # API访问控制表（防DDOS）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_access_control (
                    control_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    ip_whitelist TEXT,
                    rate_limit INTEGER DEFAULT 100,
                    requests_per_minute INTEGER DEFAULT 60,
                    max_concurrent_requests INTEGER DEFAULT 10,
                    last_request_time REAL,
                    request_count_minute INTEGER DEFAULT 0,
                    blocked BOOLEAN DEFAULT 0,
                    blocked_reason TEXT,
                    blocked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
            logger.info("✓ Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            conn.close()
    
    def create_user(self, partner_name: str, tier: str = 'pro', 
                   email: str = None, initial_days: int = 30,
                   recharge_type: str = 'monthly') -> Dict:
        """
        创建新用户
        
        Args:
            partner_name: 合作商名称
            tier: 用户等级 ('free', 'pro', 'svip')
            email: 邮箱
            initial_days: 初始充值天数
            recharge_type: 充值类型 ('monthly', 'quarterly', 'yearly', 'permanent')
        
        Returns:
            用户信息字典
        """
        try:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            api_key = self._generate_api_key()
            api_secret = self._generate_api_secret()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建用户
            cursor.execute('''
                INSERT INTO users (user_id, api_key, api_secret, partner_name, tier, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, api_key, api_secret, partner_name, tier, email))
            
            # 创建余额记录
            balance_id = f"balance_{uuid.uuid4().hex[:12]}"
            cursor.execute('''
                INSERT INTO balance (balance_id, user_id, tier, balance_days, total_charged_days)
                VALUES (?, ?, ?, ?, ?)
            ''', (balance_id, user_id, tier, initial_days, initial_days))
            
            # 记录初始充值
            record_id = f"recharge_{uuid.uuid4().hex[:12]}"
            expiry_date = self._calculate_expiry_date(initial_days, recharge_type)
            cursor.execute('''
                INSERT INTO recharge_log 
                (record_id, user_id, tier, amount_days, recharge_type, recharge_date, expiry_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (record_id, user_id, tier, initial_days, recharge_type, 
                  datetime.now().isoformat(), expiry_date, 'completed'))
            
            # 创建API访问控制
            control_id = f"control_{uuid.uuid4().hex[:12]}"
            rate_limit = 1000 if tier == 'svip' else 500 if tier == 'pro' else 100
            rpm = 120 if tier == 'svip' else 60 if tier == 'pro' else 30
            
            cursor.execute('''
                INSERT INTO api_access_control
                (control_id, user_id, api_key, rate_limit, requests_per_minute)
                VALUES (?, ?, ?, ?, ?)
            ''', (control_id, user_id, api_key, rate_limit, rpm))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ User created: {user_id} ({partner_name}, {tier})")
            
            return {
                'status': 'ok',
                'user_id': user_id,
                'api_key': api_key,
                'api_secret': api_secret,
                'partner_name': partner_name,
                'tier': tier,
                'balance_days': initial_days,
                'created_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def verify_api_key(self, api_key: str, api_secret: str = None) -> Tuple[bool, Optional[Dict]]:
        """
        验证API密钥
        
        Args:
            api_key: API密钥
            api_secret: API密钥（可选，用于高级验证）
        
        Returns:
            (是否有效, 用户信息)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute('''
                SELECT u.user_id, u.api_key, u.api_secret, u.tier, u.is_active,
                       b.balance_days, b.last_charge_date
                FROM users u
                LEFT JOIN balance b ON u.user_id = b.user_id
                WHERE u.api_key = ?
            ''', (api_key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, None
            
            user_id, api_key_stored, api_secret_stored, tier, is_active, balance_days, last_charge_date = result
            
            # 检查用户是否活跃
            if not is_active:
                logger.warning(f"Inactive user attempted access: {user_id}")
                return False, None
            
            # 如果提供了api_secret，进行完整验证
            if api_secret and api_secret != api_secret_stored:
                logger.warning(f"Invalid API secret for user: {user_id}")
                return False, None
            
            user_info = {
                'user_id': user_id,
                'api_key': api_key,
                'tier': tier,
                'balance_days': balance_days or 0,
                'is_active': is_active,
                'last_charge_date': last_charge_date
            }
            
            return True, user_info
        
        except Exception as e:
            logger.error(f"API verification failed: {e}")
            return False, None
    
    def charge_daily(self, user_id: str) -> Dict:
        """
        每日扣费
        
        Args:
            user_id: 用户ID
        
        Returns:
            扣费结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取用户余额
            cursor.execute('''
                SELECT balance_days, tier FROM balance WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'status': 'error', 'message': 'User not found'}
            
            balance_days, tier = result
            
            # 检查今天是否已扣费
            cursor.execute('''
                SELECT COUNT(*) FROM usage_log 
                WHERE user_id = ? AND usage_date = ?
            ''', (user_id, datetime.now().date().isoformat()))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                return {
                    'status': 'ok',
                    'message': 'Already charged today',
                    'remaining_days': balance_days
                }
            
            # 扣费（每天扣1天）
            if balance_days <= 0:
                conn.close()
                return {'status': 'error', 'message': 'Insufficient balance'}
            
            new_balance = balance_days - 1
            
            # 更新余额
            cursor.execute('''
                UPDATE balance 
                SET balance_days = ?, daily_charge_count = daily_charge_count + 1, last_charge_date = ?
                WHERE user_id = ?
            ''', (new_balance, datetime.now().isoformat(), user_id))
            
            # 记录使用
            usage_id = f"usage_{uuid.uuid4().hex[:12]}"
            cursor.execute('''
                INSERT INTO usage_log (usage_id, user_id, tier, days_charged, usage_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (usage_id, user_id, tier, 1, datetime.now().date().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Daily charge for {user_id}: {balance_days} → {new_balance}")
            
            return {
                'status': 'ok',
                'message': 'Daily charge successful',
                'remaining_days': new_balance,
                'charged_days': 1
            }
        
        except Exception as e:
            logger.error(f"Daily charge failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def recharge_user(self, user_id: str, amount_days: int, 
                     recharge_type: str = 'manual', payment_method: str = 'transfer') -> Dict:
        """
        充值用户余额
        
        Args:
            user_id: 用户ID
            amount_days: 充值天数
            recharge_type: 充值类型 ('manual', 'monthly', 'quarterly', 'yearly', 'permanent')
            payment_method: 支付方式 ('transfer', 'wechat', 'alipay', 'crypto')
        
        Returns:
            充值结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取用户信息
            cursor.execute('''
                SELECT tier, balance_days FROM balance WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'status': 'error', 'message': 'User not found'}
            
            tier, current_balance = result
            
            # 更新余额
            new_balance = current_balance + amount_days
            expiry_date = self._calculate_expiry_date(amount_days, recharge_type)
            
            cursor.execute('''
                UPDATE balance 
                SET balance_days = ?, total_charged_days = total_charged_days + ?, 
                    last_charge_date = ?, last_charge_amount = ?
                WHERE user_id = ?
            ''', (new_balance, amount_days, datetime.now().isoformat(), 
                  amount_days, user_id))
            
            # 记录充值
            record_id = f"recharge_{uuid.uuid4().hex[:12]}"
            cursor.execute('''
                INSERT INTO recharge_log
                (record_id, user_id, tier, amount_days, recharge_type, recharge_date, 
                 expiry_date, payment_method, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (record_id, user_id, tier, amount_days, recharge_type,
                  datetime.now().isoformat(), expiry_date, payment_method, 'completed'))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Recharge for {user_id}: +{amount_days} days ({recharge_type})")
            
            return {
                'status': 'ok',
                'message': 'Recharge successful',
                'user_id': user_id,
                'previous_balance': current_balance,
                'new_balance': new_balance,
                'amount_days': amount_days,
                'recharge_type': recharge_type,
                'expiry_date': expiry_date,
                'record_id': record_id
            }
        
        except Exception as e:
            logger.error(f"Recharge failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户详细信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.user_id, u.partner_name, u.tier, u.email, u.is_active,
                       b.balance_days, b.total_charged_days, b.daily_charge_count, b.last_charge_date,
                       (SELECT COUNT(*) FROM usage_log WHERE user_id = u.user_id) as total_api_calls
                FROM users u
                LEFT JOIN balance b ON u.user_id = b.user_id
                WHERE u.user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            user_id, partner_name, tier, email, is_active, balance_days, total_charged, daily_count, last_charge, total_calls = result
            
            return {
                'user_id': user_id,
                'partner_name': partner_name,
                'tier': tier,
                'email': email,
                'is_active': is_active,
                'balance_days': balance_days or 0,
                'total_charged_days': total_charged or 0,
                'daily_charge_count': daily_count or 0,
                'last_charge_date': last_charge,
                'total_api_calls': total_calls or 0
            }
        
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def check_rate_limit(self, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        检查API速率限制（防DDOS）
        
        Returns:
            (是否通过, 阻止原因)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取访问控制配置
            cursor.execute('''
                SELECT control_id, blocked, blocked_reason, blocked_until,
                       requests_per_minute, request_count_minute, last_request_time
                FROM api_access_control
                WHERE api_key = ?
            ''', (api_key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return True, None
            
            control_id, blocked, blocked_reason, blocked_until, rpm_limit, request_count, last_request_time = result
            
            # 检查是否被阻止
            if blocked:
                if blocked_until and datetime.fromisoformat(blocked_until) > datetime.now():
                    return False, f"Rate limit blocked: {blocked_reason}"
                else:
                    # 解除阻止
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE api_access_control
                        SET blocked = 0, blocked_reason = NULL, blocked_until = NULL
                        WHERE api_key = ?
                    ''', (api_key,))
                    conn.commit()
                    conn.close()
            
            # 检查每分钟请求数
            if last_request_time:
                import time
                current_time = time.time()
                if current_time - last_request_time < 60:  # 同一分钟内
                    if request_count >= rpm_limit:
                        return False, f"Rate limit exceeded: {rpm_limit} requests per minute"
            
            return True, None
        
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False, str(e)
    
    def record_api_call(self, api_key: str) -> bool:
        """记录API调用（用于速率限制）"""
        try:
            import time
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = time.time()
            
            cursor.execute('''
                UPDATE api_access_control
                SET request_count_minute = request_count_minute + 1,
                    last_request_time = ?
                WHERE api_key = ?
            ''', (current_time, api_key))
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            logger.error(f"Failed to record API call: {e}")
            return False
    
    # 辅助方法
    
    @staticmethod
    def _generate_api_key() -> str:
        """生成API密钥"""
        return f"pk_{uuid.uuid4().hex[:32]}"
    
    @staticmethod
    def _generate_api_secret() -> str:
        """生成API密钥"""
        return uuid.uuid4().hex
    
    @staticmethod
    def _calculate_expiry_date(days: int, recharge_type: str) -> str:
        """计算过期日期"""
        if recharge_type == 'permanent':
            return '9999-12-31'
        
        now = datetime.now()
        if recharge_type == 'monthly':
            expiry = now + timedelta(days=30)
        elif recharge_type == 'quarterly':
            expiry = now + timedelta(days=90)
        elif recharge_type == 'yearly':
            expiry = now + timedelta(days=365)
        else:
            expiry = now + timedelta(days=days)
        
        return expiry.isoformat()
