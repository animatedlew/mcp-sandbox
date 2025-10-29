# MCP Sandbox - Module Architecture

This document describes the refactored modular architecture.

## Structure

```
src/mcp_sandbox/
├── __init__.py              # Main package exports
├── server/                  # MCP Server (provides tools)
│   ├── __init__.py         # Server exports
│   ├── __main__.py         # Module entry point (enables python -m)
│   ├── app.py              # FastMCP server setup (~40 lines)
│   ├── database.py         # SQLite connection & initialization (~55 lines)
│   └── tools.py            # Tool definitions (@mcp.tool decorators) (~270 lines)
└── client/                  # MCP Client (connects to Claude)
    ├── __init__.py         # Client exports
    ├── app.py              # MCPClient - main orchestration (~226 lines)
    ├── session.py          # MCPSessionManager - server connections (~227 lines)
    ├── metrics.py          # RequestMetrics & MetricsCollector (~55 lines)
    └── chat.py             # MCPChat - interactive UI (~113 lines)
```

## Module Responsibilities

### Server Package (`server/`)

**Purpose**: Runs as a separate process to provide MCP tools via stdio transport.

- **`database.py`**: Database connection management and initialization
  - `get_db_connection()`: Create SQLite connection with Row factory
  - `initialize_database()`: Set up tables and sample data
  
- **`tools.py`**: Tool definitions using FastMCP decorators
  - `register_tools(mcp)`: Register all 5 database tools
  - Tools: `execute_sql_query`, `get_database_schema`, `get_table_info`, `insert_user`, `search_users`
  
- **`app.py`**: Main server setup
  - Creates FastMCP instance
  - Registers tools
  - `run_server()`: Entry point for server execution
  
- **`__main__.py`**: Makes server runnable as module
  - Enables: `python -m mcp_sandbox.server`

### Client Package (`client/`)

**Purpose**: Connects to Claude's API and coordinates with MCP servers.

- **`metrics.py`**: Request metrics and reporting
  - `RequestMetrics`: Dataclass for individual request metrics
  - `MetricsCollector`: Aggregates and summarizes metrics
  
- **`session.py`**: MCP server session management
  - `MCPServerConfig`: Configuration dataclass
  - `MCPSessionManager`: Manages connections to MCP servers
    - Load configuration
    - Initialize server connections (stdio transport)
    - Execute tools on appropriate servers
    - Health checks
  
- **`app.py`**: Main client orchestration
  - `MCPClient`: Core client with Claude integration
    - Retry logic with exponential backoff
    - Tool execution routing
    - Conversation management
    - Error handling for timeouts and rate limits
  
- **`chat.py`**: Interactive chat interface
  - `MCPChat`: CLI chat system
    - Commands: `/help`, `/clear`, `/metrics`, `/quit`
    - User input loop
    - Command handling

## Key Design Decisions

### 1. Server as Module
The server runs as a Python module (`python -m mcp_sandbox.server`) rather than a script. This:
- Ensures proper package imports
- Makes the server portable
- Allows relative imports to work correctly

### 2. Stdout/Stderr Separation
MCP uses stdout for JSON-RPC communication, so:
- All print statements redirect to `stderr`
- Prevents interference with MCP protocol
- Logging stays on stderr

### 3. Configuration
- Uses module path `"mcp_sandbox.server"` instead of file paths
- Session manager detects module paths (no `.py` extension)
- Runs with `-m` flag automatically

### 4. Single Responsibility
Each module has one clear purpose:
- `database.py`: Only database operations
- `tools.py`: Only tool definitions
- `session.py`: Only session management
- `metrics.py`: Only metrics collection
- `chat.py`: Only UI/interaction

## Usage

### Run Demo
```bash
python main.py
# or
make demo
```

### Run Interactive Chat
```bash
python main.py --chat
# or
make chat
```

### Run Server Standalone
```bash
python -m mcp_sandbox.server
```

### Import in Code
```python
# Client
from mcp_sandbox.client import MCPClient, MCPChat

# Server
from mcp_sandbox.server import mcp, initialize_database
```

## Benefits

1. **Modularity**: Easy to test individual components
2. **Clarity**: Server vs client distinction is obvious
3. **Maintainability**: Small, focused modules (40-270 lines)
4. **Extensibility**: Easy to add new tools or client features
5. **Reusability**: Components can be imported separately

## Migration Notes

### Configuration

The configuration file `config/mcp.json`:
```json
{
  "servers": [{
    "name": "sqlite-database",
    "script_path": "mcp_sandbox.server",  // module path, not file path
    "enabled": true,
    "timeout": 30,
    "max_retries": 3,
    "health_check_interval": 60
  }],
  "log_level": "INFO"
}
```

### Package Exports

```python
# From src/mcp_sandbox/__init__.py
from .client import MCPChat, MCPClient
from .server import initialize_database, mcp

__all__ = ["MCPChat", "MCPClient", "initialize_database", "mcp"]
```

## Testing

All existing functionality preserved:
- ✅ Demo mode: 6/6 queries successful
- ✅ Chat mode: All commands working
- ✅ Tool execution: All 5 tools functional
- ✅ Error handling: Retry logic operational
- ✅ Metrics: Collection and reporting working
