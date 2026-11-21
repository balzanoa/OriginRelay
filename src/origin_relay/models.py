from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    """Roles que el orquestador asigna. No son el producto de propiedades."""

    PROGRAMMING = "programming"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOY = "deploy"


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


@dataclass
class PipelineResult:
    description: str
    subtasks: list[Subtask]
    events: list[Event] = field(default_factory=list)
    deployed: bool = False
    phase: Phase = Phase.BLOCKED

    @property
    def ok(self) -> bool:
        return self.phase == Phase.DONE and self.deployed

    @property
    def security_ran_on_pr(self) -> bool:
        security_events = [e for e in self.events if e.role == Role.SECURITY]
        return bool(security_events) and all(
            e.phase == Phase.PULL_REQUEST for e in security_events
        )

    def summary(self) -> str:
        lines = [
            f"tarea: {self.description}",
            f"fase: {self.phase.value}",
            f"deploy: {'sí' if self.deployed else 'no'}",
            "eventos:",
        ]
        for event in self.events:
            role = event.role.value if event.role else "-"
            lines.append(f"  [{event.phase.value}] {role} {event.action}")
        return "\n".join(lines)
