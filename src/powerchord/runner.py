import logging
from dataclasses import dataclass

from based_utils.asynx import concurrent_call, exec_command
from based_utils.cli import human_readable_duration, timed_awaitable
from kleur.formatting import FAIL, OK, bold, faint

from . import log

_main_logger = log.get_logger()


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
            _main_logger.warning("Nothing to do. Getting bored...\n")
            return True
        if self.has_named_tasks:
            await self._show_todo()
        results = await concurrent_call(self._run_task, self.tasks)
        failed_tasks = [task for task, ok in results if not ok]
        if failed_tasks:
            failed_tasks_str = " ".join(f"{FAIL} {t}" for t in failed_tasks)
            _main_logger.error("")
            _main_logger.error(f"💀 {bold('Failed tasks:')} {failed_tasks_str}")
        return not failed_tasks

    def _task_line(self, bullet: str, task: Task, data: str) -> str:
        return f"{bullet} {task.id.ljust(self.max_name_length)}  {faint(data)}"

    async def _show_todo(self) -> None:
        summary = [self._task_line("•", task, task.command) for task in self.tasks]
        for line in (bold("To do:"), *summary, "", bold("Results:")):
            _main_logger.info(line)

    async def _run_task(self, task: Task) -> tuple[str, bool]:
        result, duration = await timed_awaitable(exec_command(task.command))
        is_successful, (out, err) = result

        log_level = logging.INFO if is_successful else logging.ERROR

        bullet = OK if is_successful else FAIL
        task_line = self._task_line(bullet, task, human_readable_duration(duration))
        _main_logger.log(log_level, task_line)

        logger_name = "successful" if is_successful else "failed"
        task_logger = log.get_logger(f"{logger_name}_tasks")
        if out:
            task_logger.info(out.decode())
        if err:
            task_logger.error(err.decode())

        return task.id, is_successful
