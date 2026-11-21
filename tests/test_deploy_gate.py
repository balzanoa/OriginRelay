from origin_relay.models import Role


def test_no_deploya_si_fallan_las_pruebas(gate):
    deploy_calls: list[str] = []

    def record(subtask):
        deploy_calls.append(subtask.id)
        return True

    result = gate(
        runners={
            Role.TESTING: lambda _subtask: False,
            Role.GITHUB: record,
            Role.AZURE: record,
        },
        max_attempts=2,
    ).run("Cambio con tests rotos")

    assert deploy_calls == []
    assert result.deployed is False
    assert any(event.role == Role.GITHUB and event.action == "skip" for event in result.events)
    assert any(event.role == Role.AZURE and event.action == "skip" for event in result.events)
    assert [item.status for item in result.subtasks if item.role in {Role.GITHUB, Role.AZURE}] == [
        "skipped",
        "skipped",
    ]


def test_deploy_es_github_y_despues_azure(gate):
    order: list[str] = []

    def track(subtask):
        order.append(subtask.id)
        return True

    result = gate(runners={Role.GITHUB: track, Role.AZURE: track}).run("Cambio listo")

    assert order == ["deploy-github", "deploy-azure"]
    assert result.deployed is True


def test_si_github_falla_no_publica_en_azure(gate):
    order: list[str] = []

    def github(subtask):
        order.append(subtask.id)
        return False

    def azure(subtask):
        order.append(subtask.id)
        return True

    result = gate(
        runners={Role.GITHUB: github, Role.AZURE: azure},
        max_attempts=1,
    ).run("Release")

    assert order == ["deploy-github"]
    azure_task = next(item for item in result.subtasks if item.id == "deploy-azure")
    assert azure_task.status == "skipped"
    assert result.deployed is False
    assert result.partial_deploy is False
