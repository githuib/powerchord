import asyncio
import sys
import tomllib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from chili.decoder import decode

from .formatting import bright, dim, status
from .utils import concurrent_call, exec_command, timed_awaitable


class BoredomError(Exception):
    pass


@dataclass
class ConfigError(Exception):
    config_file: Path
    message: str


class Output(Enum):
    OUT = 'info'
    ERR = 'error'


@dataclass
class Verbosity:
    success: list[Output] = field(default_factory=list)
    fail: list[Output] = field(default_factory=lambda: [Output.OUT, Output.ERR])

    def should_output(self, out: Output, success: bool):
        return (out in self.success) if success else (out in self.fail)


@dataclass
class Config:
    tasks: dict[str, str] = field(default_factory=dict)
    verbosity: Verbosity = field(default_factory=lambda: Verbosity())

    def __post_init__(self):
        if not self.tasks:
            raise BoredomError


class TaskRunner:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.max_name_length = max(len(n) for n in config.tasks)

    @classmethod
    def with_pyproject_config(cls) -> 'TaskRunner':
        pyproject_file = Path('pyproject.toml')
        try:
            with pyproject_file.open('rb') as f:
                config_dict = tomllib.load(f).get('tool', {}).get('powerchord', {})
        except OSError as exc:
            raise ConfigError(pyproject_file, str(exc)) from exc
        try:
            config = decode(config_dict, Config)
        except ValueError as exc:
            raise ConfigError(pyproject_file, str(exc)) from exc
        return cls(config)

    async def run_task(self, name: str, task: str) -> tuple[str, bool]:
        (success, out, err), duration = await timed_awaitable(exec_command(task))
        sys.stdout.write(f'{status(success)} {name.ljust(self.max_name_length)}  {dim(duration)}\n')
        if self.config.verbosity.should_output(Output.OUT, success):
            sys.stdout.buffer.write(out)
            sys.stdout.buffer.flush()
        if self.config.verbosity.should_output(Output.ERR, success):
            sys.stderr.buffer.write(err)
            sys.stderr.buffer.flush()
        return name, success

    async def run_tasks(self) -> list[tuple[str, bool]]:
        tasks = self.config.tasks.items()
        sys.stdout.write(bright('To do:\n'))
        for name, task in tasks:
            sys.stdout.write(f'• {name.ljust(self.max_name_length)}  {dim(task)}\n')
        sys.stdout.write(bright('\nResults:\n'))
        return await concurrent_call(self.run_task, tasks)


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
