import json
import logging
import time
import traceback
import uuid
from datetime import datetime, timezone

from flask import g, request


class JsonFormatter(logging.Formatter):
    """Render each log record as one searchable JSON line."""

    EXTRA_FIELDS = (
        "event",
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
    )

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            # json.dumps escapes newlines, so even a traceback remains one line.
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_json_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    configured_level = app.config.get("LOG_LEVEL", "INFO")
    if isinstance(configured_level, str):
        configured_level = getattr(logging, configured_level.upper(), logging.INFO)
    # Keep INFO enabled so successful request records are present in production too.
    app.logger.setLevel(min(configured_level, logging.INFO))
    app.logger.propagate = False
    # The Werkzeug development server has its own plain-text access logger.
    # The structured http.request record above replaces that access line.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def register_request_logging(app):
    @app.before_request
    def start_request_log_context():
        g.request_started_at = time.perf_counter()
        # Generate our own correlation ID instead of trusting arbitrary header text.
        g.request_id = uuid.uuid4().hex

    @app.after_request
    def log_request(response):
        duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)
        response.headers["X-Request-ID"] = g.request_id
        status_code = response.status_code
        if status_code >= 500:
            log_method = app.logger.error
        elif status_code >= 400:
            log_method = app.logger.warning
        else:
            log_method = app.logger.info

        log_method(
            "HTTP request completed",
            extra={
                "event": "http.request",
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
