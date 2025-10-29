import contextlib
import os
import sqlite3
import tempfile

import pytest


@pytest.fixture(scope="session")
def test_database():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    test_users = [
        ("Alice Johnson", "alice@test.com", 28),
        ("Bob Smith", "bob@test.com", 34),
        ("Carol Davis", "carol@test.com", 26),
    ]

    cursor.executemany(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)", test_users
    )

    conn.commit()
    conn.close()

    yield path

    with contextlib.suppress(FileNotFoundError):
        os.unlink(path)


@pytest.fixture
def mock_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")


@pytest.fixture
def temp_workspace():
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_configure(config):
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
