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


def test_un_argumento_es_una_subtarea(capsys):
    main(["Logout"])
    output = capsys.readouterr().out

    assert _programming_titles(["Logout"]) == ["Logout"]
    assert output.startswith("tarea: Logout\n")


def test_cada_argumento_es_una_subtarea(capsys):
    main(["Login con correo", "Logout"])
    output = capsys.readouterr().out

    assert _programming_titles(["Login con correo", "Logout"]) == [
        "Login con correo",
        "Logout",
    ]
    assert output.startswith("tarea: Login con correo\nLogout\n")


def test_frase_con_espacios_es_una_sola_subtarea(capsys):
    main(["Login con correo"])
    output = capsys.readouterr().out

    assert _programming_titles(["Login con correo"]) == ["Login con correo"]
    assert output.startswith("tarea: Login con correo\n")
