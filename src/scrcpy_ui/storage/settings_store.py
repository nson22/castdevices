"""Persistência das preferências do usuário num SQLite local (key-value)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def default_db_path() -> Path:
    app_data_dir = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )
    app_data_dir.mkdir(parents=True, exist_ok=True)
    return app_data_dir / "settings.sqlite3"


class SettingsStore:
    def __init__(self, db_path: Path | None = None):
        self._conn = sqlite3.connect(db_path or default_db_path(), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self._conn.commit()

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()
