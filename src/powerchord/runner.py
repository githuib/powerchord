import asyncio
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .formatting import bright, dim, status
from .utils import exec_command, timed_awaitable


class BoredomError(Exception):
    pass


@dataclass
class ConfigError(Exception):
    config_file: Path
    message: str


class Output(StrEnum):
    OUT = 'info'
    ERR = 'error'


class Verbosity:
    def __init__(self, success: Sequence[Output] = None, fail: Sequence[Output] = None):
        self.success = success or []
        self.fail = fail or [Output.OUT, Output.ERR]

    def should_output(self, out: Output, success: bool):
        return (out in self.success) if success else (out in self.fail)


class TaskRunner:
    def __init__(self, tasks: dict[str, str], verbosity: Verbosity):
        if not tasks:
            raise BoredomError
        self.tasks = tasks
        self.verbosity = verbosity
        self.max_name_length = max(len(n) for n in tasks)

    @classmethod
    def with_pyproject_config(cls) -> 'TaskRunner':
        pyproject_file = Path('pyproject.toml')
        try:
            with pyproject_file.open('rb') as f:
                config = tomllib.load(f).get('tool', {}).get('powerchord', {})
        except OSError as exc:
            raise ConfigError(pyproject_file, str(exc)) from exc
        if not config:
            raise ConfigError(pyproject_file, 'Could not find any [tool.powerchord(.*)] entries')
        return cls(config.get('tasks', {}), Verbosity(**config.get('verbosity', {})))

    async def run_task(self, name: str, task: str) -> tuple[str, bool]:
        (success, out, err), duration = await timed_awaitable(exec_command(task))
        sys.stdout.write(f'{status(success)} {name.ljust(self.max_name_length)}  {dim(duration)}\n')
        if self.verbosity.should_output(Output.OUT, success):
            sys.stdout.buffer.write(out)
            sys.stdout.buffer.flush()
        if self.verbosity.should_output(Output.ERR, success):
            sys.stderr.buffer.write(err)
            sys.stderr.buffer.flush()
        return name, success

    async def run_tasks(self) -> list[tuple[str, bool]]:
        sys.stdout.write(bright('To do:\n'))
        for name, task in self.tasks.items():
            sys.stdout.write(f'• {name.ljust(self.max_name_length)}  {dim(task)}\n')
        sys.stdout.write(bright('\nResults:\n'))
        futures = [
            asyncio.create_task(self.run_task(name, task))
            for name, task in self.tasks.items()
        ]
        return [await f for f in futures]


def fail_with(*lines: str) -> None:
    sys.exit('💀 ' + '\n'.join(lines))


def run_tasks() -> None:
    try:
        task_runner = TaskRunner.with_pyproject_config()
    except ConfigError as exc:
        fail_with(f'Error while loading {exc.config_file}:\n{exc.message}')
    except BoredomError:
        sys.stdout.write('Nothing to do. Getting bored...\n')
    else:
        failed_tasks = [task for task, ok in asyncio.run(task_runner.run_tasks()) if not ok]
        if failed_tasks:
            sys.stderr.write('\n')
            fail_with(bright('Failed tasks:'), ', '.join(failed_tasks))
