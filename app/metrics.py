from time import perf_counter

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "stock_bot_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "stock_bot_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
TELEGRAM_MESSAGES = Counter(
    "stock_bot_telegram_messages_total",
    "Processed Telegram messages",
    ["intent", "status"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "")
        start = perf_counter()
        status_holder = {"value": 500}

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_holder["value"] = message["status"]
            await send(message)

        await self.app(scope, receive, wrapped_send)
        duration = perf_counter() - start
        REQUEST_COUNT.labels(method=method, path=path, status=str(status_holder["value"])).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)

