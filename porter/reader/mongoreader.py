#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time

from porter.dbproviders.mongo import Mongo
from porter.reader.base import BaseReader

from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


class MongoReader(BaseReader):
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
        self.collection = db_config["collection"]
        self.user = db_config["user"]
        self.password = db_config["password"]
        self.columns = db_config["column"] or None
        self.appendices = db_config["appendices"]
        self._client = Mongo(**db_config)
        self.total = 0

    def sync(self):
        self._migrate()

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

        logger.info(f"complete migration for {self.db}.{self.collection}, clean cache")
        self.cache.hdel(self.cache_key, ["count", "page", "total", "record", "_id"])
        self._client.close()

    def _extract(self):
        last_id = self.cache.get(self.cache_key, "_id")
        if last_id:
            last_id = ObjectId(last_id)
        records, last_id = self._client.pagination(
            page_size=self.limit, last_id=last_id, fields=self.columns
        )
        if records:
            self.cache.set(self.cache_key, "record", records[-1])
            self.cache.set(self.cache_key, "_id", str(last_id))
        return records

    def count(self):
        return self._client.collection.find().count()

    def append(self, values):
        for v in values:
            for a in self.appendices:
                key, val = a.split(":")
                v[key] = val
            yield v

    def filter(self, values):
        if not self.columns:
            return values

        columns = set(self.columns)
        return ({k: v for k, v in val.items() if k in columns} for val in values)

    def push(self, values):
        if values:
            values = self.append(self.filter(values))
            self.queue.push(self.queue_key, values)

    def status(self):
        count = self.cache.get(self.cache_key, "count")
        page = self.cache.get(self.cache_key, "page")
        record = self.cache.get(self.cache_key, "record")
        object_id = self.cache.get(self.cache_key, "_id")
        return {
            "db": self.db,
            "collection": self.collection,
            "count": count,
            "page": page,
            "_id": object_id,
            "record": record,
        }
