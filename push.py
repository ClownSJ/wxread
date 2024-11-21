# push.py
import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PushNotification:
    def __init__(self, pushplus_token=None):
        self.pushplus_url = "https://www.pushplus.plus/send"
        self.headers = {
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
        }
        self.pushplus_token = pushplus_token or os.getenv("PUSHPLUS_TOKEN", "YOUR_PUSHPLUS_TOKEN")

    def push_pushplus(self, content):
        """
        Send notification via PushPlus
        """
        try:
            params = {
                "token": self.pushplus_token,
                "content": content
            }
            response = requests.get(self.pushplus_url, headers=self.headers, params=params)
            response.raise_for_status()
            logger.info("PushPlus Response: %s", response.text)
            return True
        except requests.RequestException as e:
            logger.error("PushPlus通知发送失败: %s", str(e))
            return False

def push(content, method, pushplus_token=None):
    """
    统一推送接口
    """
    if method != "pushplus":
        raise ValueError("无效的通知渠道. 请选择 'pushplus'")
    
    notifier = PushNotification(pushplus_token)
    return notifier.push_pushplus(content)
