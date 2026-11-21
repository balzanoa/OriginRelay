"""Runners del grafo. Ninguno devuelve True si no hizo el trabajo."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from origin_relay.models import Role, Subtask

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

AZURE_DEPLOY_ENV = "ORIGIN_RELAY_AZURE_DEPLOY"


def programming_runner(subtask: Subtask) -> bool:
    """Runner invocable. Sin agente configurado, falla: no marca passed."""
    raise RuntimeError(
        "No hay agente de programación configurado para "
        f"{subtask.id} ({subtask.title}). El rol no se marca passed."
    )


def testing_runner(
    subtask: Subtask,
    *,
    workdir: Path,
    command_runner: CommandRunner,
) -> bool:
    del subtask
    completed = command_runner(
        [sys.executable, "-m", "pytest"],
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def security_runner(
    subtask: Subtask,
    *,
    workdir: Path,
    command_runner: CommandRunner,
) -> bool:
    del subtask
    probe = command_runner(
        [sys.executable, "-c", "import bandit"],
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise RuntimeError(
            "Bandit no está instalado. El rol de seguridad falla y no se marca passed."
        )
    completed = command_runner(
        [sys.executable, "-m", "bandit", "-r", "src", "-ll"],
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def github_runner(
    subtask: Subtask,
    *,
    workdir: Path,
    command_runner: CommandRunner,
) -> bool:
    """Publica HEAD en origin. No revierte commits."""
    del subtask
    completed = command_runner(
        ["git", "push", "origin", "HEAD"],
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "git push falló").strip()
        raise RuntimeError(f"GitHub no publicó el historial: {detail}")
    return True


def azure_runner(
    subtask: Subtask,
    *,
    workdir: Path,
    command_runner: CommandRunner,
    deploy_command: str,
) -> bool:
    """Ejecuta el comando ya configurado. No elige el proyecto destino."""
    del subtask
    command = deploy_command.strip()
    if not command:
        raise RuntimeError(
            "No hay destino de Azure configurado "
            f"({AZURE_DEPLOY_ENV}). No se elige un proyecto y el rol no se marca passed."
        )
    completed = command_runner(
        shlex.split(command, posix=(sys.platform != "win32")),
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "el deploy de Azure falló").strip()
        raise RuntimeError(f"Azure falló: {detail}")
    return True


def default_runners(
    workdir: Path,
    command_runner: CommandRunner | None = None,
    azure_deploy_command: str | None = None,
) -> dict[Role, Callable[[Subtask], bool]]:
    run = command_runner or subprocess.run
    if azure_deploy_command is None:
        azure_deploy_command = os.environ.get(AZURE_DEPLOY_ENV, "")

    def testing(subtask: Subtask) -> bool:
        return testing_runner(subtask, workdir=workdir, command_runner=run)

    def security(subtask: Subtask) -> bool:
        return security_runner(subtask, workdir=workdir, command_runner=run)

    def github(subtask: Subtask) -> bool:
        return github_runner(subtask, workdir=workdir, command_runner=run)

    def azure(subtask: Subtask) -> bool:
        return azure_runner(
            subtask,
            workdir=workdir,
            command_runner=run,
            deploy_command=azure_deploy_command or "",
        )

    return {
        Role.PROGRAMMING: programming_runner,
        Role.TESTING: testing,
        Role.SECURITY: security,
        Role.GITHUB: github,
        Role.AZURE: azure,
    }
