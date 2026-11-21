from __future__ import annotations

import argparse

from origin_relay.orchestrator import Orchestrator


def description_from_args(arguments: list[str]) -> str:
    """Cada argumento es una subtarea. Los espacios internos se conservan."""
    lines = [argument.strip() for argument in arguments if argument.strip()]
    return "\n".join(lines) if lines else "Tarea de ejemplo"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Origin Relay: parte una tarea, asigna roles y corre el grafo código → pruebas → deploy."
    )
    parser.add_argument(
        "tarea",
        nargs="*",
        help="Cada argumento es una subtarea de programación. Una frase entre comillas cuenta como una sola.",
    )
    args = parser.parse_args(argv)
    description = description_from_args(args.tarea)
    result = Orchestrator().run(description)
    print(result.summary())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
