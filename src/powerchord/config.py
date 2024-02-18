import argparse
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chili import decode

from .logging import LogLevel, LogLevels


@dataclass
class Config:
    tasks: dict[str, str] = field(default_factory=dict)
    log_levels: LogLevels = field(default_factory=LogLevels)

    @classmethod
    def decode(cls, value: dict) -> 'Config':
        return decode(value, Config, decoders={LogLevel: LogLevel})


class FatalError(SystemExit):
    def __init__(self, *args):
        super().__init__(f'💀 {" ".join(str(arg) for arg in args)}')


class ConfigError(FatalError):
    def __init__(self, config_source: str = None, *args):
        message = 'Could not load config'
        if config_source:
            message += f' from {config_source}'
            if args:
                message += ': ' + ' '.join(str(a) for a in args)
        super().__init__(message)


class ParseDict(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str = None,
    ) -> None:
        value_seq = [values] if isinstance(values, str) else [str(v) for v in values or []]
        try:
            pairs = (item.split('=', 1) for item in value_seq)
            new_pairs = {key.strip(): value for key, value in pairs}
        except ValueError:
            parser.error(
                f'argument {option_string}: not matching pattern key1=val1 [key2=val2 ...]',
            )
        else:
            setattr(namespace, self.dest, (getattr(namespace, self.dest) or {}) | new_pairs)


def config_from_args(_config_source: str) -> Config | None:
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
    arg_parser.add_argument(
        '-l',
        '--log-levels',
        dest='log_levels',
        nargs='+',
        metavar='NAME=COMMAND',
        action=ParseDict,
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
