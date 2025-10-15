import os
import sqlite3
from typing import List

from app.config import DB_FILE


class BrokerService:
    def __init__(self):
        self.db_path = DB_FILE
        self._ensure_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS brokers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            # Seed defaults if empty
            cur = conn.execute("SELECT COUNT(*) FROM brokers")
            if (cur.fetchone()[0] or 0) == 0:
                defaults = ["Nubank", "XP", "Clear", "BTG", "Inter"]
                conn.executemany(
                    "INSERT OR IGNORE INTO brokers (name) VALUES (?)",
                    [(n,) for n in defaults],
                )
                conn.commit()

    def list_all(self) -> List[str]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT name FROM brokers ORDER BY name COLLATE NOCASE ASC"
            )
            return [r[0] for r in cur.fetchall()]

    def add_broker(self, name: str) -> bool:
        name = (name or "").strip()
        if not name:
            return False
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO brokers (name) VALUES (?)",
                    (name,),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def rename_broker(self, old_name: str, new_name: str) -> bool:
        old_name = (old_name or "").strip()
        new_name = (new_name or "").strip()
        if not old_name or not new_name or old_name == new_name:
            return False
        with self._connect() as conn:
            # Atualiza investimentos vinculados
            conn.execute("UPDATE investments SET broker = ? WHERE broker = ?", (new_name, old_name))
            # Se já existir o novo, remover o antigo, senão atualizar o nome
            cur = conn.execute("SELECT COUNT(*) FROM brokers WHERE name = ?", (new_name,))
            exists_new = (cur.fetchone()[0] or 0) > 0
            if exists_new:
                conn.execute("DELETE FROM brokers WHERE name = ?", (old_name,))
            else:
                conn.execute("UPDATE brokers SET name = ? WHERE name = ?", (new_name, old_name))
            conn.commit()
            return True

    def delete_broker(self, name: str, reassign_to: str | None = None) -> bool:
        name = (name or "").strip()
        if not name:
            return False
        with self._connect() as conn:
            if reassign_to:
                reassign_to = reassign_to.strip()
                if not reassign_to:
                    return False
                conn.execute("INSERT OR IGNORE INTO brokers (name) VALUES (?)", (reassign_to,))
                conn.execute("UPDATE investments SET broker = ? WHERE broker = ?", (reassign_to, name))
                conn.execute("DELETE FROM brokers WHERE name = ?", (name,))
                conn.commit()
                return True

            # Bloquear se houver investimentos ainda vinculados
            cur = conn.execute("SELECT COUNT(*) FROM investments WHERE broker = ?", (name,))
            used_count = cur.fetchone()[0] or 0
            if used_count > 0:
                return False
            conn.execute("DELETE FROM brokers WHERE name = ?", (name,))
            conn.commit()
            return True