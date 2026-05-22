import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import DeclarationCreate, StoredDeclaration


class DeclarationStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS declarations (
                    record_id TEXT PRIMARY KEY,
                    producer_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    declared_quantities_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_declarations_lookup
                ON declarations (producer_id, month, created_at)
                """
            )

    def create(self, payload: DeclarationCreate) -> StoredDeclaration:
        record_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO declarations (
                    record_id, producer_id, month, declared_quantities_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    payload.producer_id,
                    payload.month,
                    json.dumps(payload.declared_quantities_kg, sort_keys=True),
                    created_at.isoformat(),
                ),
            )
        return StoredDeclaration(
            record_id=record_id,
            created_at=created_at,
            **payload.model_dump(),
        )

    def get_latest(self, producer_id: str, month: str) -> StoredDeclaration | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_id, producer_id, month, declared_quantities_json, created_at
                FROM declarations
                WHERE producer_id = ? AND month = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (producer_id, month),
            ).fetchone()
        if row is None:
            return None
        return StoredDeclaration(
            record_id=row["record_id"],
            producer_id=row["producer_id"],
            month=row["month"],
            declared_quantities_kg=json.loads(row["declared_quantities_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
