import asyncio
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Optional

import anthropic
from dotenv import load_dotenv

from .metrics import MetricsCollector, RequestMetrics
from .session import MCPSessionManager


Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("logs/mcp.log", mode="a"),
    ],
    force=True,
)

for mcp_logger_name in ["mcp", "mcp.client", "mcp.client.stdio"]:
    mcp_logger = logging.getLogger(mcp_logger_name)
    mcp_logger.handlers.clear()
    mcp_logger.addHandler(logging.StreamHandler(sys.stderr))
    mcp_logger.propagate = False

logger = logging.getLogger(__name__)

load_dotenv(".envrc")


class MCPClient:
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logger
        self.anthropic_client = None
        self.conversation_history = []
        self.config_path = config_path or "config/mcp.json"

        self.session_manager = MCPSessionManager()
        self.metrics_collector = MetricsCollector()

        Path("logs").mkdir(exist_ok=True)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in .envrc or environment."
            )

        try:
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            self.logger.info("✅ Anthropic client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            raise

    async def initialize(self) -> bool:
        self.logger.info("🚀 Initializing MCP client")

        try:
            await self.session_manager.load_configuration(self.config_path)
            await self.session_manager.initialize_servers()
            await self.session_manager.health_check_all()

            server_count = len(self.session_manager.server_sessions)
            self.logger.info(f"✅ MCP client ready with {server_count} servers")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize: {e}")
            return False

    async def chat_with_claude(self, user_message: str, max_retries: int = 3) -> str:
        request_id = f"req_{int(time.time() * 1000)}"
        metrics = RequestMetrics(request_id=request_id, start_time=time.time())

        self.logger.info(f"📨 [{request_id}] Processing request")

        for attempt in range(max_retries):
            try:
                response = await self._execute_chat(user_message, request_id)

                metrics.end_time = time.time()
                metrics.success = True
                self.metrics_collector.add_metric(metrics)

                elapsed = metrics.end_time - metrics.start_time
                self.logger.info(
                    f"✅ [{request_id}] Request completed in {elapsed:.2f}s"
                )

                return response

            except anthropic.APITimeoutError:
                self.logger.warning(
                    f"⏱️ [{request_id}] Timeout on attempt {attempt + 1}/{max_retries}"
                )
                if attempt == max_retries - 1:
                    metrics.error_type = "timeout"
                    metrics.end_time = time.time()
                    self.metrics_collector.add_metric(metrics)
                    return f"❌ Request timed out after {max_retries} attempts"
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except anthropic.RateLimitError:
                self.logger.warning(f"🚦 [{request_id}] Rate limit hit, waiting...")
                if attempt == max_retries - 1:
                    metrics.error_type = "rate_limit"
                    metrics.end_time = time.time()
                    self.metrics_collector.add_metric(metrics)
                    return "❌ Rate limit exceeded. Please try again later."
                await asyncio.sleep(5 * (attempt + 1))

            except Exception as e:
                self.logger.error(f"❌ [{request_id}] Error: {e}")
                metrics.error_type = type(e).__name__
                metrics.end_time = time.time()
                self.metrics_collector.add_metric(metrics)
                return f"❌ Error: {e!s}"

    async def _execute_chat(self, user_message: str, request_id: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})

        all_tools = self.session_manager.get_all_tools()

        if not all_tools:
            self.logger.warning(f"⚠️ [{request_id}] No healthy MCP servers available")
            return "❌ No MCP tools currently available. Please check server status."

        self.logger.info(
            f"🔧 [{request_id}] Using {len(all_tools)} tools from MCP servers"
        )

        system_message = """You are an AI assistant with access to MCP (Model Context Protocol) tools.

You have access to database operations and other tools provided by MCP servers.
Always explain your actions clearly and handle errors gracefully.

This environment has proper monitoring and error handling."""

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=system_message,
            messages=self.conversation_history,
            tools=all_tools,
        )

        if response.stop_reason == "tool_use":
            self.logger.info(f"🛠️ [{request_id}] Claude requested tool use")

            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_id = content_block.id

                    self.logger.info(f"🎯 [{request_id}] Executing tool: {tool_name}")

                    tool_result = await self.session_manager.execute_tool(
                        tool_name, tool_input, request_id
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(
                                        tool_result, indent=2, default=str
                                    ),
                                }
                            ],
                        }
                    )

            self.conversation_history.append(
                {"role": "assistant", "content": response.content}
            )
            self.conversation_history.append({"role": "user", "content": tool_results})

            final_response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,
                system=system_message,
                messages=self.conversation_history,
            )

            self.conversation_history.append(
                {"role": "assistant", "content": final_response.content}
            )

            return final_response.content[0].text
        else:
            self.conversation_history.append(
                {"role": "assistant", "content": response.content}
            )
            return response.content[0].text

    def get_metrics_summary(self):
        summary = self.metrics_collector.get_summary()
        summary["healthy_servers"] = self.session_manager.get_healthy_server_count()
        summary["total_servers"] = len(self.session_manager.server_sessions)
        return summary

    def clear_conversation(self):
        self.conversation_history = []
        self.logger.info("🗑️ Conversation history cleared")

    async def cleanup(self):
        await self.session_manager.cleanup()
