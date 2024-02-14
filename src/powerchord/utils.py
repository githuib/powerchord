import asyncio
from collections.abc import Awaitable, Callable
from subprocess import PIPE
from time import perf_counter_ns
from typing import TypeVar

T = TypeVar('T')


async def exec_command(command: str) -> tuple[bool, bytes, bytes]:
    proc = await asyncio.create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)
    out, err = await proc.communicate()
    return proc.returncode == 0, out, err


def human_readable_duration(nanoseconds: int) -> str:
    minutes = int(nanoseconds // 60_000_000_000)
    nanoseconds %= 60_000_000_000
    seconds = int(nanoseconds // 1_000_000_000)
    nanoseconds %= 1_000_000_000
    milliseconds = int(nanoseconds // 1_000_000)
    nanoseconds %= 1_000_000
    microseconds = int(nanoseconds // 1_000)
    nanoseconds %= 1_000
    if minutes:
        return f'{minutes:d}:{seconds:02d}.{milliseconds:03d} minutes'
    if seconds:
        return f'{seconds:d}.{milliseconds:03d} seconds'
    if milliseconds:
        return f'{milliseconds:d}.{microseconds:03d} ms'
    return f'{microseconds:d}.{nanoseconds:03d} µs'


def timed(
    func: Callable[[], T],
    formatter: Callable[[int], str] = None,
) -> tuple[T, str]:
    start = perf_counter_ns()
    return func(), (formatter or human_readable_duration)(perf_counter_ns() - start)


def timed_awaitable(
    awaitable: Awaitable[T],
    formatter: Callable[[int], str] = None,
) -> Awaitable[tuple[T, str]]:
    async def wrapper() -> tuple[T, str]:
        start = perf_counter_ns()
        return await awaitable, (formatter or human_readable_duration)(perf_counter_ns() - start)
    return wrapper()
