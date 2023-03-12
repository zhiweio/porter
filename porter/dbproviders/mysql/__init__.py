#!/usr/bin/env python
# -*- coding: utf-8 -*-

from porter.dbproviders.mysql.dbapi import DbMySQL


class MySQL:
    @staticmethod
    def client(db, host="localhost", port=80, provider="mysql", **kwargs):
        _client = None
        if provider == "proxy":
            raise NotImplementedError

        elif provider == "mysql":
            user = kwargs["user"]
            password = kwargs["password"]
            _client = DbMySQL.client(
                host=host, port=port, db=db, password=password, user=user
            )

        return _client
