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
$ powerchord -t "ruff check ." pytest mypy
✔ ruff check .  21.075 ms
✔ mypy          166.433 ms
✔ pytest        187.096 ms
```

Tasks can be labeled by passing them as NAME=COMMAND values:

```commandline
$ powerchord -t lint="ruff check ." test=pytest typing=mypy
To do:
• lint    ruff check .
• test    pytest
• typing  mypy

Results:
✔ lint    48.452 ms
✔ typing  202.403 ms
✔ test    286.231 ms
```

Verbosity can be specified for all output, for successful tasks and for failed tasks by setting log levels:

```commandline
$ powerchord -t "ruff chekc ." pytest mypy -l all=info success=info fail=error
✘ ruff chekc .  126.852 ms
chekc:1:1: E902 No such file or directory (os error 2)
Found 1 error.

✔ pytest        255.197 ms
..                                                                       [100%]
2 passed in 0.03s

✔ mypy          542.490 ms
Success: no issues found in 11 source files


✘ Failed tasks: ['ruff chekc .']
```

For all options see the help:

```commandline
powerchord -h
```

Config can also be specified in `pyproject.toml`:

Tasks:
```toml
[tool.powerchord]
tasks = ["command --arg", "...", "..."]
```

Labeled tasks:
```toml
[tool.powerchord.tasks]
task = "command --foo bar /path/to/happiness"
other-task = "..."
you-get-the-idea = "..."
```

Log levels:
```toml
[tool.powerchord.log_levels]
all = "info" # "debug" | "info" | "warning" | "error" | "critical" | ""
success = "" # log level of successful task output
fail = "error" # log level of failed task output 
```
