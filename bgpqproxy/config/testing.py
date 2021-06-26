from os import getenv

from config.development import BaseConfig as DevelopmentConfig


class BaseConfig(DevelopmentConfig):
    REDIS_DB = getenv("REDIS_DB", "1")
