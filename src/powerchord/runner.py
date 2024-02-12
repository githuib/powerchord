import asyncio
import sys
import tomllib
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from subprocess import PIPE

from .formatting import bright, dim, status


class BoredomError(Exception):
    pass


class ConfigError(Exception, ABC):
    def __init__(self, config_file: Path):
        self.config_file = config_file

    @property
    @abstractmethod
    def message(self):
        pass


class PyprojectConfigError(ConfigError):
    def __init__(self, config_file: Path):
        super().__init__(config_file)

    @property
    def message(self):
        return (
            f'💀 Could not find [tool.powerchord(.*)] config in {self.config_file}.\n'
            'Currently no other configuration methods are supported.'
        )


class FailedTasksError(Exception):
    def __init__(self, failed_tasks: list[str]):
        self.failed_tasks = failed_tasks


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

    @classmethod
    def with_pyproject_config(cls) -> 'TaskRunner':
        pyproject_file = Path('pyproject.toml')
        try:
            with pyproject_file.open('rb') as f:
                config = tomllib.load(f).get('tool', {}).get('powerchord', {})
        except OSError:
            config = {}
        if not config:
            raise PyprojectConfigError(pyproject_file)
        return cls(config.get('tasks', {}), Verbosity(**config.get('verbosity', {})))

    def run_tasks(self) -> None:
        results = asyncio.run(self.exec_tasks())
        failed_tasks = [name for name, success in results.items() if not success]
        if failed_tasks:
            raise FailedTasksError(failed_tasks)

    async def exec_tasks(self) -> dict[str, bool]:
        sys.stdout.write(bright('To do:\n'))
        for name, task in self.tasks.items():
            sys.stdout.write(f'• {name}: {dim(task)}\n')
        sys.stdout.write(bright('\nResults:\n'))
        async with asyncio.TaskGroup() as tg:
            futures = [
                tg.create_task(self.exec_task(name, task))
                for name, task in self.tasks.items()
            ]
        return dict(future.result() for future in futures)

    async def exec_task(self, name: str, task: str) -> tuple[str, bool]:
        proc = await asyncio.create_subprocess_shell(task, stdout=PIPE, stderr=PIPE)
        out, err = await proc.communicate()
        success = proc.returncode == 0
        sys.stdout.write(f'{status(success)} {name}\n')
        if self.verbosity.should_output(Output.OUT, success):
            sys.stdout.buffer.write(out)
            sys.stdout.buffer.flush()
        if self.verbosity.should_output(Output.ERR, success):
            sys.stderr.buffer.write(err)
            sys.stderr.buffer.flush()
        return name, success


def run_tasks() -> None:
    try:
        TaskRunner.with_pyproject_config().run_tasks()
    except ConfigError as exc:
        sys.exit(exc.message)
    except BoredomError:
        sys.stdout.write('Nothing to do. Getting bored...\n')
    except FailedTasksError as exc:
        sys.exit(f'\n💀 {bright("Failed tasks:")} {", ".join(exc.failed_tasks)}')
