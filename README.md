# Powerchord: Concurrent CLI task runner

[![Poetry](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/githuib/powerchord/master/assets/logo.json)](https://pypi.org/project/powerchord)
[![PyPI - Version](https://img.shields.io/pypi/v/powerchord)](https://pypi.org/project/powerchord/#history)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/powerchord)](https://pypi.org/project/powerchord)

## Installation

```commandline
pip install powerchord
```

## Usage

Run a number of tasks:

```commandline
powerchord -t task="command --foo bar /path/to/happiness" other-task="..."
```

For all options, see

```commandline
powerchord -h
```

Config can also be specified in `pyproject.toml`:

```toml
[tool.powerchord.tasks]
task = "command --foo bar /path/to/happiness"
other-task = "..."
you-get-the-idea = "..."

[tool.powerchord.log_levels]
all = "debug" | "info" | "warning" | "error" | "critical" | ""
success = "" # log level of successful task output
fail = "info" # log level of failed task output 
```
