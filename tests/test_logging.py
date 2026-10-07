"""Tests for structured logging and operation observability."""

import io
import json
import logging
from ating_engine.observability.logging import (
    OperationLoggingContext,
    StructuredJsonFormatter,
    configure_logging,
    get_logger,
)


def test_structured_json_logging_with_operation_context():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    configure_logging(level="DEBUG", handler=handler)

    logger = get_logger("ating_engine.test")

    with OperationLoggingContext(
        operation_id="op-audit-99",
        world_id="world-prime",
        state_version=42,
        status="RUNNING",
    ):
        logger.info("Evaluating state transition")

    output = stream.getvalue().strip()
    assert output, "Log output should not be empty"

    log_entry = json.loads(output)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Evaluating state transition"
    assert log_entry["operation_id"] == "op-audit-99"
    assert log_entry["world_id"] == "world-prime"
    assert log_entry["state_version"] == 42
    assert log_entry["status"] == "RUNNING"
    assert "timestamp" in log_entry
