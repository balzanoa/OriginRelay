from origin_relay.models import Role


def test_si_un_rol_falla_lo_reintenta_y_sigue(gate):
    calls: list[str] = []

    def programming(_subtask):
        calls.append("programming")
        return len(calls) >= 2

    result = gate(
        runners={Role.PROGRAMMING: programming},
        max_attempts=2,
    ).run("Una sola pieza")

    assert calls == ["programming", "programming"]
    assert any(event.action == "retry" and event.role == Role.PROGRAMMING for event in result.events)
    assert result.ok
    assert result.deployed


def test_si_el_rol_agota_reintentos_el_pipeline_queda_bloqueado(gate):
    result = gate(
        runners={Role.PROGRAMMING: lambda _subtask: False},
        max_attempts=2,
    ).run("No implementable")

    programming = next(item for item in result.subtasks if item.role == Role.PROGRAMMING)
    assert programming.attempts == 2
    assert programming.status == "failed"
    assert result.deployed is False
    assert result.phase.value == "blocked"
    assert all(
        item.status == "skipped"
        for item in result.subtasks
        if item.role != Role.PROGRAMMING
    )
