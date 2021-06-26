from os import getenv


class BaseConfig(object):
    BGPQ_PATH = getenv("BGPQ_PATH", "/usr/local/bin/bgpq3")
    REDIS = {
        "host": getenv("REDIS_HOST", "localhost"),
        "port": getenv("REDIS_PORT", "6379"),
        "db": getenv("REDIS_DB", "0"),
    }
