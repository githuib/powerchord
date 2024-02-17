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
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET

    @classmethod
    def decode(cls, value: str) -> 'LogLevel':
        return LogLevel(logging.getLevelName(value.upper())) if value else LogLevel.NOTSET


@dataclass
class LogLevels:
    all: LogLevel | None = LogLevel.INFO
    success: LogLevel | None = None
    fail: LogLevel | None = LogLevel.INFO


def queue_listeners(levels: LogLevels) -> Iterator[QueueListener]:
    if not levels.all:
        return
    console = logging.StreamHandler(sys.stdout)
    logging.basicConfig(handlers=[console], level=levels.all, format='%(message)s')
    for name, level in asdict(levels).items():
        logger = logging.getLogger('powerchord.' + name)
        logger.propagate = False
        if level:
            queue: Queue[logging.LogRecord] = Queue()
            queue_handler = QueueHandler(queue)
            queue_handler.setLevel(level)
            logger.addHandler(queue_handler)
            listener = QueueListener(queue, console)
            yield listener


@contextmanager
def logging_context(levels: LogLevels) -> Iterator[None]:
    listeners = list(queue_listeners(levels))
    for listener in listeners:
        listener.start()
    try:
        yield
    finally:
        for listener in listeners:
            listener.stop()
