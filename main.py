import argparse
import asyncio
import sys

from src.mcp_sandbox import MCPChat, MCPClient


async def run_demo():
    print("🚀 Claude + MCP Server Demo")
    print("=" * 50)

    mcp_client = MCPClient()
    await mcp_client.initialize()

    demo_queries = [
        "What tables are in my database?",
        "Show me all users in the database",
        "What's the average age of users?",
        "Search for users with email containing 'test'",
        "Add a new user named Demo User with email demo4@example.com and age 28",
        "Show me users created today",
    ]

    try:
        for i, query in enumerate(demo_queries, 1):
            print(f"\n🎯 Demo Query {i}: {query}")
            print("-" * 40)

            try:
                response = await mcp_client.chat_with_claude(query)
                print(f"🤖 Claude: {response}")

            except Exception as e:
                print(f"❌ Error: {e}")

            print()

        print("✨ Demo complete! Claude successfully used MCP tools.")
        print("💡 MCP client with monitoring and error handling.")

        metrics = mcp_client.get_metrics_summary()
        print(f"� Metrics: {metrics}")
        print("\n🎯 Try interactive mode: python main.py --chat")

    finally:
        await mcp_client.cleanup()


async def run_interactive():
    chat = MCPChat()

    try:
        if await chat.start():
            await chat.run_chat()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if hasattr(chat, "cleanup"):
            await chat.cleanup()
        print("👋 Thanks for using MCP Chat!")


def show_help():
    print("🚀 mcpsandbox - MCP Server Integration")
    print("=" * 60)
    print("Claude API + MCP server with monitoring")
    print()
    print("Usage: python main.py [--chat] [--help]")
    print()
    print("Commands:")
    print("  python main.py        # Run demo")
    print("  python main.py --chat # Interactive chat")
    print("  make demo             # Run demo")
    print("  make chat             # Interactive chat")


def main():
    parser = argparse.ArgumentParser(
        description="MCP Server Integration",
        add_help=False,
    )

    parser.add_argument(
        "--chat", "-c", action="store_true", help="Start interactive chat mode"
    )

    parser.add_argument(
        "--help", "-h", action="store_true", help="Show help information"
    )

    args = parser.parse_args()

    if args.help:
        show_help()
        return

    if args.chat:
        print("🎯 Starting chat mode...")
        asyncio.run(run_interactive())
    else:
        print("🎯 Running demo...")
        asyncio.run(run_demo())


def chat():
    print("🎯 Starting chat mode...")
    asyncio.run(run_interactive())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
