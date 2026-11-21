from origin_relay.models import Phase, Role
from origin_relay.orchestrator import Orchestrator


def test_split_parte_lineas_en_subtareas_de_programacion():
    orchestrator = Orchestrator()
    subtasks = orchestrator.split_task("Login con correo\nLogout")
    programming = [item for item in subtasks if item.role == Role.PROGRAMMING]

    assert [item.title for item in programming] == ["Login con correo", "Logout"]
    assert {item.role for item in subtasks} == {
        Role.PROGRAMMING,
        Role.TESTING,
        Role.SECURITY,
        Role.GITHUB,
        Role.AZURE,
    }


def test_split_asigna_seguridad_al_pull_request_y_deploy_al_final():
    subtasks = Orchestrator().split_task("Endpoint de salud")

    security = next(item for item in subtasks if item.role == Role.SECURITY)
    testing = next(item for item in subtasks if item.role == Role.TESTING)
    deploys = [item for item in subtasks if item.role in {Role.GITHUB, Role.AZURE}]

    assert security.phase == Phase.PULL_REQUEST
    assert testing.phase == Phase.PULL_REQUEST
    assert [item.id for item in deploys] == ["deploy-github", "deploy-azure"]
    assert [item.role for item in deploys] == [Role.GITHUB, Role.AZURE]
    assert all(item.phase == Phase.DEPLOY for item in deploys)


def test_split_de_texto_vacio_genera_una_subtarea_de_programacion():
    programming = [
        item
        for item in Orchestrator().split_task("   ")
        if item.role == Role.PROGRAMMING
    ]
    assert len(programming) == 1
    assert programming[0].title == "Tarea sin título"
