#!/usr/bin/env python
# -*- coding: utf-8 -*-

from porter.backends.redisqueue import RedisQueue
from porter.backends.rediscache import RedisCache


class BaseReader:
    def __init__(self, redis_config, limit=1000, scale=3, block=True, sleep=10):
        self.queue_key_prefix = redis_config.pop("queue_key_prefix", "porter.queue")
        self.cache_key_prefix = redis_config.pop("cache_key_prefix", "porter.cache")
        self.queue_key = self.cache_key = redis_config.pop("key")
        self.limit = limit
        self.scale = scale
        self.block = block
        self.sleep = sleep
        self.cache = RedisCache(key_prefix=self.cache_key_prefix, **redis_config)
        self.queue = RedisQueue(key_prefix=self.queue_key_prefix, **redis_config)

    def sync(self):
        pass

    def push(self, *records):
        pass

    def status(self):
        pass

    def clear(self, cache):
        if cache == "status":
            self.cache.delete(self.cache_key)
        elif cache == "queue":
            self.queue.delete(self.queue_key)
        else:
            self.cache.delete(self.cache_key)
            self.queue.delete(self.queue_key)

    def count(self):
        pass
