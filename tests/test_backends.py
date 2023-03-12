#!/usr/bin/env python
# -*- coding: utf-8 -*-

from porter.backends.rediscache import RedisCache


class TestRedisCache:
    cache = RedisCache(
        host="127.0.0.1",
        port=6379,
        password="123456",
        db=53,
        key_prefix="porter.test.TestRedisCache.",
    )

    def test_get(self):
        pass

    def test_set(self):
        self.cache.setmany("hello", mapping={"Trump": "Stupid", "Biden": "Stupid"})


if __name__ == "__main__":
    test = TestRedisCache()
    test.test_set()
