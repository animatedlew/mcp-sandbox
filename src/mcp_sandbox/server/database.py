from pathlib import Path
import sqlite3


DB_PATH = Path("data/sample.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        import sys

        print("🔧 Initializing sample database...", file=sys.stderr)

        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER NOT NULL CHECK (age > 0),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        sample_users = [
            ("Alice Johnson", "alice@example.com", 28),
            ("Bob Smith", "bob@example.com", 34),
            ("Carol Davis", "carol@example.com", 26),
            ("David Wilson", "david@example.com", 42),
            ("Eva Brown", "eva@example.com", 31),
        ]

        cursor.executemany(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)", sample_users
        )

        conn.commit()
        print("✅ Sample data initialized", file=sys.stderr)

    conn.close()
