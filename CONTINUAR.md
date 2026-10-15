# Punto De Continuidad

Fecha: 2026-10-14

## Estado Actual

- La aplicacion usa React, FastAPI, MySQL y Ollama (`qwen2.5:3b`) para simular
  un agente de mantenimiento SAP; no existe integracion con un servidor SAP real.
- API y frontend se inician con `iniciar_desarrollo.bat`.
- La ultima rama publicada es `bb37f80 Agrega estado real de los servicios`.
- El trabajo de autenticacion, roles, auditoria y seguridad esta terminado de
  forma local, pero aun no fue confirmado ni publicado.
- La ultima verificacion fue `39 passed`; el build de React con
  `npm.cmd run build` tambien finalizo correctamente.

## Base De Datos Local

- Las migraciones `001_agrega_cuentas.sql`, `002_agrega_roles_y_auditoria.sql`
  y `003_refuerza_seguridad.sql` ya se aplicaron en la base MySQL local.
- La cuenta `admin` existe y tiene rol `administrador`.
- No pedir, guardar ni incluir la contrasena de `admin` en archivos, Git o chat.
- Las tablas agregadas son `cuentas`, `sesiones`, `conversaciones`,
  `mensajes_conversacion`, `auditoria` e `intentos_login`.

## Funcionalidad Implementada Sin Commit

- `seguridad.py`: hash scrypt con sal, verificacion de contrasenas, tokens y
  validacion de datos para altas de cuentas.
- `crear_cuenta.py`: crea cuentas sin registro publico, con contraseña oculta,
  usuario valido y contraseña minima de 10 caracteres.
- `api.py`: login/logout con Bearer tokens de ocho horas, proteccion de chat,
  resumen y estado; roles; auditoria y rate limit de cinco intentos fallidos por
  usuario e IP durante quince minutos.
- `tools.py`: persistencia de sesiones, auditoria, conversaciones y una
  transaccion para guardar cada pregunta y respuesta del chat.
- `frontend/src/main.jsx`: pantalla de inicio y cierre de sesion, rol visible y
  conversacion activa almacenada por usuario.
- `database/migrations/001_agrega_cuentas.sql`: cuentas, sesiones y mensajes.
- `database/migrations/002_agrega_roles_y_auditoria.sql`: roles y auditoria.
- `database/migrations/003_refuerza_seguridad.sql`: intentos de login e indices.
- `README.md`: documentacion de migraciones y autenticacion.
- `tests/test_api.py` y `tests/test_seguridad.py`: cobertura de autenticacion,
  rate limit, logout seguro y validaciones.

## Decision De Producto

- La simulacion MySQL es intencional. No intentar conectar SAP real ahora.
- La proxima mejora acordada es hacer visible el historial de conversaciones
  que ya se persiste en MySQL. No incluir borrado de conversaciones por ahora.
- Al reabrir una conversacion se mostraran rol, mensaje y fecha; no se
  persistiran ni mostraran etiquetas de herramientas de sesiones anteriores.

## Proximo Bloque: Historial De Conversaciones

1. En `tools.py`, separar el historial visual del contexto de Ollama:
   conservar los ultimos 10 mensajes para el modelo y crear una consulta de
   hasta 100 mensajes con rol, contenido y fecha.
2. Ampliar `listar_conversaciones` con titulo truncado y `actualizado_en`.
3. Crear `GET /api/conversaciones/{id}` protegido por Bearer, que devuelva
   `404` para conversaciones inexistentes o de otro usuario y `503` ante
   fallos de MySQL.
4. Agregar pruebas para listado, apertura propia, acceso ajeno, limite,
   orden cronologico y errores de base de datos.
5. En React, cargar el listado despues del login, mostrarlo en el panel lateral
   y permitir seleccionar una conversacion para leerla y continuarla.
6. Usar MySQL como fuente de mensajes; dejar `localStorage` solo para sesion e
   ID de conversacion activa.
7. Agregar estados de carga/error, seleccion activa y comportamiento usable en
   movil.
8. Ejecutar `./venv/Scripts/python.exe -m pytest -q` y `npm.cmd run build`.

## Estado De Git

- Hay cambios locales sin commit en `README.md`, `api.py`, `tools.py`,
  `frontend/src/`, `tests/`, `crear_cuenta.py`, `seguridad.py`, migraciones y
  este archivo.
- Antes de confirmar, revisar `git status`, `git diff` y `git log --oneline -10`.
- No hacer commit ni push sin solicitud explicita del usuario.
