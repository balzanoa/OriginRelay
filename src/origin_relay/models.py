from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    """Roles que el orquestador asigna. No son el producto de propiedades."""

    PROGRAMMING = "programming"
    TESTING = "testing"
    SECURITY = "security"
    GITHUB = "github"
    AZURE = "azure"


class Phase(str, Enum):
    INTAKE = "intake"
    IMPLEMENTATION = "implementation"
    PULL_REQUEST = "pull_request"
    DEPLOY = "deploy"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Event:
    """Paso registrado del grafo. Sirve para tests y para auditar el pipeline."""

    phase: Phase
    role: Role | None
    action: str


@dataclass
class Subtask:
    id: str
    title: str
    role: Role
    phase: Phase
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 2
    error: str = ""
    detail: str = ""


@dataclass
class PipelineResult:
    description: str
    subtasks: list[Subtask]
    events: list[Event] = field(default_factory=list)
    deployed: bool = False
    partial_deploy: bool = False
    phase: Phase = Phase.BLOCKED

    @property
    def ok(self) -> bool:
        return self.phase == Phase.DONE and self.deployed and not self.partial_deploy

    @property
    def security_ran_on_pr(self) -> bool:
        security_events = [e for e in self.events if e.role == Role.SECURITY]
        return bool(security_events) and all(
            e.phase == Phase.PULL_REQUEST for e in security_events
        )

    def summary(self) -> str:
        if self.deployed:
            deploy = "sí"
        elif self.partial_deploy:
            deploy = "a medias"
        else:
            deploy = "no"
        lines = [
            f"tarea: {self.description}",
            f"fase: {self.phase.value}",
            f"deploy: {deploy}",
            "eventos:",
        ]
        for event in self.events:
            role = event.role.value if event.role else "-"
            lines.append(f"  [{event.phase.value}] {role} {event.action}")
        for subtask in self.subtasks:
            if subtask.detail:
                lines.append(f"nota: {subtask.detail}")
            if subtask.error:
                lines.append(f"error: {subtask.error}")
        return "\n".join(lines)
