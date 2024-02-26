import asyncio
import sys

from .config import CLIConfig, LoadConfigError, PyprojectConfig, load_config
from .logging import logging_context
from .runner import TaskRunner
from .utils import catch_unknown_errors, killed_by


@catch_unknown_errors()
@killed_by(LoadConfigError)
def main() -> None:
    config = load_config(CLIConfig, PyprojectConfig)
    with logging_context(config.log_levels):
        success = asyncio.run(TaskRunner(config.tasks).run_tasks())
    sys.exit(not success)
