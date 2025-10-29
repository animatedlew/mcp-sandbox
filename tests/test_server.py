from pathlib import Path
import sqlite3
from unittest.mock import MagicMock

import pytest

from mcp_sandbox.server import database, tools


class TestDatabase:
    def test_db_path_creation(self):
        assert Path("data/sample.db") == database.DB_PATH

    def test_get_db_connection(self):
        conn = database.get_db_connection()
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_initialize_database_creates_table(self):
        if database.DB_PATH.exists():
            database.DB_PATH.unlink()

        database.initialize_database()

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result["name"] == "users"
        conn.close()

    def test_initialize_database_idempotent(self):
        database.initialize_database()
        database.initialize_database()  # Should not raise error

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]
        # Sample data should only be inserted once
        assert count == 5
        conn.close()


class TestTools:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        database.initialize_database()

    def test_register_tools(self):
        mock_mcp = MagicMock()
        mock_mcp.tool = MagicMock(return_value=lambda f: f)

        tools.register_tools(mock_mcp)

        assert mock_mcp.tool.call_count == 5

    def test_execute_sql_query_select(self):
        mock_mcp = MagicMock()
        tools.register_tools(mock_mcp)

        from mcp_sandbox.server.tools import execute_sql_query

        result = execute_sql_query("SELECT * FROM users LIMIT 1")

        assert result["success"] is True
        assert "data" in result
        assert result["row_count"] == 1
        assert len(result["data"]) == 1

    def test_execute_sql_query_with_error(self):
        from mcp_sandbox.server.tools import execute_sql_query

        result = execute_sql_query("SELECT * FROM nonexistent_table")

        assert result["success"] is False
        assert "error" in result
        assert "SQLite error" in result["error"]

    def test_get_database_schema(self):
        from mcp_sandbox.server.tools import get_database_schema

        result = get_database_schema()

        assert result["success"] is True
        assert result["table_count"] >= 1
        assert "tables" in result
        assert any(t["name"] == "users" for t in result["tables"])

    def test_get_table_info_existing_table(self):
        from mcp_sandbox.server.tools import get_table_info

        result = get_table_info("users")

        assert result["success"] is True
        assert result["table_name"] == "users"
        assert result["column_count"] == 5
        assert result["row_count"] >= 5

    def test_get_table_info_nonexistent_table(self):
        from mcp_sandbox.server.tools import get_table_info

        result = get_table_info("nonexistent_table")

        assert result["success"] is False
        assert "does not exist" in result["error"]

    def test_insert_user_success(self):
        from mcp_sandbox.server.tools import insert_user

        result = insert_user("Test User", "test@example.com", 25)

        assert result["success"] is True
        assert "user_id" in result
        assert result["user"]["name"] == "Test User"
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["age"] == 25

    def test_insert_user_duplicate_email(self):
        from mcp_sandbox.server.tools import insert_user

        insert_user("User1", "duplicate@example.com", 30)
        result = insert_user("User2", "duplicate@example.com", 35)

        assert result["success"] is False
        assert "already registered" in result["error"]

    def test_insert_user_invalid_name(self):
        from mcp_sandbox.server.tools import insert_user

        result = insert_user("", "test@example.com", 25)

        assert result["success"] is False
        assert "Name cannot be empty" in result["error"]

    def test_insert_user_invalid_email(self):
        from mcp_sandbox.server.tools import insert_user

        result = insert_user("Test User", "invalid-email", 25)

        assert result["success"] is False
        assert "Invalid email" in result["error"]

    def test_insert_user_invalid_age(self):
        from mcp_sandbox.server.tools import insert_user

        result = insert_user("Test User", "test@example.com", 200)

        assert result["success"] is False
        assert "Age must be between" in result["error"]

    def test_search_users_no_filters(self):
        from mcp_sandbox.server.tools import search_users

        result = search_users()

        assert result["success"] is True
        assert "users" in result
        assert result["count"] >= 5

    def test_search_users_with_search_term(self):
        from mcp_sandbox.server.tools import search_users

        result = search_users(search_term="Alice")

        assert result["success"] is True
        assert result["count"] >= 1
        assert any("Alice" in user["name"] for user in result["users"])

    def test_search_users_with_age_range(self):
        from mcp_sandbox.server.tools import search_users

        result = search_users(min_age=30, max_age=40)

        assert result["success"] is True
        for user in result["users"]:
            assert 30 <= user["age"] <= 40

    def test_search_users_with_limit(self):
        from mcp_sandbox.server.tools import search_users

        result = search_users(limit=2)

        assert result["success"] is True
        assert result["count"] <= 2
