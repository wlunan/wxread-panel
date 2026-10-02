# main.py 主逻辑：字段拼接、请求签名、模拟阅读（青龙面板版）
import json
import time
import random
import logging
import hashlib
import requests
import urllib.parse

from push import push
from config import (
    data,
    headers,
    cookies,
    READ_TIME_MIN,
    READ_TIME_MAX,
    READ_INTERVAL_MIN,
    READ_INTERVAL_MAX,
    PUSH_METHOD,
    book,
    chapter,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)-8s - %(message)s')

# 加密盐及其它默认值
KEY = "3c5c8717f3daf09iop3423zafeqoi"
READ_URL = "https://weread.qq.com/web/book/read"
RENEW_URL = "https://weread.qq.com/web/login/renewal"
FIX_SYNCKEY_URL = "https://weread.qq.com/web/book/chapterInfos"
COOKIE_DATA_VARIANTS = [
    {"rq": "%2Fweb%2Fbook%2Fread", "ql": False},
    {"rq": "%2Fweb%2Fbook%2Fread", "ql": True},
    {"rq": "%2Fweb%2Fbook%2Fread"},
]
REQUEST_TIMEOUT = (10, 30)
SYNCKEY_REPAIR_LIMIT = 3
SYNCKEY_REPAIR_DELAY = 5
AUTH_ERROR_CODES = {-2012, -2013}


def encode_data(data):
    """数据编码"""
    return '&'.join(f"{k}={urllib.parse.quote(str(data[k]), safe='')}" for k in sorted(data.keys()))


def cal_hash(input_string):
    """计算哈希值"""
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
    """刷新 cookie 密钥"""
    for cookie_data in COOKIE_DATA_VARIANTS:
        try:
            response = requests.post(
                RENEW_URL,
                headers=headers,
                cookies=cookies,
                data=json.dumps(cookie_data, separators=(',', ':')),
                timeout=REQUEST_TIMEOUT,
            )
            if 'wr_skey' in response.cookies:
                return response.cookies['wr_skey'][:8]
        except requests.RequestException as exc:
            logging.warning(f"refresh_cookie 请求失败，payload={cookie_data}，原因：{exc}")
    return None


