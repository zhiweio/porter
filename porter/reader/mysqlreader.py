#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time

from porter.dbproviders.mysql import MySQL
from porter.exceptions import InvalidConfiguration
from porter.reader.base import BaseReader

logger = logging.getLogger(__name__)


class MySQLReader(BaseReader):
    def __init__(
        self, db_config, redis_config, limit=1000, scale=3, block=True, sleep=10
    ):
        super().__init__(
            redis_config=redis_config,
            limit=limit,
            scale=scale,
            block=block,
            sleep=sleep,
        )
        self.db = db_config["db"]
        self.port = db_config["port"]
        self.table = db_config.pop("table")
        self.user = db_config["user"]
        self.password = db_config["password"]
        self.pk = db_config.pop("pk")
        if not self.pk:
            raise InvalidConfiguration(f"Require primary key")

        self.columns = db_config.pop("column") or ["*"]
        self.append_db_info = db_config["append_db_info"]
        self.appendices = db_config["appendices"]
        self._client = MySQL.client(provider="mysql", **db_config)
        self.total = 0

    def sync(self):
        self._migrate()

    def reset(self, db=None, table=None):
        if db:
            self.db = db
        if table:
            self.table = table

    def _migrate(self):
        page = self.cache.get(self.cache_key, "page") or 0
        count = self.cache.get(self.cache_key, "count") or 1
        self.total = self.cache.get(self.cache_key, "total") or self.count()
        logger.info(
            f"continue at page: \33[0;32m{page}\33[0m\tcount: \33[0;32m{count}\33[0m"
        )

        while count < self.total:
            if self.block:
                if self.queue.len(self.queue_key) >= self.limit * self.scale:
                    logger.debug(f"wait for {self.sleep}s...")
                    time.sleep(self.sleep)
                    continue

            self.push(self._extract())
            logger.debug(f"{self.limit} records pushed")
            count += self.limit
            page += 1
            self.cache.setmany(
                self.cache_key,
                mapping={"page": page, "count": count, "total": self.total},
            )

        logger.info(f"complete migration for {self.db}.{self.table}, clean cache")
        self.cache.hdel(self.cache_key, ["count", "page", "total", "record", self.pk])
        self._client.close()

    def _extract(self):
        fields = self.columns + [self.pk]
        pk_v = self.cache.get(self.cache_key, self.pk)
        if pk_v:
            pk_v = self._client.escape(pk_v)
            sql = (
                f'SELECT {",".join(fields)} '
                f"FROM {self.table} "
                f"WHERE {self.pk} > {pk_v} "
                f"ORDER BY {self.pk} LIMIT {self.limit}"
            )
        else:
            sql = (
                f'SELECT {",".join(fields)} '
                f"FROM {self.table} "
                f"ORDER BY {self.pk} LIMIT {self.limit}"
            )

        records = self._client.select(sql)
        if records:
            self.cache.set(self.cache_key, "record", records[-1])
            self.cache.set(self.cache_key, self.pk, records[-1][self.pk])
        return records

    def count(self):
        sql = f"SELECT COUNT({self.pk}) AS total FROM {self.table}"
        ret = self._client.select(sql)
        return int(ret[0]["total"])

    def filter(self, values):
        if self.columns == ["*"]:
            return values

        columns = set(self.columns)
        return ({k: v for k, v in val.items() if k in columns} for val in values)

    def append(self, values):
        for v in values:
            if self.append_db_info:
                v["porter_db"] = self.db
                v["porter_table"] = self.table
            for a in self.appendices:
                key, val = a.split(":")
                v[key] = val
            yield v

    def push(self, values):
        if values:
            values = self.append(self.filter(values))
            self.queue.push(self.queue_key, values)

    def status(self):
        count = self.cache.get(self.cache_key, "count")
        page = self.cache.get(self.cache_key, "page")
        record = self.cache.get(self.cache_key, "record")
        pk_v = self.cache.get(self.cache_key, self.pk)
        return {
            "db": self.db,
            "table": self.table,
            "count": count,
            "page": page,
            self.pk: pk_v,
            "record": record,
        }
