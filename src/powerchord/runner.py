import logging
from dataclasses import dataclass

from based_utils.cli import human_readable_duration, timed_awaitable

from .formatting import FAIL, OK, bright, dim
from .logging import ASYNC_LOG, task_log
from .utils import concurrent_call, exec_command

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
        (ok, (out, err)), duration = await timed_awaitable(exec_command(task.command))
        log_level = logging.INFO if ok else logging.ERROR
        log.log(
            log_level,
            self._task_line(
                OK if ok else FAIL, task, human_readable_duration(duration)
            ),
        )
        log_task = task_log("success" if ok else "fail", log_level)
        if out:
            log_task(out.decode())
        if err:
            log_task(err.decode())
        return task.id, ok