def fix_no_synckey():
    """重建 synckey"""
    response = requests.post(
        FIX_SYNCKEY_URL,
        headers=headers,
        cookies=cookies,
        data=json.dumps({"bookIds": ["3300060341"]}, separators=(',', ':')),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def refresh_cookie(strict=True):
    """刷新 cookie；strict=False 时失败也不终止"""
    logging.info("刷新 cookie")
    new_skey = get_wr_skey()
    if new_skey:
        cookies['wr_skey'] = new_skey
        logging.info(f"密钥刷新成功，新密钥：{new_skey[:2]}***")
        logging.info("重新本次阅读。")
        return True

    ERROR_CODE = "无法获取新密钥，当前登录状态可能已失效，终止运行。"
    if strict:
        logging.error(ERROR_CODE)
        push(ERROR_CODE, PUSH_METHOD, is_success=False)
        raise Exception(ERROR_CODE)

    logging.warning("启动时未获取到新密钥，保留现有 cookie 继续尝试阅读。")
    return False


def read():
    # renewal 失败不等于当前阅读会话已失效；启动时刷新失败也继续尝试阅读。
    refresh_cookie(strict=False)

    # 本次运行的目标总阅读时长（秒），在配置区间内随机取一个值
    target_seconds = random.uniform(READ_TIME_MIN, READ_TIME_MAX) * 60
    logging.info(
        "目标阅读时长 %.1f 分钟（范围 %g~%g 分钟），每次间隔 %d~%d 秒。",
        target_seconds / 60,
        READ_TIME_MIN,
        READ_TIME_MAX,
        READ_INTERVAL_MIN,
        READ_INTERVAL_MAX,
    )

    read_count = 0
    read_seconds = 0
    lastTime = int(time.time()) - random.randint(READ_INTERVAL_MIN, READ_INTERVAL_MAX)
    synckey_repair_attempts = 0

    while read_seconds < target_seconds:
        data.pop('s')
        data['b'] = random.choice(book)
        data['c'] = random.choice(chapter)
        thisTime = int(time.time())
        data['ct'] = thisTime
        data['rt'] = thisTime - lastTime
        data['ts'] = int(thisTime * 1000) + random.randint(0, 1000)
        data['rn'] = random.randint(0, 1000)
        data['sg'] = hashlib.sha256(f"{data['ts']}{data['rn']}{KEY}".encode()).hexdigest()
        data['s'] = cal_hash(encode_data(data))

        logging.info(
            "阅读进度: 第 %d 次，已完成 %.1f / %.1f 分钟",
            read_count + 1, read_seconds / 60, target_seconds / 60,
        )
        logging.debug("data: %s", data)

        try:
            response = requests.post(
                READ_URL,
                headers=headers,
                cookies=cookies,
                data=json.dumps(data, separators=(',', ':')),
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            ERROR_CODE = f"阅读请求失败：{exc}"
            logging.error(ERROR_CODE)
            push(ERROR_CODE, PUSH_METHOD, is_success=False)
            raise RuntimeError(ERROR_CODE) from exc

        try:
            resData = response.json()
        except ValueError as exc:
            ERROR_CODE = f"read 接口返回非 JSON 响应，HTTP {response.status_code}。"
            logging.error(ERROR_CODE)
            push(ERROR_CODE, PUSH_METHOD, is_success=False)
            raise RuntimeError(ERROR_CODE) from exc

        logging.debug("response: %s", resData)

        if 'succ' in resData:
            if 'synckey' in resData:
                synckey_repair_attempts = 0
                lastTime = thisTime
                read_seconds += data['rt']
                read_count += 1
                time.sleep(random.uniform(READ_INTERVAL_MIN, READ_INTERVAL_MAX))
            else:
                synckey_repair_attempts += 1
                if synckey_repair_attempts > SYNCKEY_REPAIR_LIMIT:
                    ERROR_CODE = f"连续 {SYNCKEY_REPAIR_LIMIT} 次未恢复 synckey，终止运行。"
                    logging.error(ERROR_CODE)
                    push(ERROR_CODE, PUSH_METHOD, is_success=False)
                    raise RuntimeError(ERROR_CODE)

                logging.warning(
                    "无 synckey，尝试修复（%d/%d）...",
                    synckey_repair_attempts, SYNCKEY_REPAIR_LIMIT,
                )
                try:
                    fix_no_synckey()
                except requests.RequestException as exc:
                    ERROR_CODE = f"synckey 修复请求失败：{exc}"
                    logging.error(ERROR_CODE)
                    push(ERROR_CODE, PUSH_METHOD, is_success=False)
                    raise RuntimeError(ERROR_CODE) from exc
                time.sleep(SYNCKEY_REPAIR_DELAY)
        else:
            err_code = resData.get('errCode')
            err_msg = resData.get('errMsg')
            logging.warning(
                "read 接口返回异常：HTTP %s，errCode=%s，errMsg=%s",
                response.status_code, err_code, err_msg,
            )

            if err_code in AUTH_ERROR_CODES:
                logging.warning("检测到登录/鉴权异常，尝试刷新 cookie...")
            else:
                logging.warning("未识别为已知鉴权错误，保留现有刷新流程尝试恢复...")
            refresh_cookie()

    logging.info("阅读脚本已完成，共阅读 %d 次，累计 %.1f 分钟。", read_count, read_seconds / 60)

    if PUSH_METHOD not in (None, ''):
        logging.info("开始推送...")
        push(f"微信读书自动阅读完成。\n阅读时长：{read_seconds / 60:.1f} 分钟。", PUSH_METHOD, is_success=True)
    else:
        logging.info("未配置推送渠道，跳过推送。")


if __name__ == '__main__':
    read()
