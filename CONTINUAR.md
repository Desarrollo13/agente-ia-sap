# Punto De Continuidad

Fecha: 2026-10-15

## Estado Actual

- La aplicacion es una demo de mantenimiento SAP con React, FastAPI, MySQL y
  Ollama (`qwen2.5:3b`). MySQL simula SAP; no hay integracion SAP real.
- La rama `main` esta publicada hasta `20b030a Agrega gestion administrativa de
  cuentas`.
- API y frontend se inician con `iniciar_desarrollo.bat`.
- La funcionalidad actual incluye autenticacion, roles, rate limit, historial
  de conversaciones, auditoria y gestion de cuentas para administradores.
- La documentacion completa esta en `DOCUMENTACION.md`.

## Base De Datos Local

- Estan aplicadas las migraciones `001_agrega_cuentas.sql`,
  `002_agrega_roles_y_auditoria.sql` y `003_refuerza_seguridad.sql`.
- La cuenta `admin` tiene rol `administrador`.
- No pedir, guardar ni incluir la contrasena de `admin` en archivos, Git o chat.
- Las tablas de aplicacion son `cuentas`, `sesiones`, `conversaciones`,
  `mensajes_conversacion`, `auditoria` e `intentos_login`.

## Reglas De Producto

- Mantener la simulacion MySQL; no conectar SAP real sin una decision explicita.
- Operadores pueden consultar y acceder solo a sus propias conversaciones.
- Administradores pueden revisar auditoria y gestionar cuentas.
- No incorporar borrado de conversaciones ni gestion de contrasenas desde la
  interfaz sin definir primero sus reglas de seguridad.

## Ultima Verificacion

- `50 passed` con `./venv/Scripts/python.exe -m pytest -q`.
- `npm.cmd run build` finalizo correctamente dentro de `frontend/`.

## Antes De Continuar

1. Revisar `git status`, `git diff` y `git log --oneline -10`.
2. Ejecutar las pruebas y el build despues de cualquier cambio.
3. No hacer commit ni push sin solicitud explicita del usuario.
