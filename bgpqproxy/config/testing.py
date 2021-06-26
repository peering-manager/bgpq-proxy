from os import getenv

from bgpqproxy.config.development import BaseConfig as DevConfig


class BaseConfig(DevConfig):
    super().REDIS["db"] = getenv("REDIS_DB", "1")
