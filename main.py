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

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    return logging.getLogger('main')

def get_env_variable(var_name, default_value):
    return os.getenv(var_name, default_value)

def load_json_data(env_data, local_data):
    return json.loads(json.dumps(eval(env_data))) if env_data else local_data

def initialize():
    headers = load_json_data(get_env_variable('WXREAD_HEADERS', None), local_headers)
    cookies = load_json_data(get_env_variable('WXREAD_COOKIES', None), local_cookies)
    number = int(get_env_variable('READ_NUM', DEFAULT_READ_NUM))
    return headers, cookies, number

def main():
    headers, cookies, number = initialize()
    log = setup_logging()

    index = 1
    failTimes = 0
    readTime = 0
    while index <= number:
        if read_book(index, headers, cookies, log):
            random_sleep = SLEEP_INTERVAL + random.randint(0, 5)
            time.sleep(random_sleep)
            log.info(f"阅读成功，阅读时间：{random_sleep} 秒")
            index += 1
            readTime += random_sleep
        elif failTimes < 3:
            failTimes += 1
            continue
        else:
            log.error("连续三次阅读失败，程序退出。")
            break

    log.info(f"阅读完成，此次共阅读 {readTime} 秒")
    if env_method := get_env_variable('PUSH_METHOD', None):
        push(f"阅读完成，此次共阅读 {readTime} 秒", env_method)

def read_book(index, headers, cookies, log, retry=False):
    data['ct'] = int(time.time())
    data['ts'] = int(time.time() * 1000)
    data['rn'] = random.randint(0, 1000)
    data['sg'] = hashlib.sha256(f"{data['ts']}{data['rn']}{KEY}".encode()).hexdigest()
    data['s'] = cal_hash(encode_data(data))

    log.info(f"尝试第 {index} 次阅读...")
    try:
        response = requests.post(READ_URL, headers=headers, cookies=cookies, data=json.dumps(data, separators=(',', ':')))
        resData = response.json()
        log.info(resData)

        if 'succ' in resData:
            log.info(f"正在进行第 {index} 次阅读...")
            return True
        else:
            if not retry:
                log.error("cookie 已过期，尝试刷新...")
                new_skey = get_wr_skey(headers, cookies, log)
                if new_skey:
                    cookies['wr_skey'] = new_skey  
                    log.info(f"密钥刷新成功，新密钥：{new_skey}, 重新本次阅读。")
                else:
                    log.warning("无法获取新密钥，终止运行。")
            return False
    except requests.RequestException as e:
        log.warning(f"请求失败: {e}")
    finally:
        data.pop('s', None)  # 避免 KeyError

def get_wr_skey(headers, cookies, log):
    try:
        response = requests.post(RENEW_URL, headers=headers, cookies=cookies, data=json.dumps(COOKIE_DATA, separators=(',', ':')))
        for cookie in response.headers.get('Set-Cookie', '').split(';'):
            if "wr_skey" in cookie:
                new_skey = cookie.split('=')[-1][:8]
                return new_skey
    except requests.RequestException as e:
        log.warning(f"⚠ 请求失败: {e}")
    return None

if __name__ == "__main__":
    main()
