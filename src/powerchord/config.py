import argparse
import tomllib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from chili import decode
from gaffe import raises

from .logging import LogLevel, LogLevels
from .runner import Task


class ParseConfigError(Exception):
    pass


@dataclass
class Config:
    tasks: list[Task] = field(default_factory=list)
    log_levels: LogLevels = field(default_factory=LogLevels)


class DecodeConfigError(Exception):
    pass


@dataclass
class ConfigLoader(ABC):
    name: ClassVar[str]

    tasks: list[Task] = field(default_factory=list)
    log_levels: LogLevels = field(default_factory=LogLevels)

    @classmethod
    @raises(ParseConfigError)
    @abstractmethod
    def _parse(cls) -> dict:
        pass

    @classmethod
    @raises(ParseConfigError, DecodeConfigError)
    def load(cls) -> Config | None:
        config_dict = cls._parse()
        if not any(config_dict.values()):
            return None

        tasks = config_dict.get("tasks", {})
        if isinstance(tasks, list):
            task_items = [("", t) if isinstance(t, str) else t for t in tasks]
        elif isinstance(tasks, dict):
            task_items = list(tasks.items())
        else:
            raise DecodeConfigError(f"Wrong value for tasks: {tasks}")
        config_dict["tasks"] = [{"command": t, "name": n} for n, t in task_items]

        log_levels = config_dict.get("log_levels", {})
        if isinstance(log_levels, list):
            config_dict["log_levels"] = dict(log_levels)

        try:
            return decode(config_dict, Config, decoders={LogLevel: LogLevel})
        except ValueError as exc:
            raise DecodeConfigError(*exc.args) from exc


def parse_key_value_pair(value: str) -> tuple[str, str]:
    key, value = value.split("=", 1)
    return key, value


def try_parse_key_value_pair(value: str) -> str | tuple[str, str]:
    try:
        return parse_key_value_pair(value)
    except ValueError:
        return value


class CLIConfig(ConfigLoader):
    name = "command line"

    @classmethod
    @raises(ParseConfigError)
    def _parse(cls) -> dict:
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument(
            "-t",
            "--tasks",
            dest="tasks",
            nargs="+",
            metavar="COMMAND | NAME=COMMAND",
            type=try_parse_key_value_pair,
            default={},
        )
        arg_parser.add_argument(
            "-l",
            "--log-levels",
            dest="log_levels",
            nargs="+",
            metavar='OUTPUT=LOGLEVEL (debug | info | warning | error | critical | "")',
            type=parse_key_value_pair,
            default={},
        )
        try:
            return arg_parser.parse_args().__dict__
        except (argparse.ArgumentError, SystemExit, TypeError) as exc:
            raise ParseConfigError from exc


class PyprojectConfig(ConfigLoader):
    name = "pyproject.toml"

    @classmethod
    @raises(ParseConfigError)
    def _parse(cls) -> dict:
        try:
            with Path("pyproject.toml").open("rb") as f:
                return tomllib.load(f).get("tool", {}).get("powerchord", {})
        except OSError:
            return {}
        except ValueError as exc:
            raise ParseConfigError from exc


class LoadConfigError(Exception):
    def __init__(self, name: str = "", *args):
        super().__init__(f"Could not load config{name}{':' if args else ''}", *args)


class LoadSpecificConfigError(LoadConfigError):
    def __init__(self, name: str, *args):
        super().__init__(f" from {name}", *args)


@raises(LoadConfigError)
def load_config(*loaders: type[ConfigLoader]) -> Config:
    for loader_cls in loaders:
        try:
            config = loader_cls.load()
        except (ParseConfigError, DecodeConfigError) as exc:
            raise LoadSpecificConfigError(loader_cls.name, *exc.args) from exc
        if config:
            return config
    raise LoadConfigError
