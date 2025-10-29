from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_sandbox.client import metrics, session


class TestMetrics:
    def test_request_metrics_creation(self):
        metric = metrics.RequestMetrics(request_id="test-123", start_time=100.0)

        assert metric.request_id == "test-123"
        assert metric.start_time == 100.0
        assert metric.end_time is None
        assert metric.success is False
        assert metric.error_type is None

    def test_metrics_collector_empty(self):
        collector = metrics.MetricsCollector()

        summary = collector.get_summary()

        assert summary == {"message": "No metrics available"}

    def test_metrics_collector_add_metric(self):
        collector = metrics.MetricsCollector()

        metric = metrics.RequestMetrics(
            request_id="test-123", start_time=100.0, end_time=105.0, success=True
        )

        collector.add_metric(metric)

        assert len(collector.metrics) == 1

    def test_metrics_collector_summary(self):
        collector = metrics.MetricsCollector()

        collector.add_metric(
            metrics.RequestMetrics(
                request_id="req-1", start_time=100.0, end_time=105.0, success=True
            )
        )
        collector.add_metric(
            metrics.RequestMetrics(
                request_id="req-2", start_time=200.0, end_time=203.0, success=True
            )
        )

        # Add a failed metric
        collector.add_metric(
            metrics.RequestMetrics(
                request_id="req-3",
                start_time=300.0,
                end_time=302.0,
                success=False,
                error_type="timeout",
            )
        )

        summary = collector.get_summary()

        assert summary["total_requests"] == 3
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == "66.7%"
        assert "avg_duration_seconds" in summary

    def test_metrics_collector_clear(self):
        collector = metrics.MetricsCollector()

        collector.add_metric(
            metrics.RequestMetrics(
                request_id="test", start_time=100.0, end_time=105.0, success=True
            )
        )

        assert len(collector.metrics) == 1

        collector.clear()

        assert len(collector.metrics) == 0


class TestSession:
    def test_mcp_server_config_creation(self):
        config = session.MCPServerConfig(
            name="test-server", script_path="/path/to/server.py"
        )

        assert config.name == "test-server"
        assert config.script_path == "/path/to/server.py"
        assert config.enabled is True
        assert config.timeout == 30

    def test_mcp_session_manager_init(self):
        manager = session.MCPSessionManager()

        assert manager.server_configs == []
        assert manager.server_sessions == {}

    @pytest.mark.asyncio
    async def test_load_configuration_creates_default(self):
        manager = session.MCPSessionManager()

        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            await manager.load_configuration("test_config.json")

        assert len(manager.server_configs) > 0

    @pytest.mark.asyncio
    async def test_initialize_servers_disabled(self):
        manager = session.MCPSessionManager()

        config = session.MCPServerConfig(
            name="disabled-server", script_path="test.py", enabled=False
        )
        manager.server_configs = [config]

        await manager.initialize_servers()

        assert len(manager.server_sessions) == 0

    def test_get_all_tools_empty(self):
        manager = session.MCPSessionManager()

        tools = manager.get_all_tools()

        assert tools == []

    def test_get_all_tools_unhealthy_servers(self):
        manager = session.MCPSessionManager()

        manager.server_sessions["test-server"] = {
            "healthy": False,
            "tools": [{"name": "test_tool"}],
        }

        tools = manager.get_all_tools()

        assert tools == []

    def test_get_all_tools_healthy_servers(self):
        manager = session.MCPSessionManager()

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object"}

        manager.server_sessions["test-server"] = {
            "healthy": True,
            "tools": [mock_tool],
        }

        tools = manager.get_all_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["description"] == "A test tool"

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        manager = session.MCPSessionManager()

        result = await manager.execute_tool("nonexistent_tool", {}, "req-123")

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        manager = session.MCPSessionManager()

        # Mock a healthy server with tools
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"success": true, "result": "test"}'
        mock_result.content = [mock_content]
        mock_session.call_tool.return_value = mock_result

        manager.server_sessions["test-server"] = {
            "healthy": True,
            "tools": [mock_tool],
            "session": mock_session,
        }

        result = await manager.execute_tool("test_tool", {"arg": "value"}, "req-123")

        assert result["success"] is True
        assert result["result"] == "test"

    def test_get_healthy_server_count(self):
        manager = session.MCPSessionManager()

        manager.server_sessions["server1"] = {"healthy": True}
        manager.server_sessions["server2"] = {"healthy": False}
        manager.server_sessions["server3"] = {"healthy": True}

        count = manager.get_healthy_server_count()

        assert count == 2

    @pytest.mark.asyncio
    async def test_cleanup(self):
        manager = session.MCPSessionManager()

        mock_session = AsyncMock()
        mock_stdio = AsyncMock()

        manager.server_sessions["test-server"] = {
            "session": mock_session,
            "stdio": mock_stdio,
        }

        await manager.cleanup()

        mock_session.__aexit__.assert_called_once()
        mock_stdio.__aexit__.assert_called_once()
