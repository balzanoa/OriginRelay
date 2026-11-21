from origin_relay.__main__ import description_from_args, main
from origin_relay.models import Role
from origin_relay.orchestrator import Orchestrator


def _programming_titles(arguments: list[str]) -> list[str]:
    description = description_from_args(arguments)
    return [
        item.title
        for item in Orchestrator().split_task(description)
        if item.role == Role.PROGRAMMING
    ]


def _programming_passes(output: str) -> int:
    return output.count("[implementation] programming pass")


def test_un_argumento_es_una_subtarea(capsys):
    code = main(["Logout"])
    output = capsys.readouterr().out

    assert code == 0
    assert _programming_titles(["Logout"]) == ["Logout"]
    assert output.startswith("tarea: Logout\n")
    assert _programming_passes(output) == 1


def test_cada_argumento_es_una_subtarea(capsys):
    code = main(["Login con correo", "Logout"])
    output = capsys.readouterr().out

    assert code == 0
    assert _programming_titles(["Login con correo", "Logout"]) == [
        "Login con correo",
        "Logout",
    ]
    assert output.startswith("tarea: Login con correo\nLogout\n")
    assert _programming_passes(output) == 2


def test_frase_con_espacios_es_una_sola_subtarea(capsys):
    code = main(["Login con correo"])
    output = capsys.readouterr().out

    assert code == 0
    assert _programming_titles(["Login con correo"]) == ["Login con correo"]
    assert output.startswith("tarea: Login con correo\n")
    assert _programming_passes(output) == 1
