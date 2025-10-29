# MCP Sandbox - Claude + MCP Server Integration

A production-ready Python application demonstrating proper MCP (Model Context Protocol) implementation with Claude API and modular architecture.

## 🚀 What This Is

This project showcases **production-ready MCP integration** with:
- **Modular Architecture**: Separate client and server packages for clarity
- **MCP Protocol**: Proper stdio transport with separate server process
- **Real MCP Server**: Using official `mcp` library with FastMCP
- **SQLite Database**: Real data persistence and operations
- **Production Features**: Error handling, monitoring, metrics, and retry logic
- **Comprehensive Testing**: 45 tests covering all functionality

Perfect for learning MCP concepts and building production-ready MCP integrations.

## 📁 Project Structure

```
mcp-sandbox/
├── main.py                           # 🚀 MAIN ENTRY POINT
├── pyproject.toml                    # Poetry dependencies & config
├── Makefile                          # Development commands
├── data/                             # SQLite database files
├── logs/                             # Application logs
├── config/                           # MCP server configuration
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md               # Module architecture details
│   └── PRODUCTION.md                 # Production deployment guide
├── tests/                            # Test suite (45 tests)
│   ├── test_main.py                  # Main entry point tests
│   ├── test_client.py                # Client tests
│   └── test_server.py                # Server tests
└── src/
    └── mcp_sandbox/                  # Main package
        ├── __init__.py               # Package exports
        ├── client/                   # MCP Client (connects to Claude)
        │   ├── __init__.py           # Client exports
        │   ├── app.py                # MCPClient - main orchestration
        │   ├── session.py            # MCPSessionManager - server connections
        │   ├── metrics.py            # Request metrics collection
        │   └── chat.py               # MCPChat - interactive interface
        └── server/                   # MCP Server (provides tools)
            ├── __init__.py           # Server exports
            ├── __main__.py           # Module entry point (python -m)
            ├── app.py                # FastMCP server setup
            ├── database.py           # SQLite operations
            └── tools.py              # MCP tool definitions (5 tools)
```

## 🔧 Key Components

### 1. **Main Entry Point (`main.py`)**
- Demo mode with 6 example queries
- Interactive chat with Claude
- Simple command-line interface

### 2. **Client Package (`client/`)**
- **`app.py`** - `MCPClient` class for Claude API integration
  - Enhanced error handling with retry logic and exponential backoff
  - Request metrics tracking
  - Conversation management
- **`session.py`** - `MCPSessionManager` for MCP server connections
  - JSON-based configuration management
  - Health monitoring and automatic recovery
  - Tool execution routing
- **`metrics.py`** - Request metrics and reporting
- **`chat.py`** - `MCPChat` interactive interface
  - Commands: `/help`, `/clear`, `/metrics`, `/quit`
  - Natural language database interactions

### 3. **Server Package (`server/`)**
- **`app.py`** - FastMCP server setup and initialization
- **`database.py`** - SQLite connection and schema management
- **`tools.py`** - 5 MCP tool implementations:
  - `execute_sql_query` - Parameterized SQL queries
  - `get_database_schema` - Complete database structure
  - `get_table_info` - Detailed table analysis
  - `insert_user` - Safe user insertion with validation
  - `search_users` - Flexible user search with filters
- **`__main__.py`** - Module entry point (`python -m mcp_sandbox.server`)

## 🎯 Features

✅ **Modular Architecture** - Separate client and server packages  
✅ **Production-Ready** - Error handling, monitoring, metrics, retry logic  
✅ **Real MCP Server** - Official `mcp` library with FastMCP  
✅ **Comprehensive Testing** - 45 tests with 100% pass rate  
✅ **Structured Logging** - File-based logs with stderr separation  
✅ **Health Monitoring** - Automatic server health checks  
✅ **Configuration Management** - JSON-based server configuration  
✅ **Interactive Chat** - Natural language database interactions  
✅ **Tool Calling** - Claude can use all 5 database tools  
✅ **SQLite Backend** - Real data persistence  
✅ **Poetry Management** - Modern dependency management  
✅ **Code Quality** - Ruff, isort, and comprehensive linting  

