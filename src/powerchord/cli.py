import asyncio
import sys

from .config import load_config
from .logging import logging_context
from .runner import TaskRunner


def main() -> None:
    config = load_config()
    with logging_context(config.log_levels):
        success = asyncio.run(TaskRunner(config.tasks).run_tasks())
    sys.exit(not success)
