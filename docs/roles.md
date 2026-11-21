# Roles de Origin Relay

Origin Relay asigna trabajo a roles. Cada rol es un agente (humano o automático) con una responsabilidad clara. El orquestador espera el resultado y decide si avanza o reintenta.

Esto no es el sistema de administración de propiedades. Es la pieza reutilizable que coordina cómo se construye software.

## Programación

Implementa el cambio. Recibe una subtarea partida del pedido original y entrega código en una rama.

En el grafo v0 corre en la fase `implementation`, antes de abrir el pull request.

## Pruebas unitarias y BDD

BDD describe el comportamiento esperado (qué debe pasar). Las unitarias verifican ese comportamiento por dentro (cómo está armado).

En el grafo v0 corre en la fase `pull_request`. Si falla, el orquestador reintenta; si agota reintentos, **no hay deploy**.

## Seguridad

Revisa el cambio en **cada pull request**: secretos, dependencias, patrones inseguros. No es un control que se deja para el final del proyecto ni para después de publicar.

En el grafo v0 corre en la fase `pull_request`, junto con las pruebas y **antes** de GitHub/Azure. En CI es el job `security` del workflow de PR.

Si falla, no hay merge ni deploy.

## Deploy

Dos pasos, en este orden:

1. **GitHub** — historial y ramas. Es la fuente para revertir.
2. **Azure** — ambiente publicado. Si Azure falla, se revierte desde GitHub.

El rol no corre si las pruebas o la seguridad del PR no pasaron.
