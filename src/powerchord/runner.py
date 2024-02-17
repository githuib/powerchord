import logging

from .formatting import bright, dim, status
from .logging import ASYNC_LOG, task_log
from .utils import concurrent_call, exec_command, timed_awaitable

log = ASYNC_LOG


class TaskRunner:
    def __init__(self, tasks: dict[str, str]) -> None:
        self.tasks = tasks
        self.max_name_length = max(len(n) for n in tasks) if tasks else 0

    async def run_task(self, name: str, task: str) -> tuple[str, bool]:
        (success, (out, err)), duration = await timed_awaitable(exec_command(task))
        log.info(f'{status(success)} {name.ljust(self.max_name_length)}  {dim(duration)}')
        for level, stream in ((logging.INFO, out), (logging.ERROR, err)):
            if stream:
                task_log(success).log(level, stream.decode())
        return name, success

    async def run_tasks(self) -> list[tuple[str, bool]]:
        if not self.tasks:
            log.warning('Nothing to do. Getting bored...\n')
            return []
        tasks = self.tasks.items()
        summary = [f'• {name.ljust(self.max_name_length)}  {dim(task)}' for name, task in tasks]
        for line in (bright('To do:'), *summary, '', bright('Results:')):
            log.info(line)
        return await concurrent_call(self.run_task, tasks)
