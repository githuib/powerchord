import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import IntEnum
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from typing import TypeVar

T = TypeVar('T')

ASYNC_LOG = logging.getLogger('powerchord.all')


def task_log(success: bool) -> logging.Logger:
    return logging.getLogger('powerchord.' + ('success' if success else 'fail'))


class LogLevel(IntEnum):
    NEVER = 100
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    @classmethod
    def decode(cls, value: str) -> 'LogLevel':
        if not value:
            return LogLevel.NEVER
        try:
            return LogLevel[value.upper()]
        except KeyError as exc:
            raise ValueError('Invalid log level:', value) from exc


@dataclass
class LogLevels:
    all: LogLevel = LogLevel.INFO
    success: LogLevel = LogLevel.NEVER
    fail: LogLevel = LogLevel.INFO


def queue_listener(levels: LogLevels) -> QueueListener | None:
    if levels.all == LogLevel.NEVER:
        return None
    console = logging.StreamHandler(sys.stdout)
    logging.basicConfig(handlers=[console], level=levels.all, format='%(message)s')
    queue: Queue[logging.LogRecord] = Queue()
    for name, level in asdict(levels).items():
        logger = logging.getLogger('powerchord.' + name)
        logger.setLevel(max(level, levels.all))
        logger.addHandler(QueueHandler(queue))
        logger.propagate = False
    return QueueListener(queue, console)


@contextmanager
def logging_context(levels: LogLevels) -> Iterator[None]:
    listener = queue_listener(levels)
    if listener:
        listener.start()
    try:
        yield
    finally:
        if listener:
            listener.stop()
