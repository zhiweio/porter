#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections

from porter.backends.base import RedisBase


class RedisQueue(RedisBase):
    """
    :param host: address of the Redis server or an object which API is
                 compatible with the official Python Redis client (redis-py).
    :param port: port number on which Redis server listens for connections.
    :param password: password authentication for the Redis server.
    :param db: db (zero-based numeric index) on Redis Server to connect.
    :param key_prefix: A prefix that should be added to all keys.

    Any additional keyword arguments will be passed to ``redis.Redis``.
    """

    def __init__(
        self,
        host="localhost",
        port=6379,
        password=None,
        db=0,
        key_prefix=None,
        **kwargs
    ):
        super(RedisQueue, self).__init__(host, port, password, db, key_prefix, **kwargs)

    def range(self, key, start, end):
        return self._read_client.lrange(self._get_prefix() + key, start, end)

    def len(self, key):
        return self._read_client.llen(self._get_prefix() + key)

    def push(self, key, values):
        if isinstance(values, (tuple, list, collections.Generator)):
            values = (self.dump_object(_) for _ in values)
            return self._write_client.rpush(self._get_prefix() + key, *values)
        else:
            values = self.dump_object(values)
            return self._write_client.rpush(self._get_prefix() + key, values)

    def pop(self, key):
        return self.load_object(self._read_client.lpop(self._get_prefix() + key))

    def pop_many(self, key, count):
        length = self.len(key)
        if length < count:
            count = length
        return [self.pop(key) for _ in range(count)]
