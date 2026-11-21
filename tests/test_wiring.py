import subprocess
import sys

import pytest

from origin_relay.models import Phase, Role, Subtask
from origin_relay.orchestrator import Orchestrator
from origin_relay.runners import programming_runner


def _completed(args, code, stderr=""):
    return subprocess.CompletedProcess(args, code, stdout="", stderr=stderr)


def _forbid(*_args, **_kwargs):
    raise AssertionError("no debía ejecutar un comando")


def test_el_runner_de_programacion_es_invocable_y_no_finge_exito():
    subtask = Subtask(
        id="code-1",
        title="Login",
        role=Role.PROGRAMMING,
        phase=Phase.IMPLEMENTATION,
    )
    with pytest.raises(RuntimeError, match="No hay agente de programación"):
        programming_runner(subtask)


def test_sin_agente_programacion_falla_y_el_resto_queda_skipped():
    result = Orchestrator(
        command_runner=_forbid,
        azure_deploy_command="",
        max_attempts=1,
    ).run("Una\nOtra")

    statuses = {item.id: item.status for item in result.subtasks}
    assert statuses["code-1"] == "failed"
    assert "No hay agente de programación" in result.subtasks[0].error
    assert statuses["code-2"] == "skipped"
    assert statuses["tests"] == "skipped"
    assert statuses["security"] == "skipped"
    assert statuses["deploy-github"] == "skipped"
    assert statuses["deploy-azure"] == "skipped"
    assert "pending" not in statuses.values()
    assert result.deployed is False


def test_una_excepcion_del_runner_queda_failed():
    calls = {"n": 0}

    def explode(_subtask):
        calls["n"] += 1
        raise ValueError("cortó")

    result = Orchestrator(
        runners={Role.PROGRAMMING: explode},
        command_runner=_forbid,
        max_attempts=2,
    ).run("Pieza")

    programming = next(item for item in result.subtasks if item.role == Role.PROGRAMMING)
    assert calls["n"] == 2
    assert programming.status == "failed"
    assert "cortó" in programming.error
    assert all(
        item.status == "skipped"
        for item in result.subtasks
        if item.role != Role.PROGRAMMING
    )


def test_pytest_bandit_github_y_azure_corren_en_ese_orden(tmp_path):
    recorded: list[tuple[list[str], str | None]] = []

    def fake_run(args, cwd=None, capture_output=False, text=False):
        del capture_output, text
        recorded.append((list(args), cwd))
        return _completed(args, 0)

    result = Orchestrator(
        runners={Role.PROGRAMMING: lambda _subtask: True},
        workdir=tmp_path,
        command_runner=fake_run,
        azure_deploy_command="echo azure",
        max_attempts=1,
    ).run("Cambio listo")

    commands = [args for args, _cwd in recorded]
    assert commands == [
        [sys.executable, "-m", "pytest"],
        [sys.executable, "-c", "import bandit"],
        [sys.executable, "-m", "bandit", "-r", "src", "-ll"],
        ["git", "push", "origin", "HEAD"],
        ["echo", "azure"],
    ]
    assert {cwd for _args, cwd in recorded} == {str(tmp_path)}
    assert result.ok is True
    assert result.deployed is True


def test_si_bandit_no_esta_instalado_seguridad_falla(tmp_path):
    recorded: list[list[str]] = []

    def fake_run(args, cwd=None, capture_output=False, text=False):
        del cwd, capture_output, text
        recorded.append(list(args))
        if list(args)[1:3] == ["-c", "import bandit"]:
            return _completed(args, 1, "No module named bandit")
        return _completed(args, 0)

    result = Orchestrator(
        runners={Role.PROGRAMMING: lambda _subtask: True},
        workdir=tmp_path,
        command_runner=fake_run,
        azure_deploy_command="echo azure",
        max_attempts=1,
    ).run("Cambio")

    security = next(item for item in result.subtasks if item.role == Role.SECURITY)
    assert security.status == "failed"
    assert "Bandit no está instalado" in security.error
    assert all(
        item.status == "skipped"
        for item in result.subtasks
        if item.role in {Role.GITHUB, Role.AZURE}
    )
    assert ["git", "push", "origin", "HEAD"] not in recorded
    assert result.deployed is False


def test_si_pytest_falla_no_hay_deploy(tmp_path):
    recorded: list[list[str]] = []

    def fake_run(args, cwd=None, capture_output=False, text=False):
        del cwd, capture_output, text
        recorded.append(list(args))
        if list(args)[1:3] == ["-m", "pytest"]:
            return _completed(args, 1, "falló")
        return _completed(args, 0)

    result = Orchestrator(
        runners={Role.PROGRAMMING: lambda _subtask: True},
        workdir=tmp_path,
        command_runner=fake_run,
        azure_deploy_command="echo azure",
        max_attempts=1,
    ).run("Cambio")

    testing = next(item for item in result.subtasks if item.role == Role.TESTING)
    assert testing.status == "failed"
    assert ["git", "push", "origin", "HEAD"] not in recorded
    assert all(
        item.status == "skipped"
        for item in result.subtasks
        if item.role in {Role.GITHUB, Role.AZURE}
    )


def test_si_github_falla_azure_queda_skipped(tmp_path):
    recorded: list[list[str]] = []

    def fake_run(args, cwd=None, capture_output=False, text=False):
        del cwd, capture_output, text
        recorded.append(list(args))
        if list(args)[:2] == ["git", "push"]:
            return _completed(args, 1, "rejected")
        return _completed(args, 0)

    result = Orchestrator(
        runners={Role.PROGRAMMING: lambda _subtask: True},
        workdir=tmp_path,
        command_runner=fake_run,
        azure_deploy_command="echo azure",
        max_attempts=1,
    ).run("Release")

    github = next(item for item in result.subtasks if item.role == Role.GITHUB)
    azure = next(item for item in result.subtasks if item.role == Role.AZURE)
    assert github.status == "failed"
    assert azure.status == "skipped"
    assert ["echo", "azure"] not in recorded
    assert result.partial_deploy is False
    assert result.deployed is False


def test_si_azure_falla_el_deploy_queda_a_medias(tmp_path):
    recorded: list[list[str]] = []

    def fake_run(args, cwd=None, capture_output=False, text=False):
        del cwd, capture_output, text
        recorded.append(list(args))
        if list(args)[:1] == ["echo"]:
            return _completed(args, 1, "azure down")
        return _completed(args, 0)

    result = Orchestrator(
        runners={Role.PROGRAMMING: lambda _subtask: True},
        workdir=tmp_path,
        command_runner=fake_run,
        azure_deploy_command="echo azure",
        max_attempts=1,
    ).run("Release")

    github = next(item for item in result.subtasks if item.role == Role.GITHUB)
    azure = next(item for item in result.subtasks if item.role == Role.AZURE)
    assert github.status == "passed"
    assert azure.status == "failed"
    assert result.partial_deploy is True
    assert result.deployed is False
    assert result.ok is False
    summary = result.summary()
    assert "deploy: a medias" in summary
    assert "No se revierten commits" in summary
    assert all("revert" not in arg for args in recorded for arg in args)
