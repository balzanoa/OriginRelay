from __future__ import annotations

import argparse

from origin_relay.orchestrator import Orchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Origin Relay: parte una tarea, asigna roles y corre el grafo código → pruebas → deploy."
    )
    parser.add_argument(
        "tarea",
        nargs="*",
        help="Descripción de la tarea. Varias líneas se parten en subtareas de programación.",
    )
    args = parser.parse_args(argv)
    description = " ".join(args.tarea).strip() or "Tarea de ejemplo"
    result = Orchestrator().run(description)
    print(result.summary())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
