from origin_relay.models import Phase, Role


def test_seguridad_corre_en_el_pr_no_al_final(gate):
    result = gate().run("Cambio con PR")

    security_events = [event for event in result.events if event.role == Role.SECURITY]
    assert security_events
    assert all(event.phase == Phase.PULL_REQUEST for event in security_events)
    assert result.security_ran_on_pr is True

    pr_opened_index = next(
        index
        for index, event in enumerate(result.events)
        if event.action == "pr_opened"
    )
    first_security = next(
        index
        for index, event in enumerate(result.events)
        if event.role == Role.SECURITY
    )
    first_deploy = next(
        index
        for index, event in enumerate(result.events)
        if event.role in {Role.GITHUB, Role.AZURE}
    )
    assert pr_opened_index < first_security < first_deploy


def test_si_seguridad_falla_no_hay_deploy(gate):
    result = gate(
        runners={Role.SECURITY: lambda _subtask: False},
        max_attempts=1,
    ).run("Cambio inseguro")

    assert result.deployed is False
    assert any(event.role == Role.SECURITY and event.action == "fail" for event in result.events)
    assert all(
        item.status == "skipped"
        for item in result.subtasks
        if item.role in {Role.GITHUB, Role.AZURE}
    )
