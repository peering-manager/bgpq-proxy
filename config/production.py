from os import getenv


class BaseConfig(object):
    BGPQ_PATH = getenv("BGPQ_PATH", "/usr/local/bin/bgpq3")

    REDIS_HOST = getenv("REDIS_HOST", "")
    REDIS_PORT = getenv("REDIS_PORT", "6379")
    REDIS_DB = getenv("REDIS_DB", "6")
