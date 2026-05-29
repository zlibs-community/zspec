"""Tests for LoggingTranslator."""

import logging
from typing import Any, override

import pytest

from zspec import Specification
from zspec.log import LoggingTranslator, logger
from zspec.translator import Translator


class Always(Specification[object]):
    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return True


class Never(Specification[object]):
    @override
    def is_satisfied_by(self, candidate: object) -> bool:
        return False


class StringTranslator(Translator[str]):
    """Minimal translator that produces human-readable strings."""

    @override
    def _translate(self, spec: Specification[Any]) -> str:
        return str(spec)

    @override
    def _and(self, left: str, right: str) -> str:
        return f"({left} AND {right})"

    @override
    def _or(self, left: str, right: str) -> str:
        return f"({left} OR {right})"

    @override
    def _not(self, operand: str) -> str:
        return f"NOT ({operand})"


class TestLoggingTranslator:
    def test_delegates_translate(self) -> None:
        inner = StringTranslator()
        wrapped = LoggingTranslator(inner)
        spec = Always() & Never()
        assert wrapped.translate(spec) == inner.translate(spec)

    def test_inner_property(self) -> None:
        inner = StringTranslator()
        wrapped = LoggingTranslator(inner)
        assert wrapped.inner is inner

    def test_logs_spec_and_result(self, caplog: pytest.LogCaptureFixture) -> None:
        inner = StringTranslator()
        wrapped = LoggingTranslator(inner)
        spec = Always() & ~Never()
        with caplog.at_level(logging.DEBUG, logger="zspec.log"):
            wrapped.translate(spec)
        messages = [r.message for r in caplog.records]
        assert len(messages) >= 2
        assert "(Always AND NOT (Never))" in messages

    def test_logs_to_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        inner = StringTranslator()
        wrapped = LoggingTranslator(inner)
        with caplog.at_level(logging.DEBUG, logger="zspec.log"):
            wrapped.translate(Always())
        assert len(caplog.records) == 2
        assert all(r.levelno == logging.DEBUG for r in caplog.records)

    def test_logs_recursive_structure(self, caplog: pytest.LogCaptureFixture) -> None:
        inner = StringTranslator()
        wrapped = LoggingTranslator(inner)
        with caplog.at_level(logging.DEBUG, logger="zspec.log"):
            wrapped.translate(Always() & Never())
        messages = [r.message for r in caplog.records]
        assert any("  ->" in m for m in messages)

    def test_no_logging_when_disabled(self, caplog: pytest.LogCaptureFixture) -> None:
        inner = StringTranslator()
        wrapped = LoggingTranslator(inner)
        caplog.set_level(logging.DEBUG, logger="zspec.log")
        logger.setLevel(logging.WARNING)
        try:
            wrapped.translate(Always())
            assert len(caplog.records) == 0
        finally:
            logger.setLevel(logging.NOTSET)
