# Roles de Origin Relay

Origin Relay asigna trabajo a roles. Cada rol es un agente (humano o automático) con una responsabilidad clara. El orquestador espera el resultado y decide si avanza o reintenta.

Esto no es el sistema de administración de propiedades. Es la pieza reutilizable que coordina cómo se construye software.

## Programación

Implementa el cambio. Recibe una subtarea partida del pedido original y entrega código en una rama.

En el grafo v0 corre en la fase `implementation`, antes de abrir el pull request. El runner es invocable. Si no hay agente configurado, falla con un error claro y no marca passed.

## Pruebas unitarias y BDD

BDD describe el comportamiento esperado (qué debe pasar). Las unitarias verifican ese comportamiento por dentro (cómo está armado).

En el grafo v0 corre `pytest` en el repo de trabajo, en la fase `pull_request`. Si falla, el orquestador reintenta; si agota reintentos, **no hay deploy**.

## Seguridad

Revisa el cambio en **cada pull request**: secretos, dependencias, patrones inseguros. No es un control que se deja para el final del proyecto ni para después de publicar.

En el grafo v0 corre Bandit sobre `src`, en la fase `pull_request`, junto con las pruebas y **antes** de GitHub/Azure. Si Bandit no está instalado, el rol falla. En CI es el job `security` del workflow de PR.

Si falla, no hay merge ni deploy.

## Deploy

Dos pasos, en este orden:

1. **GitHub** — `git push` del historial. No revierte commits.
2. **Azure** — corre el comando de `ORIGIN_RELAY_AZURE_DEPLOY`. No elige el proyecto. Si no hay comando, falla. Si Azure falla después de GitHub, el deploy queda a medias: GitHub sigue publicado y el resultado lo dice.

Ninguno corre si las pruebas o la seguridad del PR no pasaron. Si GitHub falla, Azure queda skipped.
