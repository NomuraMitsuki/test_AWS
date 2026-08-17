"""Secrets Manager から RDS 接続情報を読み、psycopg で接続する。"""

from __future__ import annotations

import json
from typing import Any


def load_db_secret(secret_arn: str, client: Any = None) -> dict:
    if client is None:
        import boto3

        client = boto3.client("secretsmanager")
    raw = client.get_secret_value(SecretId=secret_arn)["SecretString"]
    secret = json.loads(raw)
    required = ("host", "dbname", "username", "password")
    missing = [k for k in required if not secret.get(k)]
    if missing:
        raise ValueError(f"DB secret に必須キーがありません: {', '.join(missing)}")
    return secret


def connect_from_secret(secret: dict):
    import psycopg

    return psycopg.connect(
        host=secret["host"],
        port=int(secret.get("port") or 5432),
        dbname=secret["dbname"],
        user=secret["username"],
        password=secret["password"],
        connect_timeout=10,
        sslmode="require",
        autocommit=False,
        cursor_factory=psycopg.ClientCursor,
    )
