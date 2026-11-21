from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from origin_relay.models import Event, Phase, PipelineResult, Role, Subtask
from origin_relay.runners import AZURE_DEPLOY_ENV, default_runners

Runner = Callable[[Subtask], bool]

_PARTIAL_DETAIL = (
    "Deploy a medias: GitHub quedó publicado y Azure falló. No se revierten commits."
)


class Orchestrator:
    """Grafo: programar → pytest → Bandit → GitHub → Azure.

    Programar sin agente falla. Bandit ausente falla. GitHub es `git push` y no
    revierte commits. Azure corre después y solo si hay un comando configurado.
    """

    def __init__(
        self,
        runners: dict[Role, Runner] | None = None,
        max_attempts: int = 2,
        workdir: Path | str | None = None,
        command_runner: Callable | None = None,
        azure_deploy_command: str | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts debe ser >= 1")
        self.max_attempts = max_attempts
        self.workdir = Path(workdir) if workdir is not None else Path.cwd()
        if azure_deploy_command is None:
            azure_deploy_command = os.environ.get(AZURE_DEPLOY_ENV)
        self.runners = default_runners(
            self.workdir,
            command_runner,
            azure_deploy_command,
        )
        if runners:
            self.runners.update(runners)

    def split_task(self, description: str) -> list[Subtask]:
        """Parte la descripción en subtareas de programación y adjunta las puertas del pipeline."""
        work_items = _work_items(description)
        subtasks: list[Subtask] = []
        for index, title in enumerate(work_items, start=1):
            subtasks.append(
                Subtask(
                    id=f"code-{index}",
                    title=title,
                    role=Role.PROGRAMMING,
                    phase=Phase.IMPLEMENTATION,
                    max_attempts=self.max_attempts,
                )
            )
        subtasks.extend(
            [
                Subtask(
                    id="tests",
                    title="Pruebas unitarias y BDD",
                    role=Role.TESTING,
                    phase=Phase.PULL_REQUEST,
                    max_attempts=self.max_attempts,
                ),
                Subtask(
                    id="security",
                    title="Seguridad en el pull request",
                    role=Role.SECURITY,
                    phase=Phase.PULL_REQUEST,
                    max_attempts=self.max_attempts,
                ),
                Subtask(
                    id="deploy-github",
                    title="Publicar historial en GitHub",
                    role=Role.GITHUB,
                    phase=Phase.DEPLOY,
                    max_attempts=self.max_attempts,
                ),
                Subtask(
                    id="deploy-azure",
                    title="Publicar en Azure",
                    role=Role.AZURE,
                    phase=Phase.DEPLOY,
                    max_attempts=self.max_attempts,
                ),
            ]
        )
        return subtasks

    def run(self, description: str) -> PipelineResult:
        subtasks = self.split_task(description)
        events: list[Event] = [Event(Phase.INTAKE, None, "split")]

        if not self._run_role(subtasks, Role.PROGRAMMING, events):
            return self._blocked(description, subtasks, events)

        events.append(Event(Phase.PULL_REQUEST, None, "pr_opened"))

        tests_ok = self._run_role(subtasks, Role.TESTING, events)
        security_ok = self._run_role(subtasks, Role.SECURITY, events)
        if not tests_ok or not security_ok:
            return self._blocked(description, subtasks, events)

        if not self._run_role(subtasks, Role.GITHUB, events):
            return self._blocked(description, subtasks, events)

        if not self._run_role(subtasks, Role.AZURE, events):
            self._mark_partial(subtasks)
            return self._blocked(description, subtasks, events, partial=True)

        return PipelineResult(
            description=description,
            subtasks=subtasks,
            events=events,
            deployed=True,
            phase=Phase.DONE,
        )

    def _run_role(
        self, subtasks: list[Subtask], role: Role, events: list[Event]
    ) -> bool:
        for subtask in (item for item in subtasks if item.role == role):
            if not self._run_with_retry(subtask, events):
                self._skip_role(subtasks, role, events)
                return False
        return True

    def _run_with_retry(self, subtask: Subtask, events: list[Event]) -> bool:
        runner = self.runners[subtask.role]
        while subtask.attempts < subtask.max_attempts:
            subtask.attempts += 1
            events.append(Event(subtask.phase, subtask.role, "start"))
            subtask.error = ""
            try:
                ok = bool(runner(subtask))
            except Exception as exc:
                ok = False
                subtask.error = f"{type(exc).__name__}: {exc}"
            if ok:
                subtask.status = "passed"
                events.append(Event(subtask.phase, subtask.role, "pass"))
                return True
            if subtask.attempts < subtask.max_attempts:
                subtask.status = "retrying"
                events.append(Event(subtask.phase, subtask.role, "retry"))
            else:
                subtask.status = "failed"
                events.append(Event(subtask.phase, subtask.role, "fail"))
                return False
        return False

    def _skip_role(
        self, subtasks: list[Subtask], role: Role, events: list[Event]
    ) -> None:
        for subtask in (item for item in subtasks if item.role == role):
            if subtask.status == "pending":
                subtask.status = "skipped"
                events.append(Event(subtask.phase, role, "skip"))

    def _skip_all_pending(self, subtasks: list[Subtask], events: list[Event]) -> None:
        for subtask in subtasks:
            if subtask.status == "pending":
                subtask.status = "skipped"
                events.append(Event(subtask.phase, subtask.role, "skip"))

    def _mark_partial(self, subtasks: list[Subtask]) -> None:
        for subtask in subtasks:
            if subtask.role == Role.GITHUB and subtask.status == "passed":
                subtask.detail = _PARTIAL_DETAIL

    def _blocked(
        self,
        description: str,
        subtasks: list[Subtask],
        events: list[Event],
        *,
        partial: bool = False,
    ) -> PipelineResult:
        self._skip_all_pending(subtasks, events)
        if partial:
            events.append(Event(Phase.DEPLOY, Role.AZURE, "partial"))
        events.append(Event(Phase.BLOCKED, None, "blocked"))
        return PipelineResult(
            description=description,
            subtasks=subtasks,
            events=events,
            deployed=False,
            partial_deploy=partial,
            phase=Phase.BLOCKED,
        )


def _work_items(description: str) -> list[str]:
    items: list[str] = []
    for raw_line in description.splitlines():
        line = raw_line.strip().lstrip("-*").strip()
        if line:
            items.append(line)
    if items:
        return items
    stripped = description.strip()
    return [stripped] if stripped else ["Tarea sin título"]
