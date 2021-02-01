import time
import datetime


def close_time(extend=False):
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 18 if extend else 16, 0, 0, t.tm_wday, t.tm_yday, t.tm_isdst))


def now():
    return time.strftime("%b %d %Y %H:%M:%S", time.localtime())


def utc_to_local(utc_ts):
    pass
