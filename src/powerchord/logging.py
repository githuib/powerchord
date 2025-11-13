import logging
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import IntEnum
from functools import partial
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from typing import TYPE_CHECKING, Literal

from gaffe import raises

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

ASYNC_LOG = logging.getLogger("powerchord.all")

Category = Literal["success", "fail"]


def task_log(category: Category, log_level: int) -> Callable[[str], None]:
    return partial(logging.getLogger(f"powerchord.{category}").log, log_level)


class InvalidLogLevelError(ValueError):
    def __init__(self, log_level: str) -> None:
        super().__init__(f"Invalid log level: {log_level}")


class LogLevel(IntEnum):
    NEVER = 100
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    @classmethod
    @raises(ValueError)
    def decode(cls, value: str) -> LogLevel:
        if not value:
            return cls.NEVER
        try:
            return cls[value.upper()]
        except (AttributeError, KeyError) as exc:
            raise InvalidLogLevelError(value) from exc


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
