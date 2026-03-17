from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Iterable, Any

class PostgresConnector:
    _instance: Optional["PostgresConnector"] = None

    def __new__(cls, *args, **kwargs) -> "PostgresConnector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        user = os.getenv("POSTGRES_USER", "admin")
        password = os.getenv("POSTGRES_PASSWORD", "admin")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        dbname = os.getenv("POSTGRES_DB", "FLIGHTSASL")

        self._conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            cursor_factory=RealDictCursor
        )
        self._initialized = True

    def execute(self, query: str, params: Optional[Iterable[Any]] = None, fetch: str = "all"):
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                if fetch == "one":
                    return cur.fetchone()
                if fetch == "all":
                    return cur.fetchall()
                return None
        except psycopg2.Error:
            self._conn.rollback()
            raise

    def insert_one(self, query: str, params: Iterable[Any]):
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                self._conn.commit()
                return cur.rowcount
        except psycopg2.Error:
            self._conn.rollback()
            raise

    def insert_many(self, query: str, params_list: Iterable[Iterable[Any]]):
        with self._conn.cursor() as cur:
            cur.executemany(query, params_list)
            self._conn.commit()
            return cur.rowcount

    def update_one(self, query: str, params: Iterable[Any]):
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            self._conn.commit()
            return cur.rowcount

    def delete_one(self, query: str, params: Iterable[Any]):
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            self._conn.commit()
            return cur.rowcount

    def get_pg() -> PostgresConnector:
        return PostgresConnector()

    def close(self):
        self._conn.close()