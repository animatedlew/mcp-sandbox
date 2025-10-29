import asyncio
import logging
from typing import Optional

from .app import MCPClient


logger = logging.getLogger(__name__)


class MCPChat:
    def __init__(self, config_path: Optional[str] = None):
        self.client = MCPClient(config_path)
        self.running = True
        self.logger = logger

    async def start(self) -> bool:
        print("🚀 MCP Chat System")
        print("=" * 50)

        if await self.client.initialize():
            print("✅ System initialized successfully")
            print(f"✅ MCP servers: {len(self.client.session_manager.server_sessions)}")
            print("✅ Error handling and retry logic active")
            print("✅ Metrics collection enabled")
            print()
            return True
        else:
            print("❌ Failed to initialize system")
            return False

    async def run_chat(self):
        print("💬 MCP Chat Ready!")
        print("Type '/help' for commands or '/quit' to exit.")
        print()

        while self.running:
            try:
                user_input = input("🧑‍💻 You: ").strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                    continue

                response = await self.client.chat_with_claude(user_input)
                print(f"\n🤖 Claude: {response}\n")

            except KeyboardInterrupt:
                print("\n🛑 Use '/quit' to exit gracefully")
                continue
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"Error in chat: {e}")
                print(f"\n❌ Error: {e}\n")

    async def handle_command(self, command: str):
        cmd = command.lower().strip()

        if cmd in {"/quit", "/exit"}:
            self.running = False
            await self.client.cleanup()
            print("👋 Goodbye!")
        elif cmd == "/clear":
            self.client.clear_conversation()
            print("🗑️ Conversation cleared\n")
        elif cmd == "/metrics":
            metrics = self.client.get_metrics_summary()
            print("\n📊 System Metrics:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
            print()
        elif cmd == "/help":
            print("\n🔧 Available Commands:")
            print("  /clear    - Clear conversation")
            print("  /metrics  - Show system metrics")
            print("  /help     - Show this help")
            print("  /quit     - Exit chat")
            print()
        else:
            print(f"❓ Unknown command: {command}\n")


async def main():
    chat = MCPChat()

    try:
        if await chat.start():
            await chat.run_chat()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
    finally:
        print("👋 Thanks for using MCP Chat!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