## 🚀 Quick Start

### 1. **Setup Environment**
```bash
# Clone and setup
cd mcp-sandbox
poetry install

# Set up your Claude API key
echo "export ANTHROPIC_API_KEY=your_key_here" > .envrc
source .envrc  # or use direnv
```

### 2. **Run Demos**

**Using Make Commands (Recommended):**
```bash
# Run demo with 6 example queries
make demo

# Interactive chat with Claude
make chat

# Run test suite (45 tests)
make test

# Format and check code
make check

# Complete development setup
make dev-setup

# See all available commands
make help
```

**Using Poetry Scripts:**
```bash
# Run demo
poetry run demo

# Interactive chat
poetry run chat

# Run test suite
poetry run pytest
```

**Manual Execution:**
```bash
# Demo mode
poetry run python main.py

# Interactive chat mode
poetry run python main.py --chat
```

### 3. **Get Help**
```bash
poetry run python main.py --help
```

## 💬 Example Interactions

```
🧑‍💻 You: What tables are in my database?

🤖 Claude: Based on the schema, there is currently 1 table:

1. `users` table with columns:
   - id (INTEGER, Primary Key, Auto-incrementing)
   - name (TEXT, Not Null) 
   - email (TEXT, Unique)
   - age (INTEGER)
   - created_at (DATETIME, Default: current timestamp)
```

```
🧑‍💻 You: Show me all users over 30 years old

🤖 Claude: [Executes search_users tool with min_age filter]

Found 2 users over 30:
1. Bob Smith (34 years old, bob@test.com)
2. Alice Johnson (32 years old, alice@test.com)
```

```
🧑‍💻 You: Add a new user named Sarah with email sarah@test.com and age 28

🤖 Claude: [Uses insert_user tool with validation]

✅ Successfully added Sarah to the database!
- Name: Sarah, Email: sarah@test.com, Age: 28, ID: 8
```

## 🧪 Testing

The project includes comprehensive tests covering all components:

### **Running Tests**
```bash
# Run all tests (recommended)
make test

# Alternative syntax
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_client.py

# Run specific test
poetry run pytest tests/test_main.py::TestMainEntryPoints::test_run_demo
```

### **Test Coverage (45 Tests)**
- **Main Entry Points** (10 tests) - CLI, demo mode, chat mode, error handling
- **Client Package** (16 tests) - Metrics collection, session management, configuration
- **Server Package** (19 tests) - Database operations, tool execution, validation

### **Test Structure**
```
tests/
├── conftest.py          # Test configuration and fixtures
├── test_main.py         # Main entry point tests (10 tests)
├── test_client.py       # Client package tests (16 tests)
└── test_server.py       # Server package tests (19 tests)
```

**Key Features:**
- ✅ 100% test pass rate with zero warnings
- ✅ Async test support with pytest-asyncio
- ✅ Proper mock configuration for coroutines
- ✅ Comprehensive coverage of error scenarios

## 🛠️ Architecture

### **System Architecture**
```
main.py
   ↓
MCPClient (client/app.py)
   ↓
MCPSessionManager (client/session.py)
   ↓
[stdio transport / JSON-RPC]
   ↓
FastMCP Server (server/app.py)
   ↓
Tools (server/tools.py)
   ↓
SQLite Database (server/database.py)
```

### **Key Design Principles**
- ✅ **Modularity** - Separate packages for client and server
- ✅ **MCP Protocol** - Industry standard stdio transport
- ✅ **Process Isolation** - Server runs as separate process
- ✅ **JSON-RPC Communication** - Proper MCP message handling
- ✅ **Production Ready** - Error handling, monitoring, metrics
- ✅ **Testability** - Comprehensive test coverage

### **Module Responsibilities**
- **Client Package**: Claude API integration, session management, metrics
- **Server Package**: MCP tool implementation, database operations
- **Main Entry**: CLI interface, demo and chat modes

## 🧪 Usage Modes

