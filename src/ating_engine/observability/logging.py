"""Structured logging foundation for simulation engine operations."""

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ating_engine.version import __version__

# Context variables for tracing operation context across logging calls
_current_operation_context: ContextVar[Dict[str, Any]] = ContextVar(
    "current_operation_context",
    default={},
)


class OperationLoggingContext:
    """Context manager to attach simulation operation metadata to structured log events."""

    def __init__(
        self,
        operation_id: Optional[str] = None,
        world_id: Optional[str] = None,
        state_version: Optional[int] = None,
        status: Optional[str] = None,
        engine_version: str = __version__,
        **extra: Any,
    ) -> None:
        self.context_data: Dict[str, Any] = {
            "operation_id": operation_id,
            "world_id": world_id,
            "state_version": state_version,
            "status": status,
            "engine_version": engine_version,
            **extra,
        }
        self._token: Optional[Any] = None

    def __enter__(self) -> "OperationLoggingContext":
        merged = {**_current_operation_context.get(), **self.context_data}
        self._token = _current_operation_context.set(merged)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._token is not None:
            _current_operation_context.reset(self._token)


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with simulation operation metadata."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = _current_operation_context.get()

        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "operation_id": getattr(record, "operation_id", ctx.get("operation_id")),
            "world_id": getattr(record, "world_id", ctx.get("world_id")),
            "state_version": getattr(record, "state_version", ctx.get("state_version")),
            "status": getattr(record, "status", ctx.get("status")),
            "engine_version": getattr(record, "engine_version", ctx.get("engine_version", __version__)),
        }

        # Attach error or exception info if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "error") and record.error:
            log_payload["error"] = record.error

        # Extra attributes passed via extra={}
        for k, v in record.__dict__.items():
            if k not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
                "operation_id", "world_id", "state_version", "status", "engine_version", "error",
            ):
                log_payload[k] = v

        return json.dumps(log_payload, default=str)


def configure_logging(level: str = "INFO", handler: Optional[logging.Handler] = None) -> None:
    """Configure root logger for ating_engine with StructuredJsonFormatter."""
    logger = logging.getLogger("ating_engine")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    if handler is None:
        handler = logging.StreamHandler()

    handler.setFormatter(StructuredJsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str = "ating_engine") -> logging.Logger:
    """Retrieve logger configured for engine subsystems."""
    return logging.getLogger(name)
