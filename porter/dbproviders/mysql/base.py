#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql


class BaseMySQL:
    def __init__(self, host="localhost", port=80, db=None, password=None, user=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.user = user

    def execute(self, sql, **kwargs):
        pass

    def insert(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    def delete(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    def update(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    def select(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    @staticmethod
    def escape(text):
        if isinstance(text, str):
            return f"'{pymysql.escape_string(text)}'"
        return text
