import logging

from .formatting import bright, dim, status
from .logging import ASYNC_LOG, task_log
from .utils import concurrent_call, exec_command, timed_awaitable

log = ASYNC_LOG


class TaskRunner:
    def __init__(self, tasks: dict[str, str]) -> None:
        self.tasks = tasks
        self.max_name_length = max(len(n) for n in tasks) if tasks else 0

    async def run_tasks(self) -> bool:
        if not self.tasks:
            log.warning('Nothing to do. Getting bored...\n')
            return True
        tasks = self.tasks.items()
        summary = [f'• {name.ljust(self.max_name_length)}  {dim(task)}' for name, task in tasks]
        for line in (bright('To do:'), *summary, '', bright('Results:')):
            log.info(line)
        results = await concurrent_call(self._run_task, tasks)
        failed_tasks = [task for task, ok in results if not ok]
        if failed_tasks:
            log.error('')
            log.error(f'{bright("Failed tasks:")} {failed_tasks}')
        return not failed_tasks

    async def _run_task(self, name: str, task: str) -> tuple[str, bool]:
        (success, (out, err)), duration = await timed_awaitable(exec_command(task))
        log.info(f'{status(success)} {name.ljust(self.max_name_length)}  {dim(duration)}')
        for level, stream in ((logging.INFO, out), (logging.ERROR, err)):
            if stream:
                task_log(success).log(level, stream.decode())
        return name, success
