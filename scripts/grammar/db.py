"""PostgreSQL helpers for grammar tagging scripts."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def load_db_env(env_path: Path | None = None) -> None:
    if env_path is None:
        env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
    load_dotenv(env_path)


def db_connect() -> psycopg.Connection:
    load_db_env()
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "lingraft_dev"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
    )
