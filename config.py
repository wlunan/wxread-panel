# config.py 青龙面板配置：优先读环境变量，回退到青龙 QLAPI，最后使用默认值
import os
import re


def getenv(key, default=None):
    """读取环境变量。

    顺序：进程环境变量 -> 青龙 QLAPI -> 默认值。
    这样同一份代码在青龙面板和本地/服务器都能直接运行。
    """
    value = os.getenv(key)
    if value:
        return value
    try:
        # QLAPI 由青龙运行时注入；本地运行时未定义会抛 NameError 并落到 except
        result = QLAPI.getEnvs({"searchValue": key})  # noqa: F821
        return result["data"][0]["value"]
    except Exception:
        return default


# ---- 每次阅读的间隔范围（秒）----
# 两次请求之间随机 sleep 该范围内的秒数，均值约等于服务端单次计入的阅读时长
READ_INTERVAL_MIN = int(getenv('READ_INTERVAL_MIN') or 20)
READ_INTERVAL_MAX = int(getenv('READ_INTERVAL_MAX') or 40)

# ---- 目标总阅读时长范围（分钟）——主开关 ----
# 累计阅读时长达到区间内随机取到的目标后停止；想固定时长就把上下限填成相同的值
READ_TIME_MIN = float(getenv('READ_TIME_MIN') or 0)
READ_TIME_MAX = float(getenv('READ_TIME_MAX') or 0)

# 兼容旧配置：未配置 READ_TIME_*（需两项都大于 0）时，按 READ_NUM × 30 秒换算目标时长
if READ_TIME_MIN <= 0 or READ_TIME_MAX <= 0:
    READ_TIME_MIN = READ_TIME_MAX = int(getenv('READ_NUM') or 40) * 30 / 60

# 非法配置回退：时长上下限颠倒时交换，间隔非法时用默认值
if READ_TIME_MAX < READ_TIME_MIN:
    READ_TIME_MIN, READ_TIME_MAX = READ_TIME_MAX, READ_TIME_MIN
if READ_INTERVAL_MIN <= 0 or READ_INTERVAL_MAX <= 0 or READ_INTERVAL_MIN > READ_INTERVAL_MAX:
    READ_INTERVAL_MIN, READ_INTERVAL_MAX = 20, 40


# 推送方式与令牌
PUSH_METHOD = getenv('PUSH_METHOD')
PUSHPLUS_TOKEN = getenv('PUSHPLUS_TOKEN')
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')
WXPUSHER_SPT = getenv('WXPUSHER_SPT')
SERVERCHAN_SPT = getenv('SERVERCHAN_SPT')

# read 接口的 curl bash 命令，本地部署时可对应替换 headers、cookies
curl_str = getenv('WXREAD_CURL_BASH')

# headers、cookies 是一个省略模版，青龙部署时会被 curl_str 覆盖
cookies = {
    'RK': 'oxEY1bTnXf',
    'ptcz': '53e3b35a9486dd63c4d06430b05aa169402117fc407dc5cc9329b41e59f62e2b',
    'pac_uid': '0_e63870bcecc18',
    'iip': '0',
    '_qimei_uuid42': '183070d3135100ee797b08bc922054dc3062834291',
    'wr_avatar': 'https%3A%2F%2Fthirdwx.qlogo.cn%2Fmmopen%2Fvi_32%2FeEOpSbFh2Mb1bUxMW9Y3FRPfXwWvOLaNlsjWIkcKeeNg6vlVS5kOVuhNKGQ1M8zaggLqMPmpE5qIUdqEXlQgYg%2F132',
    'wr_gender': '0',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ko;q=0.5',
    'baggage': 'sentry-environment=production,sentry-release=dev-1730698697208,sentry-public_key=ed67ed71f7804a038e898ba54bd66e44,sentry-trace_id=1ff5a0725f8841088b42f97109c45862',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
}


# 书籍
book = [
    "36d322f07186022636daa5e","6f932ec05dd9eb6f96f14b9","43f3229071984b9343f04a4","d7732ea0813ab7d58g0184b8",
    "3d03298058a9443d052d409","4fc328a0729350754fc56d4","a743220058a92aa746632c0","140329d0716ce81f140468e",
    "1d9321c0718ff5e11d9afe8","ff132750727dc0f6ff1f7b5","e8532a40719c4eb7e851cbe","9b13257072562b5c9b1c8d6"
]

# 章节
chapter = [
    "ecc32f3013eccbc87e4b62e","a87322c014a87ff679a21ea","e4d32d5015e4da3b7fbb1fa","16732dc0161679091c5aeb1",
    "8f132430178f14e45fce0f7","c9f326d018c9f0f895fb5e4","45c322601945c48cce2e120","d3d322001ad3d9446802347",
    "65132ca01b6512bd43d90e3","c20321001cc20ad4d76f5ae","c51323901dc51ce410c121b","aab325601eaab3238922e53",
    "9bf32f301f9bf31c7ff0a60","c7432af0210c74d97b01b1c","70e32fb021170efdf2eca12","6f4322302126f4922f45dec"
]

"""
建议保留区域|默认读三体，其它书籍自行测试时间是否增加
"""
data = {
    "appId": "wb182564874663h152492176",
    "b": "ce032b305a9bc1ce0b0dd2a",
    "c": "7cb321502467cbbc409e62d",
    "ci": 70,
    "co": 0,
    "sm": "[插图]第三部广播纪元7年，程心艾AA说",
    "pr": 74,
    "rt": 30,
    "ts": 1727660516749,
    "rn": 31,
    "sg": "991118cc229871a5442993ecb08b5d2844d7f001dbad9a9bc7b2ecf73dc8db7e",
    "ct": 1727660516,
    "ps": "b1d32a307a4c3259g016b67",
    "pc": "080327b07a4c3259g018787",
}


def convert(curl_command):
    """提取 curl 命令里的 headers 与 cookies
    支持 -H 'Cookie: xxx' 和 -b 'xxx' 两种方式的 cookie 提取
    """
    # 提取 headers
    headers_temp = {}
    for match in re.findall(r"-H '([^:]+): ([^']+)'", curl_command):
        headers_temp[match[0]] = match[1]

    # 提取 cookies：优先 -b，其次 -H 'Cookie: xxx'
    cookie_header = next((v for k, v in headers_temp.items()
                          if k.lower() == 'cookie'), '')
    cookie_b = re.search(r"-b '([^']+)'", curl_command)
    cookie_string = cookie_b.group(1) if cookie_b else cookie_header

    cookies = {}
    if cookie_string:
        for cookie in cookie_string.split('; '):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()

    # 移除 headers 中的 Cookie/cookie
    headers = {k: v for k, v in headers_temp.items()
               if k.lower() != 'cookie'}

    return headers, cookies


headers, cookies = convert(curl_str) if curl_str else (headers, cookies)
