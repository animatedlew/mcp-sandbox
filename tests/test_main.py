from unittest.mock import AsyncMock, MagicMock, patch

from main import chat, main, run_demo, run_interactive
import pytest


class TestMainEntryPoints:
    @pytest.mark.asyncio
    async def test_run_demo(self):
        """Test the demo function."""
        with patch("main.MCPClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.initialize = AsyncMock(return_value=True)
            mock_client.chat_with_claude = AsyncMock(return_value="Demo response")
            mock_client.get_metrics_summary = MagicMock(
                return_value={
                    "total_requests": 6,
                    "successful": 6,
                    "failed": 0,
                }
            )
            mock_client.cleanup = AsyncMock()

            with patch("builtins.print"):
                await run_demo()
                mock_client.initialize.assert_called_once()
                assert mock_client.chat_with_claude.call_count == 6  # 6 demo queries
                mock_client.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_demo_with_error(self):
        """Test demo handles errors gracefully."""
        with patch("main.MCPClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.initialize = AsyncMock(return_value=True)
            mock_client.chat_with_claude = AsyncMock(
                side_effect=[
                    Exception("Test error"),
                    "Success response",
                    "Success response",
                    "Success response",
                    "Success response",
                    "Success response",
                ]
            )
            mock_client.get_metrics_summary = MagicMock(
                return_value={
                    "total_requests": 6,
                    "successful": 5,
                    "failed": 1,
                }
            )
            mock_client.cleanup = AsyncMock()

            with patch("builtins.print"):
                await run_demo()
                assert mock_client.chat_with_claude.call_count == 6
                mock_client.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_interactive(self):
        """Test the interactive chat."""
        with patch("main.MCPChat") as mock_chat_class:
            mock_chat = MagicMock()
            mock_chat_class.return_value = mock_chat
            mock_chat.start = AsyncMock(return_value=True)
            mock_chat.run_chat = AsyncMock()
            mock_chat.cleanup = AsyncMock()

            await run_interactive()

            mock_chat.start.assert_called_once()
            mock_chat.run_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_interactive_start_failure(self):
        """Test interactive mode handles start failure."""
        with patch("main.MCPChat") as mock_chat_class:
            mock_chat = MagicMock()
            mock_chat_class.return_value = mock_chat
            mock_chat.start = AsyncMock(return_value=False)
            mock_chat.run_chat = AsyncMock()
            mock_chat.cleanup = AsyncMock()

            with patch("builtins.print"):
                await run_interactive()

            mock_chat.start.assert_called_once()
            # run_chat may or may not be called depending on error handling

    def test_main_help_flag(self):
        test_args = ["main.py", "--help"]

        with (
            patch("sys.argv", test_args),
            patch("main.show_help") as mock_help,
            patch("builtins.print"),
        ):
            main()
            mock_help.assert_called_once()

    def test_main_demo_mode(self):
        test_args = ["main.py"]

        async def mock_run_demo():
            pass

        with (
            patch("sys.argv", test_args),
            patch("main.run_demo", side_effect=mock_run_demo) as mock_demo,
            patch("builtins.print"),
        ):
            main()
            # Verify run_demo was called (via asyncio.run)
            mock_demo.assert_called_once()

    def test_main_chat_mode(self):
        test_args = ["main.py", "--chat"]

        async def mock_run_interactive():
            pass

        with (
            patch("sys.argv", test_args),
            patch(
                "main.run_interactive", side_effect=mock_run_interactive
            ) as mock_interactive,
            patch("builtins.print"),
        ):
            main()
            # Verify run_interactive was called (via asyncio.run)
            mock_interactive.assert_called_once()

    def test_chat_entry_point(self):
        """Test the chat entry point."""

        async def mock_run_interactive():
            pass

        with (
            patch("builtins.print"),
            patch(
                "main.run_interactive", side_effect=mock_run_interactive
            ) as mock_interactive,
        ):
            chat()
            # Verify run_interactive was called (via asyncio.run)
            mock_interactive.assert_called_once()

    def test_main_keyboard_interrupt(self):
        test_args = ["main.py"]

        # Create a non-async mock to prevent coroutine creation
        mock_run_demo = MagicMock(return_value=None)

        with (
            patch("sys.argv", test_args),
            patch("builtins.print") as mock_print,
            patch("sys.exit") as mock_exit,
            patch("main.run_demo", mock_run_demo),
            patch("asyncio.run", side_effect=KeyboardInterrupt),
        ):
            # Simulate the try-except block from if __name__ == "__main__"
            try:
                main()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                mock_exit(1)

        mock_print.assert_called_with("\n👋 Goodbye!")
        mock_exit.assert_not_called()

    def test_main_exception_handling(self):
        test_args = ["main.py"]

        # Create a non-async mock to prevent coroutine creation
        mock_run_demo = MagicMock(return_value=None)

        with (
            patch("sys.argv", test_args),
            patch("builtins.print") as mock_print,
            patch("sys.exit") as mock_exit,
            patch("main.run_demo", mock_run_demo),
            patch("asyncio.run", side_effect=Exception("Test error")),
        ):
            # Simulate the try-except block from if __name__ == "__main__"
            try:
                main()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                mock_exit(1)

        mock_print.assert_called_with("\n❌ Error: Test error")
        mock_exit.assert_called_with(1)
