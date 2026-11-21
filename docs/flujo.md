# Flujo v0

```
tarea
  → partir en subtareas
  → programación
  → abrir pull request
  → pruebas unitarias/BDD  +  seguridad   (puertas del PR)
  → si ambas pasan: GitHub  →  Azure
  → si programación falla: el resto queda skipped
  → si GitHub falla: Azure queda skipped
  → si Azure falla: deploy a medias, sin revertir commits
  → si alguna puerta falla: reintentar el rol; sin deploy
```

El grafo vive en `src/origin_relay/orchestrator.py`. Es un estado versionable y testeable, no un framework.

Más adelante se puede mapear el mismo grafo a LangGraph o CrewAI sin cambiar los roles ni las pruebas de contrato.
