# Agente IA SAP

Demo web de un asistente para mantenimiento de planta. Permite consultar datos
SAP simulados mediante lenguaje natural, analizar el riesgo de equipos y
gestionar alertas operativas. Usa Ollama para interpretar consultas y MySQL
como fuente de datos.

> El proyecto no se conecta a un sistema SAP productivo. MySQL contiene datos
> locales de demostracion.

## Estado Del Proyecto

La aplicacion esta terminada como demo funcional y contiene una interfaz React,
API FastAPI, autenticacion, base de datos y agente de IA local. El flujo
principal se ejecuta en Windows con XAMPP/MySQL y Ollama.

## Funcionalidades

- Chat con Ollama (`qwen2.5:3b`) y herramientas deterministas para consultar
  ordenes, materiales, stock y usuarios.
- Resumen operativo con totales de ordenes, materiales sin stock y prioridad.
- Historial persistente de conversaciones por usuario, con creacion y borrado.
- Cuentas con roles `operador` y `administrador`, sesiones Bearer de ocho horas
  y bloqueo temporal despues de intentos de acceso fallidos.
- Auditoria de acciones administrativas y operativas.
- Historial de equipos SAP PM, avisos de falla y puntaje de riesgo explicable.
- Alertas de mantenimiento para equipos de riesgo alto, con seguimiento hasta
  su atencion.
- Base documental tecnica con busqueda RAG de texto completo y administracion
  de documentos para administradores.
- Interfaz responsive, accesible por teclado y protegida ante respuestas HTTP
  obsoletas o consultas de chat agotadas.

## Tecnologias

- Python 3.12, FastAPI y MySQL.
- React 19, Vite y Vitest.
- Ollama con el modelo local `qwen2.5:3b`.

La guia completa de arquitectura, seguridad, roles y flujos de uso esta en
[`DOCUMENTACION.md`](DOCUMENTACION.md).

## Requisitos

- Python 3.12
- MySQL con las tablas `ordenes`, `usuarios`, `materiales` y `orden_materiales`
- Ollama en ejecucion con el modelo `qwen2.5:3b`

## Configuracion

Copiar `.env.example` como `.env` y completar las credenciales de MySQL:

```env
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_contrasena
DB_NAME=tu_base_de_datos
```

Instalar las dependencias en un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

Descargar el modelo de Ollama si fuera necesario:

```powershell
ollama pull qwen2.5:3b
```

## Base de datos

Crear una base vacia con el mismo nombre configurado en `DB_NAME` y ejecutar los
scripts incluidos:

```powershell
mysql -u root -p -e "CREATE DATABASE agente_ia_sap CHARACTER SET utf8mb4"
mysql -u root -p agente_ia_sap < database/schema.sql
mysql -u root -p agente_ia_sap < database/seed.sql
```

`schema.sql` crea las tablas si no existen y `seed.sql` inserta los datos de
ejemplo sin duplicarlos. Ajustar `agente_ia_sap` en los comandos si `DB_NAME`
tiene otro valor.

Para habilitar las funciones de acceso, equipos, alertas y RAG, ejecutar las
migraciones en orden. En PowerShell:

```powershell
Get-ChildItem database\migrations\*.sql | Sort-Object Name | ForEach-Object {
    Get-Content $_ | mysql -u root -p agente_ia_sap
}
```

Luego crear la cuenta inicial:

```powershell
.\venv\Scripts\python.exe crear_cuenta.py admin
```

## Uso

La interfaz principal es el frontend React. Para iniciar API y frontend en dos
terminales separadas, ejecutar desde la raiz del proyecto:

```powershell
.\iniciar_desarrollo.bat
```

Abrir la URL de Vite que aparece en la terminal del frontend, normalmente
`http://127.0.0.1:5173`.

La CLI se conserva como herramienta de desarrollo y diagnostico:

```powershell
.\venv\Scripts\python.exe main.py
```

Ejemplos de preguntas:

- `Consulta la orden 45001234`
- `Cual es el stock de MAT-003?`
- `Que materiales estan sin stock?`
- `Cuantas ordenes hay y que ordenes tienen materiales sin stock?`
- `Que ordenes esperando material tienen la prioridad mas baja?`

## API REST

Iniciar la API local:

```powershell
.\venv\Scripts\uvicorn.exe api:app --reload
```

La documentacion interactiva queda disponible en `http://127.0.0.1:8000/docs`.
Primero iniciar sesion en `POST /api/login`; los endpoints de chat, resumen y
estado requieren el token devuelto como `Authorization: Bearer <token>`. Las
sesiones vencen a las ocho horas y `POST /api/logout` las revoca.

Las cuentas tienen los roles `operador` y `administrador`. La cuenta inicial
`admin` queda como administradora; `GET /api/auditoria` y los endpoints de
cuentas requieren ese rol.

Ejecutar despues `database/migrations/003_refuerza_seguridad.sql`. Esta
migracion agrega el control de intentos de inicio de sesion y los indices usados
por sesiones y conversaciones. Se bloquean cinco intentos fallidos por usuario
y direccion IP durante quince minutos.

```json
{
  "usuario": "admin",
  "contrasena": "tu-contrasena"
}
```

## Frontend web

Con la API iniciada, abrir otra terminal y ejecutar:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Vite mostrara la URL local, normalmente `http://127.0.0.1:5173`. Para generar
los archivos de produccion usar `npm.cmd run build`.

## Pruebas

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan la base MySQL configurada en `.env` y esperan los datos SAP de
ejemplo incluidos en sus aserciones.

Para las pruebas y el build del frontend:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

## Estructura

- `api.py`: API REST, sesiones, permisos y contratos HTTP.
- `main.py`: orquestacion del agente Ollama y sus herramientas.
- `tools.py`: consultas, transacciones y logica de negocio MySQL.
- `frontend/`: interfaz React.
- `database/`: esquema, datos de demostracion y migraciones SQL.
- `tests/`: pruebas de API, seguridad, consultas y reglas operativas.

La arquitectura, endpoints, permisos y limites conocidos se documentan en
[`DOCUMENTACION.md`](DOCUMENTACION.md).