### **Demo Mode**
- Runs 6 example queries showcasing all tools
- Perfect for testing and demonstration
- Shows MCP protocol in action

```bash
make demo
# or
poetry run demo
```

### **Interactive Chat**  
- Natural language interface to your database
- Full conversation with Claude using tools
- Commands: `/help`, `/clear`, `/metrics`, `/quit`

```bash
make chat
# or
poetry run chat
```

## 🔍 Key Learning Areas

### **1. MCP Protocol Implementation**
- Stdio transport setup and communication (`client/session.py`)
- JSON-RPC message handling
- Tool definition and execution (`server/tools.py`)
- Error handling and recovery with retry logic

### **2. FastMCP Server Development**
- Tool registration with decorators (`server/tools.py`)
- Input validation and schema definition
- Database operations with security (`server/database.py`)
- Module-based server execution (`server/__main__.py`)

### **3. Claude API Integration**
- Tool calling with proper formatting (`client/app.py`)
- Conversation management
- Tool result processing
- Request metrics collection (`client/metrics.py`)
- Exponential backoff for rate limits

### **4. Modular Architecture**
- Package structure and organization
- Separation of concerns (client vs server)
- Configuration management (`client/session.py`)
- Logging with stdout/stderr separation

## 📊 Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Dependencies

**Core:**
- `mcp` ^1.0.0 - Official Model Context Protocol library
- `anthropic` ^0.34.0 - Claude API client
- `python-dotenv` ^1.0.0 - Environment variable management
- `httpx` <0.28 - HTTP client (version pinned for compatibility)

**Built-in:**
- `sqlite3` - Database operations
- `asyncio` - Async support
- `pathlib` - File path handling

## 🛠️ Development Workflow

The project includes a comprehensive Makefile for streamlined development:

### **Development Commands**
```bash
# Complete development setup
make dev-setup              # Install deps, check code, run tests

# Code quality and formatting
make lint                    # Check code quality (no fixes)
make format                  # Format code with ruff and isort
make check                   # Check and auto-fix all issues

# Testing and demos
make test                    # Run test suite
make demo                    # Quick demo (direct mode)
make chat                    # Interactive chat (direct mode)
make demo-mcp                # Demo with MCP protocol
make chat-mcp                # Chat with MCP protocol

# Maintenance
make clean                   # Clean cache files
make install                 # Install dependencies
make all                     # Complete CI pipeline
```

### **Code Quality Tools**
- **Ruff**: Modern Python linter and formatter
- **isort**: Import sorting and organization
- **pytest**: Comprehensive testing framework
- **Poetry**: Dependency management and virtual environments

All tools are configured in `pyproject.toml` with project-specific settings for optimal code quality while maintaining readability.

## 🏆 Key Achievements

This project demonstrates:

1. **Real MCP Implementation** - Uses official MCP library with FastMCP
2. **Production Patterns** - Error handling, retry logic, monitoring, metrics
3. **Modular Architecture** - Clean separation of client and server concerns
4. **Comprehensive Testing** - 45 tests with 100% pass rate, zero warnings
5. **Modern Tooling** - Poetry, Ruff, isort, proper package structure
6. **Code Quality** - Strict linting, formatting, and type checking
7. **Educational Value** - Well-documented, clear code organization

## 🤝 Next Steps

**For Learning:**
- Explore the modular architecture in `src/mcp_sandbox/`
- Read the code - it's well-documented and organized
- Experiment with the interactive chat features
- Add new tools to `server/tools.py`
- Modify and extend the client functionality

**For Production:**
- Review the production deployment guide in `docs/PRODUCTION.md`
- Add authentication and authorization
- Implement rate limiting and resource management  
- Connect to real data sources and APIs
- Deploy as microservices or containers
- Set up monitoring and alerting

## 📚 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Poetry Documentation](https://python-poetry.org/docs/)

---

**Happy Learning & Building!** 🎉

This sandbox provides practical patterns for real-world MCP applications. Start with the demos, explore the code, and build your own MCP integrations!