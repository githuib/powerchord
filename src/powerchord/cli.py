import asyncio
import sys

from based_utils.cli import killed_by_errors

from . import log
from .config import CLIConfig, LoadConfigError, PyprojectConfig, load_config
from .runner import TaskRunner


@killed_by_errors(LoadConfigError, unknown_message="Something went wrong.")
def main() -> None:
    config = load_config(CLIConfig, PyprojectConfig)
    levels = config.log_levels
    lvl_main, lvl_tasks = levels.all, levels.tasks
    lvl_tasks_s = min(levels.successful_tasks, lvl_tasks)
    lvl_tasks_f = min(levels.failed_tasks, lvl_tasks)
    runner = TaskRunner(config.tasks)
    with log.context(lvl_main, successful_tasks=lvl_tasks_s, failed_tasks=lvl_tasks_f):
        asyncio.run(runner.run_tasks())
    sys.exit(runner.failed_summary)
