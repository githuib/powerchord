import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine, Iterable
from functools import wraps
from subprocess import PIPE
from typing import Any


class FatalError(SystemExit):
    def __init__(self, *args: object) -> None:
        super().__init__(" ".join(str(a) for a in ["💀", *args]))


def killed_by[E: Exception, **P, T](
    *errors: type[E],
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except errors as exc:
                raise FatalError(*exc.args) from exc

        return wrapper

    return decorator


def catch_unknown_errors[**P, T](
    unknown_message: str = "Unknown error",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                raise FatalError(unknown_message) from exc

        return wrapper

    return decorator


async def exec_command(command: str) -> tuple[bool, tuple[bytes, bytes]]:
    proc = await asyncio.create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)
    output_streams = await proc.communicate()
    return proc.returncode == 0, output_streams


async def concurrent_iter[T](
    coroutines: Iterable[Coroutine[Any, Any, T]],
) -> AsyncIterator[T]:
    tasks: list[asyncio.Task[T]] = [asyncio.create_task(coro) for coro in coroutines]
    for task in tasks:
        yield await task


async def concurrent_list[T](coroutines: Iterable[Coroutine[Any, Any, T]]) -> list[T]:
    return [item async for item in concurrent_iter(coroutines)]


async def concurrent_call[A, T](
    async_func: Callable[[A], Coroutine[Any, Any, T]], args_list: list[A]
) -> list[T]:
    return await concurrent_list(async_func(args) for args in args_list)
