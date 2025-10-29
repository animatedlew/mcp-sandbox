from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RequestMetrics:
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_type: Optional[str] = None
    tools_called: List[str] = field(default_factory=list)
    token_usage: Optional[Dict[str, int]] = None


class MetricsCollector:
    def __init__(self):
        self.metrics: List[RequestMetrics] = []

    def add_metric(self, metric: RequestMetrics):
        self.metrics.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        if not self.metrics:
            return {"message": "No metrics available"}

        total = len(self.metrics)
        successful = sum(1 for m in self.metrics if m.success)
        failed = total - successful

        avg_duration = (
            sum(m.end_time - m.start_time for m in self.metrics if m.end_time) / total
            if total > 0
            else 0
        )

        return {
            "total_requests": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total)*100:.1f}%" if total > 0 else "0%",
            "avg_duration_seconds": f"{avg_duration:.2f}",
        }

    def clear(self):
        self.metrics.clear()
