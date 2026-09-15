import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class LocalPersistentQueue:
    def __init__(self, db_path: str = "data/queue.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )

        self._create_tables()

    def _create_tables(self):
        self.connection.execute("""
               CREATE TABLE IF NOT EXISTS processed_windows (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT NOT NULL,
                   samples TEXT NOT NULL,
                   features TEXT NOT NULL,
                   anomaly INTEGER NOT NULL,
                   uploaded INTEGER NOT NULL DEFAULT 0,
                   created_at TEXT NOT NULL
               )
           """)

        self.connection.commit()

    def save_window(self, timestamp: str, samples: list[float], features: dict, anomaly: bool):
        created_at = datetime.now(timezone.utc).isoformat()

        cursor = self.connection.execute(
            """
            INSERT INTO processed_windows (
                timestamp,
                samples,
                features,
                anomaly,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                json.dumps(samples),
                json.dumps(features),
                int(anomaly),
                created_at,
            ),
        )

        self.connection.commit()

    def get_pending_windows(self, limit: int = 100):
        rows = self.connection.execute(
            """
            SELECT
                id,
                timestamp,
                samples,
                features,
                anomaly
            FROM processed_windows
            WHERE uploaded = 0
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "samples": json.loads(row[2]),
                "features": json.loads(row[3]),
                "anomaly": bool(row[4]),
            }
            for row in rows
        ]

    def delete_windows(self, ids: list[int]) -> None:
        if not ids:
            return

        placeholders = ",".join("?" for _ in ids)

        with self.connection:
            self.connection.execute(
                f"""
                DELETE FROM processed_windows
                WHERE id IN ({placeholders})
                """,
                ids,
            )