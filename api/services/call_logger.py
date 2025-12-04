import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Optional

from django.conf import settings

_executor = ThreadPoolExecutor(max_workers=2)


class CallLogger:
    _loggers: Dict[str, logging.Logger] = {}
    _log_queue: Dict[str, asyncio.Queue] = {}
    _log_tasks: Dict[str, asyncio.Task] = {}

    @classmethod
    def get_logger(cls, call_id: str) -> logging.Logger:
        if call_id in cls._loggers:
            return cls._loggers[call_id]

        logs_dir = settings.BASE_DIR / "logs" / "calls"
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"{call_id}_{timestamp}.log"

        logger = logging.getLogger(f"call_{call_id}")
        logger.setLevel(logging.DEBUG)
        logger.handlers = []
        logger.propagate = False

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        cls._loggers[call_id] = logger

        logger.info("=" * 60)
        logger.info(f"CALL STARTED: {call_id}")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 60)

        return logger

    @classmethod
    def _log_sync(cls, call_id: str, level: str, message: str) -> None:
        logger = cls.get_logger(call_id)
        if level == "info":
            logger.info(message)
        elif level == "error":
            logger.error(message)
        elif level == "debug":
            logger.debug(message)

    @classmethod
    def _log_async(cls, call_id: str, level: str, message: str) -> None:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(_executor, cls._log_sync, call_id, level, message)

    @classmethod
    def close_logger(cls, call_id: str) -> None:
        if call_id not in cls._loggers:
            return

        logger = cls._loggers[call_id]
        logger.info("=" * 60)
        logger.info(f"CALL ENDED: {call_id}")
        logger.info("=" * 60)

        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        del cls._loggers[call_id]

    @classmethod
    def log_user_speech(cls, call_id: str, transcript: str) -> None:
        cls._log_async(call_id, "info", f"[USER] {transcript}")

    @classmethod
    def log_assistant_speech(cls, call_id: str, transcript: str) -> None:
        cls._log_async(call_id, "info", f"[ASSISTANT] {transcript}")

    @classmethod
    def log_data_query(cls, call_id: str, query: str) -> None:
        cls._log_async(call_id, "info", f"[DATA_AGENT] Query: {query}")

    @classmethod
    def log_data_tool_call(cls, call_id: str, tool_name: str, args: Dict) -> None:
        cls._log_async(call_id, "info",
                       f"[DATA_AGENT] Tool: {tool_name} | Args: {args}")

    @classmethod
    def log_data_result(cls, call_id: str, result: str) -> None:
        cls._log_async(call_id, "info", f"[DATA_AGENT] Result: {result}")

    @classmethod
    def log_filler(cls, call_id: str, filler: str) -> None:
        cls._log_async(call_id, "info", f"[FILLER] {filler}")

    @classmethod
    def log_context_injection(cls, call_id: str, context: str) -> None:
        cls._log_async(call_id, "info",
                       f"[CONTEXT_INJECTED] {context[:200]}...")

    @classmethod
    def log_event(cls, call_id: str, event: str, details: Optional[str] = None) -> None:
        if details:
            cls._log_async(call_id, "info", f"[EVENT] {event}: {details}")
        else:
            cls._log_async(call_id, "info", f"[EVENT] {event}")

    @classmethod
    def log_error(cls, call_id: str, error: str) -> None:
        cls._log_async(call_id, "error", f"[ERROR] {error}")

    @classmethod
    def log_latency(cls, call_id: str, latency_ms: float) -> None:
        cls._log_async(call_id, "debug", f"[LATENCY] {latency_ms:.0f}ms")

    @classmethod
    def log_tokens(cls, call_id: str, agent: str, tokens: Dict) -> None:
        cls._log_async(call_id, "debug", f"[TOKENS] {agent}: {tokens}")
