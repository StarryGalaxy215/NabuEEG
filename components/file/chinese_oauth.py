import requests
import hashlib
import time
import random
import string
from typing import Optional, Dict, Tuple

class ChineseOAuthManager:
    """
    国产第三方登录管理器
    支持：QQ、微信、微博、Gitee
    """
    
    def __init__(self):
        # QQ 配置（需要申请）
        self.qq_app_id = None
        self.qq_app_key = None
        self.qq_redirect_uri = None
        
        # 微信配置（需要申请）
        self.wechat_app_id = None
        self.wechat_app_secret = None
        self.wechat_redirect_uri = None
        
        # 微博配置（可选）
        self.weibo_app_key = None
        self.weibo_app_secret = None
        self.weibo_redirect_uri = None
        
        # Gitee 配置（最简单，推荐用于测试）
        self.gitee_client_id = None
        self.gitee_client_secret = None
        self.gitee_redirect_uri = None
    
    def configure_qq(self, app_id: str, app_key: str, redirect_uri: str):
        """配置 QQ 登录"""
        self.qq_app_id = app_id
        self.qq_app_key = app_key
        self.qq_redirect_uri = redirect_uri
    
    def configure_wechat(self, app_id: str, app_secret: str, redirect_uri: str):
        """配置微信登录"""
        self.wechat_app_id = app_id
        self.wechat_app_secret = app_secret
        self.wechat_redirect_uri = redirect_uri
    
    def configure_gitee(self, client_id: str, client_secret: str, redirect_uri: str):
        """配置 Gitee 登录（推荐用于测试）"""
        self.gitee_client_id = client_id
        self.gitee_client_secret = client_secret
        self.gitee_redirect_uri = redirect_uri
    
    def get_qq_auth_url(self, state: str = None) -> str:
        """获取 QQ 授权 URL"""
        if not self.qq_app_id:
            raise ValueError("请先配置 QQ 登录")
        
        state = state or self._generate_state()
        url = (
            "https://graph.qq.com/oauth2.0/authorize?"
            f"response_type=code&"
            f"client_id={self.qq_app_id}&"
            f"redirect_uri={self.qq_redirect_uri}&"
            f"state={state}&"
            f"scope=get_user_info"
        )
        return url
    
    def get_wechat_auth_url(self, state: str = None) -> str:
        """获取微信授权 URL"""
        if not self.wechat_app_id:
            raise ValueError("请先配置微信登录")
        
        state = state or self._generate_state()
        url = (
            "https://open.weixin.qq.com/connect/qrconnect?"
            f"appid={self.wechat_app_id}&"
            f"redirect_uri={self.wechat_redirect_uri}&"
            f"response_type=code&"
            f"scope=snsapi_login&"
            f"state={state}#wechat_redirect"
        )
        return url
    
    def get_gitee_auth_url(self, state: str = None) -> str:
        """获取 Gitee 授权 URL"""
        if not self.gitee_client_id:
            raise ValueError("请先配置 Gitee 登录")
        
        state = state or self._generate_state()
        url = (
            "https://gitee.com/oauth/authorize?"
            f"client_id={self.gitee_client_id}&"
            f"redirect_uri={self.gitee_redirect_uri}&"
            f"response_type=code&"
            f"scope=user_info&"
            f"state={state}"
        )
        return url
    
    def login_with_qq(self, code: str) -> Tuple[bool, dict]:
        """
        使用 QQ code 登录
        
        Args:
            code: QQ 返回的授权码
            
        Returns:
            (成功标志，用户信息字典)
        """
        try:
            # 1. 获取 access_token
            token_url = "https://graph.qq.com/oauth2.0/token"
            token_params = {
                'grant_type': 'authorization_code',
                'client_id': self.qq_app_id,
                'client_secret': self.qq_app_key,
                'code': code,
                'redirect_uri': self.qq_redirect_uri
            }
            
            response = requests.get(token_url, params=token_params, timeout=10)
            # QQ 返回的是 URL 格式，需要解析
            token_result = dict(pair.split('=') for pair in response.text.split('&'))
            
            if 'access_token' not in token_result:
                return False, {'error': '获取 access_token 失败'}
            
            access_token = token_result['access_token']
            
            # 2. 获取 OpenID
            openid_url = "https://graph.qq.com/oauth2.0/me"
            openid_response = requests.get(openid_url, params={'access_token': access_token}, timeout=10)
            # 解析 JSONP
            openid_text = openid_response.text.replace('callback(', '').replace(')', '')
            openid_data = eval(openid_text)
            openid = openid_data['openid']
            
            # 3. 获取用户信息
            user_url = "https://graph.qq.com/user/get_user_info"
            user_params = {
                'access_token': access_token,
                'oauth_consumer_key': self.qq_app_id,
                'openid': openid
            }
            
            user_response = requests.get(user_url, params=user_params, timeout=10)
            user_info = user_response.json()
            
            if user_info.get('ret') == 0:
                user_data = {
                    'platform': 'QQ',
                    'openid': openid,
                    'nickname': user_info.get('nickname', 'QQ 用户'),
                    'avatar': user_info.get('figureurl_qq_2', ''),
                    'gender': user_info.get('gender', 'unknown')
                }
                return True, user_data
            else:
                return False, {'error': user_info.get('msg', 'QQ 登录失败')}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def login_with_wechat(self, code: str) -> Tuple[bool, dict]:
        """
        使用微信 code 登录
        
        Args:
            code: 微信返回的授权码
            
        Returns:
            (成功标志，用户信息字典)
        """
        try:
            # 1. 获取 access_token 和 openid
            token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
            token_params = {
                'appid': self.wechat_app_id,
                'secret': self.wechat_app_secret,
                'code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.get(token_url, params=token_params, timeout=10)
            token_result = response.json()
            
            if 'errcode' in token_result:
                return False, {'error': token_result.get('errmsg', '微信登录失败')}
            
            access_token = token_result['access_token']
            openid = token_result['openid']
            
            # 2. 获取用户信息
            user_url = "https://api.weixin.qq.com/sns/userinfo"
            user_params = {
                'access_token': access_token,
                'openid': openid
            }
            
            user_response = requests.get(user_url, params=user_params, timeout=10)
            user_info = user_response.json()
            
            if 'errcode' not in user_info:
                user_data = {
                    'platform': '微信',
                    'openid': openid,
                    'nickname': user_info.get('nickname', '微信用户'),
                    'avatar': user_info.get('headimgurl', ''),
                    'gender': str(user_info.get('sex', 0))
                }
                return True, user_data
            else:
                return False, {'error': user_info.get('errmsg', '获取用户信息失败')}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def login_with_gitee(self, code: str) -> Tuple[bool, dict]:
        """
        使用 Gitee code 登录（推荐用于测试）
        
        Args:
            code: Gitee 返回的授权码
            
        Returns:
            (成功标志，用户信息字典)
        """
        try:
            # 1. 获取 access_token
            token_url = "https://gitee.com/oauth/token"
            token_params = {
                'grant_type': 'authorization_code',
                'client_id': self.gitee_client_id,
                'client_secret': self.gitee_client_secret,
                'code': code,
                'redirect_uri': self.gitee_redirect_uri
            }
            
            response = requests.post(token_url, data=token_params, timeout=10)
            token_result = response.json()
            
            if 'error' in token_result:
                return False, {'error': token_result.get('error_description', 'Gitee 登录失败')}
            
            access_token = token_result['access_token']
            
            # 2. 获取用户信息
            user_url = "https://gitee.com/api/v5/user"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            user_response = requests.get(user_url, headers=headers, timeout=10)
            user_info = user_response.json()
            
            if 'error' not in user_info:
                user_data = {
                    'platform': 'Gitee',
                    'openid': str(user_info.get('id', '')),
                    'nickname': user_info.get('name', user_info.get('login', 'Gitee 用户')),
                    'avatar': user_info.get('avatar_url', ''),
                    'email': user_info.get('email', '')
                }
                return True, user_data
            else:
                return False, {'error': user_info.get('message', '获取用户信息失败')}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def _generate_state(self, length: int = 32) -> str:
        """生成随机 state 字符串，防止 CSRF 攻击"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# 全局单例
_oauth_manager: Optional[ChineseOAuthManager] = None

def get_oauth_manager() -> ChineseOAuthManager:
    """获取 OAuth 管理器实例（单例模式）"""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = ChineseOAuthManager()
    return _oauth_manager
