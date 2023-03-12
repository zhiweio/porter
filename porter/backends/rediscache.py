#!/usr/bin/env python
# -*- coding: utf-8 -*-

from porter.backends.base import RedisBase, iteritems_wrapper


class RedisCache(RedisBase):
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
        super(RedisCache, self).__init__(host, port, password, db, key_prefix, **kwargs)

    def get(self, key, field):
        return self.load_object(self._read_client.hget(self._get_prefix() + key, field))

    def getmany(self, key, fields):
        return [self.load_object(_) for _ in self._read_client.mget(key, fields)]

    def getall(self, key):
        return self._read_client.hgetall(self._get_prefix() + key)

    def set(self, key, field=None, value=None):
        dump = self.dump_object(value)
        return self._write_client.hset(
            name=self._get_prefix() + key, key=field, value=dump
        )

    def setmany(self, key, mapping=None):
        if mapping:
            mapping = {k: self.dump_object(v) for k, v in iteritems_wrapper(mapping)}
        return self._write_client.hmset(name=self._get_prefix() + key, mapping=mapping)

    def hdel(self, key, fields):
        return self._write_client.hdel(self._get_prefix() + key, *fields)

    def has(self, key, field):
        return self._read_client.hexists(self._get_prefix() + key, field)

    def hasall(self, key, fields):
        return all((self.has(key, field) for field in fields))
