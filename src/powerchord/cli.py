import asyncio
import sys
from dataclasses import asdict

from based_utils.cli import LogLevel, catch_unknown_errors, killed_by

from . import log
from .config import CLIConfig, LoadConfigError, PyprojectConfig, load_config
from .runner import TaskRunner


@catch_unknown_errors()
@killed_by(LoadConfigError)
def main() -> None:
    config = load_config(CLIConfig, PyprojectConfig)
    log_levels = asdict(config.log_levels)
    main_level = log_levels.pop("all", LogLevel.INFO)
    with log.context(main_level, **log_levels):
        success = asyncio.run(TaskRunner(config.tasks).run_tasks())
    sys.exit(not success)
