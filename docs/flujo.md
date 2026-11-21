# Flujo v0

```
tarea
  → partir en subtareas
  → programación
  → abrir pull request
  → pruebas unitarias/BDD  +  seguridad   (puertas del PR)
  → si ambas pasan: GitHub  →  Azure
  → si alguna falla: reintentar el rol; sin deploy
```

El grafo vive en `src/origin_relay/orchestrator.py`. Es un estado versionable y testeable, no un framework.

Más adelante se puede mapear el mismo grafo a LangGraph o CrewAI sin cambiar los roles ni las pruebas de contrato.
