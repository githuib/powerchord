import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import IntEnum
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue

from gaffe import raises

ASYNC_LOG = logging.getLogger("powerchord.all")


def task_log(success: bool) -> logging.Logger:
    return logging.getLogger("powerchord." + ("success" if success else "fail"))


class LogLevel(IntEnum):
    NEVER = 100
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    @classmethod
    @raises(ValueError)
    def decode(cls, value: str) -> "LogLevel":
        if not value:
            return cls.NEVER
        try:
            return cls[value.upper()]
        except (AttributeError, KeyError) as exc:
            raise ValueError("Invalid log level:", value) from exc


@dataclass
class LogLevels:
    all: LogLevel = LogLevel.INFO
    success: LogLevel = LogLevel.NEVER
    fail: LogLevel = LogLevel.ERROR


def setup_logging_queues(levels: LogLevels) -> Iterator[QueueListener]:
    console = logging.StreamHandler(sys.stdout)
    logging.basicConfig(handlers=[console], level=levels.all, format="%(message)s")
    queue: Queue[logging.LogRecord] = Queue()
    for name, level in asdict(levels).items():
        logger = logging.getLogger("powerchord." + name)
        logger.setLevel(max(level, levels.all))
        logger.addHandler(QueueHandler(queue))
        logger.propagate = False
    yield QueueListener(queue, console)


@contextmanager
def logging_context(levels: LogLevels) -> Iterator[None]:
    queues_listeners = list(setup_logging_queues(levels))
    for listener in queues_listeners:
        listener.start()
    try:
        yield
    finally:
        for listener in queues_listeners:
            listener.stop()
