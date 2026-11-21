# Origin Relay

Orquestador versionable y testeable de agentes con roles. **Repo separado** y **reutilizable**: no es el producto de administración de propiedades.

Recibe una tarea, la parte en subtareas, asigna cada rol, espera resultados y decide si avanza o reintenta.

## Flujo

v0: **código → pruebas → deploy**. Crece con el tiempo.

Seguridad corre en **cada pull request**, no al final del proyecto ni después de publicar.

Deploy: primero **GitHub** (historial y ramas para revertir), después **Azure**. Si Azure falla, se revierte desde GitHub.

## Roles

| Rol | Qué hace | Cuándo |
| --- | --- | --- |
| Programación | Implementa el cambio | Antes del PR |
| Pruebas unitarias y BDD | BDD define el comportamiento; las unitarias lo verifican por dentro | En el PR. Sin verde, no hay deploy |
| Seguridad | Revisión del cambio | En **cada** PR, no al final |
| Deploy | GitHub y luego Azure | Solo si pruebas y seguridad pasaron |

Detalle en [`docs/roles.md`](docs/roles.md) y [`docs/flujo.md`](docs/flujo.md).

## Qué es v0 (y qué no)

Esto es un **esqueleto**: un grafo mínimo en Python, tests de contrato y un placeholder de CI. No es un framework completo.

La referencia de diseño es [LangGraph](https://github.com/langchain-ai/langgraph) o [CrewAI](https://github.com/crewAIInc/crewAI). v0 no las empaqueta como dependencia: un grafo simple alcanza para partir, asignar, esperar, reintentar y bloquear el deploy.

## Estructura

```
src/origin_relay/   orquestador
tests/              contratos del grafo
docs/               roles y flujo
.github/workflows/  test + security en cada PR
```

## Uso local

Python 3.11+.

```bash
python -m pip install -e ".[dev]"
pytest
python -m origin_relay "Login con correo
Logout"
```

Los tests cubren: partir la tarea, fallar un rol y reintentar, no deployar si fallan las pruebas, y que la seguridad corre en el PR (no al final).

## CI

[`.github/workflows/pr.yml`](.github/workflows/pr.yml) tiene dos jobs en el pull request:

- `test` — `pytest`
- `security` — puerta de seguridad del PR (placeholder con Bandit). Si falla, no hay merge ni deploy.

## Dónde vive el código

- Local: `D:\Code\OriginRelay` (hermano de `D:\Code\AdministracionPropiedades`)
- GitHub (si el remote existe): <https://github.com/balzanoa/OriginRelay>
- No vive dentro del producto de propiedades ni en el perfil `balzanoa/balzanoa`.
