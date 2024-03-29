import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine, Iterable
from functools import wraps
from subprocess import PIPE
from time import perf_counter_ns
from typing import Any, ParamSpec, TypeVar

T = TypeVar('T')
E = TypeVar('E', bound=Exception)
P = ParamSpec('P')


class FatalError(SystemExit):
    def __init__(self, *args):
        super().__init__(' '.join(str(a) for a in ['💀', *args]))


def killed_by(*errors: type[E]) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except errors as exc:
                raise FatalError(*exc.args) from exc
        return wrapper
    return decorator


def catch_unknown_errors(
    unknown_message: str = 'Unknown error',
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                raise FatalError(unknown_message) from exc
        return wrapper
    return decorator


async def exec_command(command: str) -> tuple[bool, tuple[bytes, bytes]]:
    proc = await asyncio.create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)
    output_streams = await proc.communicate()
    return proc.returncode == 0, output_streams


async def concurrent_iter(
    coros: Iterable[Coroutine[Any, Any, T]],
) -> AsyncIterator[T]:
    tasks: list[asyncio.Task[T]] = [asyncio.create_task(coro) for coro in coros]
    for task in tasks:
        yield await task


async def concurrent_list(
    coros: Iterable[Coroutine[Any, Any, T]],
) -> list[T]:
    return [item async for item in concurrent_iter(coros)]


async def concurrent_call(
    async_func: Callable[P, Coroutine[Any, Any, T]],
    args_list: Iterable[P.args],
) -> list[T]:
    return await concurrent_list(
        async_func(*args) if isinstance(args, Iterable) else async_func(args)
        for args in args_list
    )


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
