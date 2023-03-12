#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import pymysql

from porter.dbproviders.mysql.base import BaseMySQL

logger = logging.getLogger(__name__)


class DbMySQL:
    @staticmethod
    def client(host, db, user, password="", port=3306, **kwargs):
        _client = MysqlHelper(host, port, db, password, user)
        return _client


class MysqlHelper(BaseMySQL):
    def __init__(self, host="localhost", port=3306, db=None, password="", user=None):
        super(MysqlHelper, self).__init__(
            host=host, port=port, db=db, password=password, user=user
        )
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db,
            port=self.port,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )
        self.cursor = None

    def execute(self, sql, **kwargs):
        if self.cursor is None:
            self.cursor = self.connection.cursor()
        self.cursor.execute(sql)

    def insert(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    def delete(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    def update(self, sql, **kwargs):
        return self.execute(sql, **kwargs)

    def select(self, sql, **kwargs):
        self.execute(sql, **kwargs)
        return self.cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()

    @staticmethod
    def escape(text):
        if isinstance(text, str):
            return f"'{pymysql.escape_string(text)}'"
        return text
