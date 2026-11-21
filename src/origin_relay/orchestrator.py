from __future__ import annotations

from collections.abc import Callable

from origin_relay.models import Event, Phase, PipelineResult, Role, Subtask

Runner = Callable[[Subtask], bool]


def _always_pass(_subtask: Subtask) -> bool:
    return True


class Orchestrator:
    """Grafo mínimo: recibe una tarea, la parte, asigna roles, espera, avanza o reintenta.

    Flujo v0: código → pruebas → deploy.
    Seguridad corre en la fase de pull request, no después del deploy.
    Deploy: GitHub primero (historial revertible), Azure después.
    """

    def __init__(
        self,
        runners: dict[Role, Runner] | None = None,
        max_attempts: int = 2,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts debe ser >= 1")
        self.runners = runners or {}
        self.max_attempts = max_attempts

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
                    role=Role.DEPLOY,
                    phase=Phase.DEPLOY,
                    max_attempts=self.max_attempts,
                ),
                Subtask(
                    id="deploy-azure",
                    title="Publicar en Azure",
                    role=Role.DEPLOY,
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
            self._skip_role(subtasks, Role.DEPLOY, events)
            return self._blocked(description, subtasks, events)

        if not self._run_role(subtasks, Role.DEPLOY, events):
            return self._blocked(description, subtasks, events)

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
                self._skip_pending(subtasks, role, events)
                return False
        return True

    def _run_with_retry(self, subtask: Subtask, events: list[Event]) -> bool:
        runner = self.runners.get(subtask.role, _always_pass)
        while subtask.attempts < subtask.max_attempts:
            subtask.attempts += 1
            events.append(Event(subtask.phase, subtask.role, "start"))
            if runner(subtask):
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

    def _skip_pending(
        self, subtasks: list[Subtask], role: Role, events: list[Event]
    ) -> None:
        self._skip_role(subtasks, role, events)

    def _blocked(
        self,
        description: str,
        subtasks: list[Subtask],
        events: list[Event],
    ) -> PipelineResult:
        events.append(Event(Phase.BLOCKED, None, "blocked"))
        return PipelineResult(
            description=description,
            subtasks=subtasks,
            events=events,
            deployed=False,
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
