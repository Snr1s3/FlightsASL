from __future__ import annotations

import os
from typing import Any, Iterable, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


class MongoConnector:
    _instance: Optional["MongoConnector"] = None

    def __new__(cls, *args, **kwargs) -> "MongoConnector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB", "FLIGHTSASL")
        self._client = MongoClient(uri)
        self._db = self._client[db_name]
        self._initialized = True

    def collection(self, name: str) -> Collection:
        return self._db[name]

    def insert_one(self, collection: str, document: dict) -> InsertOneResult:
        return self.collection(collection).insert_one(document)

    def insert_many(self, collection: str, documents: Iterable[dict]):
        return self.collection(collection).insert_many(documents)

    def find_one(self, collection: str, query: dict) -> Optional[dict]:
        return self.collection(collection).find_one(query)

    def find(self, collection: str, query: dict, limit: int = 0) -> list[dict]:
        cursor = self.collection(collection).find(query)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update_one(self, collection: str, query: dict, update: dict) -> UpdateResult:
        return self.collection(collection).update_one(query, update)

    def delete_one(self, collection: str, query: dict) -> DeleteResult:
        return self.collection(collection).delete_one(query)

    def delete_many(self, collection: str, query: dict) -> DeleteResult:
        return self.collection(collection).delete_many(query)