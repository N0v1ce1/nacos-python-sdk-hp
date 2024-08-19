import threading
from collections import defaultdict
from datetime import datetime, timedelta
from ratelimit import limits, RateLimitException
from ..cache.concurrent_map import ConcurrentMap


class RateLimiterCache:
    def __init__(self):
        self.cache = defaultdict(lambda: None)

    def get(self, key):
        return self.cache[key]

    def set(self, key, value):
        self.cache[key] = value


checker = {
    'rate_limiter_cache': ConcurrentMap(),
    'mux': threading.Lock(),
}


def is_limited(check_key):
    with checker['mux']:  # 使用with语句自动获取和释放锁
        limiter = checker['rate_limiter_cache'].get(check_key)
        if limiter is None:
            # 限流器，每秒允许5次
            limiter = limits(calls=5, period=1)
            checker['rate_limiter_cache'].set(check_key, limiter)

        # 尝试在当前时间加上一秒的时间内是否允许一个请求
        try:
            # AllowN方法需要一个时间点，这里我们使用当前时间加上一秒
            limiter.allow_n(1, datetime.now() + timedelta(seconds=1))
            return False  # 如果请求没有被限制
        except RateLimitException:
            return True  # 如果请求被限制

