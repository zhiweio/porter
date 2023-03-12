#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib.parse import quote_plus

from pymongo import MongoClient


class Mongo:
    def __init__(
        self,
        host="localhost",
        port=27017,
        db=None,
        collection=None,
        user=None,
        password=None,
        **kwargs,
    ):
        uri = f"mongodb://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db}"
        self.connection = MongoClient(uri)
        self.db = self.connection[db]
        self.collection = self.db[collection]

    def pagination(self, page_size, last_id=None, fields=None):
        """Function returns `page_size` number of documents after last_id
        and the new last_id.
        """
        if fields:
            fields = {k: 1 for k in fields}

        if last_id is None:
            cursor = self.collection.find(projection=fields).limit(page_size)
        else:
            cursor = self.collection.find(
                filter={"_id": {"$gt": last_id}}, projection=fields
            ).limit(page_size)

        data = [x for x in cursor]

        if not data:
            return None, None

        # Since documents are naturally ordered with _id, last document will
        # have max id.
        last_id = data[-1]["_id"]
        return data, last_id

    def close(self):
        self.connection.close()
