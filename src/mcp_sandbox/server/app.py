from mcp.server import FastMCP

from .database import initialize_database
from .tools import register_tools


mcp = FastMCP("SQLite Database Server")

register_tools(mcp)


def run_server():
    import sys

    # Print to stderr to avoid interfering with JSON-RPC on stdout
    print("🚀 Starting MCP Server - SQLite Database", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    initialize_database()

    print("📊 Database initialized", file=sys.stderr)
    print("🔧 Available tools:", file=sys.stderr)
    print("   • execute_sql_query - Run SQL queries", file=sys.stderr)
    print("   • get_database_schema - Get database structure", file=sys.stderr)
    print("   • get_table_info - Analyze specific tables", file=sys.stderr)
    print("   • insert_user - Add new users safely", file=sys.stderr)
    print("   • search_users - Find users with filters", file=sys.stderr)
    print(file=sys.stderr)
    print("🌐 Server ready for MCP connections!", file=sys.stderr)
    print("💡 Use stdio transport to connect", file=sys.stderr)
    print(file=sys.stderr)

    mcp.run()


if __name__ == "__main__":
    run_server()
