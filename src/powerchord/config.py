import argparse
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from chili import decode
from gaffe import raises

from .logging import LogLevel, LogLevels
from .runner import Task


class ParseConfigError(Exception):
    pass


def parse_key_value_pair(value: str) -> tuple[str, str]:
    key, value = value.split('=', 1)
    return key, value


def try_parse_key_value_pair(value: str) -> str | tuple[str, str]:
    try:
        return parse_key_value_pair(value)
    except ValueError:
        return value


@raises(ParseConfigError)
def config_from_args(_config_source: str) -> dict:
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
    try:
        return arg_parser.parse_args().__dict__
    except (SystemExit, TypeError) as exc:
        raise ParseConfigError from exc


@raises(ParseConfigError)
def config_from_pyproject(config_source: str) -> dict:
    try:
        with Path(config_source).open('rb') as f:
            return tomllib.load(f).get('tool', {}).get('powerchord', {})
    except OSError:
        return {}
    except ValueError as exc:
        raise ParseConfigError from exc


@dataclass
class Config:
    tasks: list[Task] = field(default_factory=list)
    log_levels: LogLevels = field(default_factory=LogLevels)


class DecodeConfigError(Exception):
    pass


@raises(DecodeConfigError)
def decode_config(value: dict) -> Config | None:
    if not any(value.values()):
        return None
    tasks = value.get('tasks', {})
    if isinstance(tasks, list):
        task_items = [('', t) if isinstance(t, str) else t for t in tasks]
    elif isinstance(tasks, dict):
        task_items = list(tasks.items())
    else:
        raise DecodeConfigError(f'Wrong value for tasks: {tasks}')
    value['tasks'] = [{'command': t, 'name': n} for n, t in task_items]

    log_levels = value.get('log_levels', {})
    if isinstance(log_levels, list):
        value['log_levels'] = dict(log_levels)

    try:
        return decode(value, Config, decoders={LogLevel: LogLevel})
    except ValueError as exc:
        raise DecodeConfigError(*exc.args) from exc


class LoadConfigError(Exception):
    def __init__(self, name: str = '', *args):
        super().__init__(f'Could not load config{name}{":" if args else ""}', *args)


class LoadSpecificConfigError(LoadConfigError):
    def __init__(self, name: str, *args):
        super().__init__(f' from {name}', *args)


CONFIG_LOADERS: dict[str, Callable[[str], dict]] = {
    'command line': config_from_args,
    'pyproject.toml': config_from_pyproject,
}


@raises(LoadConfigError)
def load_config() -> Config:
    for name, loader in CONFIG_LOADERS.items():
        try:
            config = decode_config(loader(name))
        except ParseConfigError as exc:
            raise LoadSpecificConfigError(name, *exc.args) from exc
        if config:
            return config
    raise LoadConfigError
