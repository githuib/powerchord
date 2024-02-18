import argparse
import asyncio
import logging
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chili import TypeDecoder, decode

from .logging import LogLevel, LogLevels, logging_context
from .runner import TaskRunner

log = logging.getLogger(__name__)


class LogLevelDecoder(TypeDecoder):
    def decode(self, value: str) -> LogLevel:
        return LogLevel.decode(value)


@dataclass
class Config:
    tasks: dict[str, str] = field(default_factory=dict)
    log_levels: LogLevels = field(default_factory=lambda: LogLevels())


class ParseDict(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str = None,
    ) -> None:
        value_seq = [values] if isinstance(values, str) else [str(v) for v in values or []]
        d = getattr(namespace, self.dest) or {}
        try:
            pairs = (item.split('=', 1) for item in value_seq)
            d |= {key.strip(): value for key, value in pairs}
        except ValueError:
            parser.error(
                f'argument {option_string}: not matching key1="some val" [key2="another val" ...]',
            )
        else:
            setattr(namespace, self.dest, d)


def config_from_args() -> Config | None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '-t',
        '--tasks',
        dest='tasks',
        nargs='+',
        metavar='NAME=COMMAND',
        action=ParseDict,
        default={},
    )
    args = arg_parser.parse_args()
    return Config(args.tasks) if args.tasks else None


class FatalError(SystemExit):
    def __init__(self, *args):
        log.critical(f'💀 {" ".join(str(arg) for arg in args)}')
        super().__init__(1)


class ConfigError(FatalError):
    def __init__(self, config_source: str = None, cause: str = None):
        message = 'Could not load config'
        if config_source:
            message += f' from {config_source}'
            if cause:
                message += f': {cause}'
        super().__init__(message)


def config_from_pyproject() -> Config | None:
    pyproject_file = 'pyproject.toml'
    try:
        with Path(pyproject_file).open('rb') as f:
            config_dict = tomllib.load(f).get('tool', {}).get('powerchord', {})
    except OSError:
        return None
    try:
        return decode(config_dict, Config, decoders={LogLevel: LogLevelDecoder()})
    except ValueError as exc:
        raise ConfigError(pyproject_file, ' '.join(exc.args)) from exc


def load_config() -> Config:
    for loader in [config_from_args, config_from_pyproject]:
        config = loader()
        if config:
            return config
    raise ConfigError


def main() -> None:
    config = load_config()
    task_runner = TaskRunner(config.tasks)
    with logging_context(config.log_levels):
        sys.exit(not asyncio.run(task_runner.run_tasks()))
