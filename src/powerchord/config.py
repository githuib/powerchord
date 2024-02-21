import argparse
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from chili import decode

from .logging import LogLevel, LogLevels
from .runner import Task


@dataclass
class Config:
    tasks: list[Task] = field(default_factory=list)
    log_levels: LogLevels = field(default_factory=LogLevels)

    @classmethod
    def decode(cls, value: dict) -> 'Config':
        tasks = value.get('tasks', {})
        if isinstance(tasks, list):
            task_items = [('', t) if isinstance(t, str) else t for t in tasks]
        elif isinstance(tasks, dict):
            task_items = list(tasks.items())
        else:
            raise TypeError
        value['tasks'] = [{'command': t, 'name': n} for n, t in task_items]

        log_levels = value.get('log_levels', {})
        if isinstance(log_levels, list):
            value['log_levels'] = dict(log_levels)

        return decode(value, Config, decoders={LogLevel: LogLevel})


class FatalError(SystemExit):
    def __init__(self, *args) -> None:
        super().__init__(f'💀 {" ".join(str(arg) for arg in args)}')


class ConfigError(FatalError):
    def __init__(self, config_source: str = None, *args) -> None:
        message = 'Could not load config'
        if config_source:
            message += f' from {config_source}'
            if args:
                message += ': ' + ' '.join(str(a) for a in args)
        super().__init__(message)


def parse_key_value_pair(value: str) -> tuple[str, str]:
    key, value = value.split('=', 1)
    return key, value


def try_parse_key_value_pair(value: str) -> str | tuple[str, str]:
    try:
        return parse_key_value_pair(value)
    except ValueError:
        return value


def config_from_args(_config_source: str) -> Config | None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '-t',
        '--tasks',
        dest='tasks',
        nargs='+',
        metavar='COMMAND | NAME=COMMAND',
        type=try_parse_key_value_pair,
        default={},
    )
    arg_parser.add_argument(
        '-l',
        '--log-levels',
        dest='log_levels',
        nargs='+',
        metavar='OUTPUT=LOGLEVEL (debug | info | warning | error | critical | "")',
        type=parse_key_value_pair,
        default={},
    )
    config_dict = arg_parser.parse_args().__dict__
    return Config.decode(config_dict) if any(config_dict.values()) else None


def config_from_pyproject(config_source: str) -> Config | None:
    try:
        with Path(config_source).open('rb') as f:
            config_dict = tomllib.load(f).get('tool', {}).get('powerchord', {})
    except OSError:
        return None
    return Config.decode(config_dict)


CONFIG_LOADERS = {
    'command line': config_from_args,
    'pyproject.toml': config_from_pyproject,
}


def load_config() -> Config:
    for name, loader in CONFIG_LOADERS.items():
        try:
            config = loader(name)
        except ValueError as exc:
            raise ConfigError(name, *exc.args) from exc
        if config:
            return config
    raise ConfigError
