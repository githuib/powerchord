# Powerchord: Concurrent CLI task runner

[![Poetry](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/githuib/powerchord/master/assets/logo.json)](https://pypi.org/project/powerchord)
[![PyPI - Version](https://img.shields.io/pypi/v/powerchord)](https://pypi.org/project/powerchord/#history)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/powerchord)](https://pypi.org/project/powerchord)

## Installation

```sh
python3 -m pip install -U powerchord
```

## Usage

Currently, tasks need to be specified in `pyproject.toml`:

```toml
# tasks to do
[tool.powerchord.tasks]
do-something = "command --foo bar /path/to/happiness"
do-something-else = "..."
you-get-the-idea = "..."

# config
[tool.powerchord.verbosity]
# show output of successful tasks
success = ["info", "error"]  # default []
# show output of failed tasks
fail = ["info", "error"]  # default ["info", "error"]
```
