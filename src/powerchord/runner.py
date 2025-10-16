import logging
from dataclasses import dataclass

from .formatting import FAIL, bright, dim, status
from .logging import ASYNC_LOG, task_log
from .utils import concurrent_call, exec_command, timed_awaitable

log = ASYNC_LOG


@dataclass
class Task:
    command: str
    name: str = ""

    @property
    def id(self) -> str:
        return self.name or self.command


class TaskRunner:
    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = tasks
        self.has_named_tasks = any(t.name for t in tasks)
        self.max_name_length = max(len(t.id) for t in tasks or [Task("")])

    async def run_tasks(self) -> bool:
        if not self.tasks:
            log.warning("Nothing to do. Getting bored...\n")
            return True
        if self.has_named_tasks:
            await self._show_todo()
        results = await concurrent_call(self._run_task, self.tasks)
        failed_tasks = [task for task, ok in results if not ok]
        if failed_tasks:
            log.error("")
            log.error(f"{FAIL} {bright('Failed tasks:')} {failed_tasks}")
        return not failed_tasks

    def _task_line(self, bullet: str, task: Task, data: str) -> str:
        return f"{bullet} {task.id.ljust(self.max_name_length)}  {dim(data)}"

    async def _show_todo(self) -> None:
        summary = [self._task_line("•", task, task.command) for task in self.tasks]
        for line in (bright("To do:"), *summary, "", bright("Results:")):
            log.info(line)

    async def _run_task(self, task: Task) -> tuple[str, bool]:
        (success, output_streams), duration = await timed_awaitable(
            exec_command(task.command)
        )
        log_level = logging.INFO if success else logging.ERROR
        log.log(log_level, self._task_line(status(success), task, duration))
        for stream in output_streams:
            if stream:
                task_log(success).log(log_level, stream.decode())
        return task.id, success
