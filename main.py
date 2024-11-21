import os
import json
import requests
import time
import hashlib
import urllib.parse
import random
from pushReadRes import push
from capture import headers as local_headers, cookies as local_cookies, data
import logging

# 常量和配置项
KEY = "3c5c8717f3daf09iop3423zafeqoi"
READ_URL = "https://weread.qq.com/web/book/read"
RENEW_URL = "https://weread.qq.com/web/login/renewal"
COOKIE_DATA = {"rq": "%2Fweb%2Fbook%2Fread"}
DEFAULT_READ_NUM = 4
SLEEP_INTERVAL = 30

# 从环境变量获取 headers、cookies等值(如果不存在使用默认本地值)
env_headers = os.getenv('WXREAD_HEADERS')
env_cookies = os.getenv('WXREAD_COOKIES')
env_num = os.getenv('READ_NUM')
env_method = os.getenv('PUSH_METHOD')

headers = json.loads(json.dumps(eval(env_headers))) if env_headers else local_headers
cookies = json.loads(json.dumps(eval(env_cookies))) if env_cookies else local_cookies
number = int(env_num) if env_num not in (None, '') else DEFAULT_READ_NUM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger('main')

def encode_data(data):
    return '&'.join(f"{k}={urllib.parse.quote(str(data[k]), safe='')}" for k in sorted(data.keys()))

def cal_hash(input_string):
    _7032f5 = 0x15051505
    _cc1055 = _7032f5
    length = len(input_string)
    _19094e = length - 1

    while _19094e > 0:
        _7032f5 = 0x7fffffff & (_7032f5 ^ ord(input_string[_19094e]) << (length - _19094e) % 30)
        _cc1055 = 0x7fffffff & (_cc1055 ^ ord(input_string[_19094e - 1]) << _19094e % 30)
        _19094e -= 2

    return hex(_7032f5 + _cc1055)[2:].lower()

def get_wr_skey():
    try:
        response = requests.post(RENEW_URL, headers=headers, cookies=cookies,
                                 data=json.dumps(COOKIE_DATA, separators=(',', ':')))
        for cookie in response.headers.get('Set-Cookie', '').split(';'):
            if "wr_skey" in cookie:
                return cookie.split('=')[-1][:8]
    except requests.RequestException as e:
        log.warning(f"⚠ 请求失败: {e}")
    return None

def read_book(index):
    data['ct'] = int(time.time())
    data['ts'] = int(time.time() * 1000)
    data['rn'] = random.randint(0, 1000)
    data['sg'] = hashlib.sha256(f"{data['ts']}{data['rn']}{KEY}".encode()).hexdigest()
    data['s'] = cal_hash(encode_data(data))

    log.info(f"\n尝试第 {str(index)} 次阅读...")
    try:
        response = requests.post(READ_URL, headers=headers, cookies=cookies, data=json.dumps(data, separators=(',', ':')))
        resData = response.json()
        log.info(resData)

        if 'succ' in resData:
            return True
        else:
            log.error("❌ cookie 已过期，尝试刷新...")
            new_skey = get_wr_skey()
            if new_skey:
                cookies['wr_skey'] = new_skey
                log.info(f"✅ 密钥刷新成功，新密钥：{new_skey}\n🔄 重新本次阅读。")
            else:
                log.warning("⚠ 无法获取新密钥，终止运行。")
                return False
    except requests.RequestException as e:
        log.warning(f"⚠ 请求失败: {e}")
    finally:
        data.pop('s')
    return False

index = 1
while index <= number:
    if read_book(index):
        random_sleep = SLEEP_INTERVAL + random.randint(0, 5)
        time.sleep(random_sleep)
        log.info(f"✅ 阅读成功，阅读进度：{str(index * 0.5)} 分钟，休眠时间：{str(random_sleep)} 秒")
        index += 1
    else:
        break

log.info("🎉 阅读脚本已完成！")
if env_method not in (None, ''):
    push("阅读脚本已完成！", env_method)
