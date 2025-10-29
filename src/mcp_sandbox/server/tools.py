import sqlite3
from typing import Any, Dict, List

from .database import DB_PATH, get_db_connection


def execute_sql_query(query: str, parameters: List[str] = None) -> Dict[str, Any]:
    if parameters is None:
        parameters = []

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)

        if query.strip().upper().startswith(("SELECT", "PRAGMA")):
            rows = cursor.fetchall()
            return {
                "success": True,
                "data": [dict(row) for row in rows],
                "row_count": len(rows),
                "query": query,
                "parameters": parameters,
            }
        else:
            conn.commit()
            return {
                "success": True,
                "rows_affected": cursor.rowcount,
                "message": "Query executed successfully",
                "query": query,
                "parameters": parameters,
            }

    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"SQLite error: {e!s}",
            "query": query,
            "parameters": parameters,
        }

    finally:
        conn.close()


def get_database_schema() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = []
        for row in cursor.fetchall():
            table_name = row["name"]

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [dict(col) for col in cursor.fetchall()]

            tables.append({"name": table_name, "sql": row["sql"], "columns": columns})

        return {
            "success": True,
            "database_path": str(DB_PATH),
            "table_count": len(tables),
            "tables": tables,
        }

    except sqlite3.Error as e:
        return {"success": False, "error": f"Error getting schema: {e!s}"}

    finally:
        conn.close()


def get_table_info(table_name: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table_name],
        )

        if not cursor.fetchone():
            return {"success": False, "error": f"Table '{table_name}' does not exist"}

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [dict(col) for col in cursor.fetchall()]

        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        row_count = cursor.fetchone()["count"]

        return {
            "success": True,
            "table_name": table_name,
            "columns": columns,
            "column_count": len(columns),
            "row_count": row_count,
        }

    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"Error getting table info: {e!s}",
            "table_name": table_name,
        }

    finally:
        conn.close()


def insert_user(name: str, email: str, age: int) -> Dict[str, Any]:
    if not name or not name.strip():
        return {"success": False, "error": "Name cannot be empty"}

    if not email or "@" not in email:
        return {"success": False, "error": "Invalid email address"}

    if not isinstance(age, int) or age <= 0 or age > 150:
        return {"success": False, "error": "Age must be between 1 and 150"}

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            [name.strip(), email.strip(), age],
        )
        conn.commit()

        user_id = cursor.lastrowid

        return {
            "success": True,
            "message": "User created successfully",
            "user_id": user_id,
            "user": {
                "id": user_id,
                "name": name.strip(),
                "email": email.strip(),
                "age": age,
            },
        }

    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            return {
                "success": False,
                "error": f"Email '{email}' is already registered",
            }
        else:
            return {"success": False, "error": f"Database constraint error: {e!s}"}

    except sqlite3.Error as e:
        return {"success": False, "error": f"Database error: {e!s}"}

    finally:
        conn.close()


def search_users(
    search_term: str = None,
    min_age: int = None,
    max_age: int = None,
    limit: int = 10,
) -> Dict[str, Any]:
    limit = min(limit, 100)

    conn = get_db_connection()
    cursor = conn.cursor()

    where_conditions = []
    parameters = []

    if search_term:
        where_conditions.append("(name LIKE ? OR email LIKE ?)")
        search_pattern = f"%{search_term}%"
        parameters.extend([search_pattern, search_pattern])

    if min_age is not None:
        where_conditions.append("age >= ?")
        parameters.append(min_age)

    if max_age is not None:
        where_conditions.append("age <= ?")
        parameters.append(max_age)

    query = "SELECT * FROM users"
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)
    query += " ORDER BY name LIMIT ?"
    parameters.append(limit)

    try:
        cursor.execute(query, parameters)
        users = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "users": users,
            "count": len(users),
            "search_criteria": {
                "search_term": search_term,
                "min_age": min_age,
                "max_age": max_age,
                "limit": limit,
            },
        }

    except sqlite3.Error as e:
        return {"success": False, "error": f"Search error: {e!s}"}

    finally:
        conn.close()


def register_tools(mcp):
    mcp.tool()(execute_sql_query)
    mcp.tool()(get_database_schema)
    mcp.tool()(get_table_info)
    mcp.tool()(insert_user)
    mcp.tool()(search_users)
