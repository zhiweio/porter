#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import logging
import subprocess
import sys
import time

from porter.reader.base import BaseReader
from porter.utils import batch_read_file

logger = logging.getLogger(__name__)


class FileReader(BaseReader):
    def __init__(
        self, file_config, redis_config, limit=1000, scale=3, block=True, sleep=10
    ):
        super().__init__(
            redis_config=redis_config,
            limit=limit,
            scale=scale,
            block=block,
            sleep=sleep,
        )
        self.file_path = file_config["path"]
        self.delimiter = file_config["delimiter"]
        self.has_header = file_config["header"]
        self.appendices = file_config["appendices"]
        self.header = None
        self.total = self.cache.get(self.cache_key, "total") or self.count()

    def sync(self):
        def _wait_for_push(bulks):
            while True:
                # non-block, no resumption
                if not self.block:
                    self.push(bulks)
                    break
                else:
                    # enable block mode
                    if self.queue.len(self.cache_key) >= self.limit * self.scale:
                        logger.debug(f"wait for {self.sleep}s...")
                        time.sleep(self.sleep)
                    else:
                        self.push(bulks)
                        logger.debug(f"cache linenum: {i}")
                        self.cache.set(self.cache_key, "count", i)
                        break

        linenum = 0
        if self.cache.exists(self.cache_key):
            linenum = self.cache.get(self.cache_key, "count")
            logger.info(
                f"continue at linenum: \33[0;32m{linenum}\33[0m"
                f"\ttotal: \33[0;32m{self.total}\33[0m"
            )

        with codecs.open(self.file_path, encoding="utf8") as f_obj:
            logger.info(f"{self.file_path} opened...")
            logger.debug(f"has header: {self.has_header}")
            if self.has_header:
                self.header = f_obj.readline().rstrip("\n").split(self.delimiter)
                logger.info("header: {}".format(self.header))
            if linenum:
                for i, n_lines in batch_read_file(self.limit, f_obj):
                    # skip line has pushed
                    if i + 1 < linenum:
                        continue
                    _wait_for_push(n_lines)

            else:
                self.cache.setmany(
                    self.cache_key, mapping={"total": self.total, "count": 0}
                )
                logger.info("traverse file...")
                for i, n_lines in batch_read_file(self.limit, f_obj):
                    _wait_for_push(n_lines)
        # complete
        self.cache.set(self.cache_key, "count", self.total)

    def append(self, values):
        for v in values:
            for a in self.appendices:
                if self.has_header:
                    key, val = a.split(":")
                    v[key] = val
                else:
                    v = f"{v}{self.delimiter}{a}"
            yield v

    def push(self, values):
        if self.has_header:
            values = (
                dict(zip(self.header, line.rstrip("\n").split(self.delimiter)))
                for line in values
            )
        else:
            values = (line.rstrip("\n") for line in values)
        values = self.append(values)
        self.queue.push(self.queue_key, values)

    def count(self):
        # exclude header line
        with codecs.open(self.file_path, encoding="utf8") as fd:
            return sum(1 for _ in fd) - 1

    def status(self):
        count = self.cache.get(self.cache_key, "count")
        total = self.cache.get(self.cache_key, "total")
        return {"count": count, "total": total}
