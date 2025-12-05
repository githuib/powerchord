import asyncio
import sys

from based_utils.cli import killed_by_errors

from . import log
from .config import CLIConfig, LoadConfigError, PyprojectConfig, load_config
from .runner import TaskRunner


@killed_by_errors(LoadConfigError, unknown_message="Something went wrong.")
def main() -> None:
    config = load_config(CLIConfig, PyprojectConfig)
    log_levels = config.log_levels
    with log.context(
        log_levels.all,
        successful_tasks=log_levels.successful_tasks or log_levels.tasks,
        failed_tasks=log_levels.failed_tasks or log_levels.tasks,
    ):
        ran_without_errors = asyncio.run(TaskRunner(config.tasks).run_tasks())
    sys.exit(not ran_without_errors)
