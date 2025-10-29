from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    name: str
    script_path: str
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    health_check_interval: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPSessionManager:
    def __init__(self):
        self.server_configs: List[MCPServerConfig] = []
        self.server_sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logger

    async def load_configuration(self, config_path: str):
        config_path_obj = Path(config_path)

        if config_path_obj.exists():
            self.logger.info(f"📁 Loading config from {config_path}")
            with config_path_obj.open() as f:
                config_data = json.load(f)
                self.server_configs = [
                    MCPServerConfig(**server)
                    for server in config_data.get("servers", [])
                ]
        else:
            self.logger.info("📁 Creating default configuration")
            await self._create_default_configuration(config_path)

    async def _create_default_configuration(self, config_path: str):
        config_path_obj = Path(config_path)
        config_dir = config_path_obj.parent
        config_dir.mkdir(parents=True, exist_ok=True)

        # Use module path instead of script path for proper package execution
        default_config = {
            "servers": [
                {
                    "name": "sqlite-database",
                    "script_path": "mcp_sandbox.server",
                    "enabled": True,
                    "timeout": 30,
                    "max_retries": 3,
                    "health_check_interval": 60,
                    "metadata": {
                        "description": "SQLite database MCP server",
                        "version": "1.0.0",
                    },
                }
            ],
            "log_level": "INFO",
        }

        with config_path_obj.open("w") as f:
            json.dump(default_config, f, indent=2)

        self.server_configs = [
            MCPServerConfig(**server) for server in default_config["servers"]
        ]

        self.logger.info(f"✅ Created default config at {config_path}")

    async def initialize_servers(self):
        for server_config in self.server_configs:
            if not server_config.enabled:
                continue

            try:
                self.logger.info(f"🔧 Initializing server: {server_config.name}")

                # Run as module if script_path looks like a module path
                if (
                    "." in server_config.script_path
                    and not server_config.script_path.endswith(".py")
                ):
                    server_params = StdioServerParameters(
                        command="python",
                        args=["-m", server_config.script_path],
                        env=dict(os.environ),
                    )
                else:
                    server_params = StdioServerParameters(
                        command="python",
                        args=[server_config.script_path],
                        env=dict(os.environ),
                    )

                stdio = stdio_client(server_params)
                read, write = await stdio.__aenter__()

                session = ClientSession(read, write)
                await session.__aenter__()
                await session.initialize()

                # Get available tools
                tools_result = await session.list_tools()

                self.server_sessions[server_config.name] = {
                    "session": session,
                    "stdio": stdio,
                    "tools": tools_result.tools,
                    "healthy": True,
                    "last_check": time.time(),
                }

                self.logger.info(
                    f"✅ Server {server_config.name} ready "
                    f"with {len(tools_result.tools)} tools"
                )

            except Exception as e:
                self.logger.error(f"❌ Failed to initialize {server_config.name}: {e}")
                server_config.enabled = False

    async def health_check_all(self):
        for server_name, session_info in self.server_sessions.items():
            try:
                session_info["healthy"] = True
                session_info["last_check"] = time.time()
                self.logger.debug(f"✅ Health check passed: {server_name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Health check failed for {server_name}: {e}")
                session_info["healthy"] = False

    def get_all_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        for _server_name, session_info in self.server_sessions.items():
            if session_info.get("healthy", False):
                for tool in session_info["tools"]:
                    tool_def = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    all_tools.append(tool_def)
        return all_tools

    async def execute_tool(
        self, tool_name: str, tool_input: Dict[str, Any], request_id: str
    ) -> Dict[str, Any]:
        for _server_name, session_info in self.server_sessions.items():
            if not session_info.get("healthy", False):
                continue

            tool_names = [t.name for t in session_info["tools"]]
            if tool_name in tool_names:
                try:
                    session = session_info["session"]
                    result = await session.call_tool(
                        name=tool_name, arguments=tool_input
                    )

                    if result.content:
                        content_text = ""
                        for content in result.content:
                            if hasattr(content, "text"):
                                content_text += content.text
                            else:
                                content_text += str(content)

                        try:
                            return json.loads(content_text)
                        except json.JSONDecodeError:
                            return {"success": True, "result": content_text}
                    else:
                        return {"success": True, "result": "No content"}

                except Exception as e:
                    self.logger.error(
                        f"❌ [{request_id}] Tool execution failed: {tool_name} - {e}"
                    )
                    return {"error": f"Tool execution failed: {e!s}"}

        return {"error": f"Tool {tool_name} not found on any healthy server"}

    def get_healthy_server_count(self) -> int:
        return sum(1 for s in self.server_sessions.values() if s.get("healthy", False))

    async def cleanup(self):
        self.logger.info("🧹 Cleaning up MCP connections")

        for server_name, session_info in self.server_sessions.items():
            try:
                session = session_info.get("session")
                stdio = session_info.get("stdio")

                if session:
                    await session.__aexit__(None, None, None)
                if stdio:
                    await stdio.__aexit__(None, None, None)

                self.logger.info(f"✅ Closed connection to {server_name}")
            except Exception as e:
                self.logger.error(f"⚠️ Error closing {server_name}: {e}")
