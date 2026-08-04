import json
import logging
import os
from datetime import datetime, timezone

_configured = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "user_id",
            "ip_address",
            "method",
            "path",
            "status_code",
            "duration_ms",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_observability() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    if os.getenv("LOG_FORMAT", "text").lower() == "json":
        formatter = JsonFormatter()
        loggers = [logging.getLogger(), logging.getLogger("django"), logging.getLogger("apps")]
        seen = set()
        for logger in loggers:
            for handler in logger.handlers:
                if id(handler) not in seen:
                    handler.setFormatter(formatter)
                    seen.add(id(handler))

    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        release=os.getenv("SENTRY_RELEASE") or None,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        send_default_pii=False,
    )
