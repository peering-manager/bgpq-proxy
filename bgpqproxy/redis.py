from flask import current_app, g

import redis


def redis_client():
    if "redis_client" not in g:
        g.redis_client = redis.Redis(**current_app.config["REDIS"])

    return g.redis_client
