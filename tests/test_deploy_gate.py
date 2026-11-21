from origin_relay.models import Role
from origin_relay.orchestrator import Orchestrator


def test_no_deploya_si_fallan_las_pruebas():
    deploy_calls: list[str] = []

    result = Orchestrator(
        runners={
            Role.TESTING: lambda _subtask: False,
            Role.DEPLOY: lambda subtask: deploy_calls.append(subtask.id) or True,
        },
        max_attempts=2,
    ).run("Cambio con tests rotos")

    assert deploy_calls == []
    assert result.deployed is False
    assert any(event.role == Role.DEPLOY and event.action == "skip" for event in result.events)
    assert [item.status for item in result.subtasks if item.role == Role.DEPLOY] == [
        "skipped",
        "skipped",
    ]


def test_deploy_es_github_y_despues_azure():
    order: list[str] = []

    result = Orchestrator(
        runners={Role.DEPLOY: lambda subtask: order.append(subtask.id) or True}
    ).run("Cambio listo")

    assert order == ["deploy-github", "deploy-azure"]
    assert result.deployed is True


def test_si_github_falla_no_publica_en_azure():
    order: list[str] = []

    result = Orchestrator(
        runners={
            Role.DEPLOY: lambda subtask: order.append(subtask.id) or subtask.id != "deploy-github"
        },
        max_attempts=1,
    ).run("Release")

    assert order == ["deploy-github"]
    azure = next(item for item in result.subtasks if item.id == "deploy-azure")
    assert azure.status == "skipped"
    assert result.deployed is False
