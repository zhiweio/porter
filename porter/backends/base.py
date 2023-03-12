#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

from bson import json_util


def iteritems_wrapper(mappingorseq):
    """Wrapper for efficient iteration over mappings represented by dicts
    or sequences::

        >>> for k, v in iteritems_wrapper((i, i*i) for i in xrange(5)):
        ...    assert k*k == v

        >>> for k, v in iteritems_wrapper(dict((i, i*i) for i in xrange(5))):
        ...    assert k*k == v

    """
    if hasattr(mappingorseq, "items"):
        return mappingorseq.items()
    return mappingorseq


class RedisBase:
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
        if host is None:
            raise ValueError("RedisCache host parameter may not be None")
        if isinstance(host, str):
            try:
                import redis
            except ImportError:
                raise RuntimeError("no redis module found")
            if kwargs.get("decode_responses", None):
                raise ValueError("decode_responses is not supported by " "RedisCache.")
            client = redis.Redis(
                host=host, port=port, password=password, db=db, **kwargs
            )
        else:
            client = host

        self._write_client = self._read_client = client
        self.key_prefix = key_prefix or ""

    def _get_prefix(self):
        return (
            self.key_prefix if isinstance(self.key_prefix, str) else self.key_prefix()
        )

    def dump_object(self, value):
        """Dumps an object into a string for redis.  By default it serializes
        integers as regular string and json dumps everything else.
        """
        return json.dumps(value, ensure_ascii=False, default=json_util.default)

    def load_object(self, value):
        """The reversal of :meth:`dump_object`.  This might be called with
        None.
        """
        if value is None:
            return None
        return json.loads(value)

    def exists(self, key):
        return self._read_client.exists(self._get_prefix() + key)

    def empty(self, key):
        return not self.exists(key)

    def delete(self, key):
        return self._write_client.delete(self._get_prefix() + key)

    def delete_many(self, *keys):
        if not keys:
            return
        if self.key_prefix:
            keys = [self._get_prefix() + key for key in keys]
        return self._write_client.delete(*keys)
