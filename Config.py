import time

API_URL="https://test.g4b.cn/rpa/api"
REDIS_URL="114.132.45.130"
REDIS_DB=80

# 所有组件的超时时间
TIMEOUTS=20

# 自定义的等待时间
TIMEWAIT=2

def get_timewait():
    return TIMEWAIT

def wait():
    time.sleep(get_timewait())

# 主函数重试次数
MAIN_RETRY=3




