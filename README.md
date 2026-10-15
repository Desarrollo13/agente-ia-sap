# Agente IA SAP

Agente conversacional en Python para consultar ordenes de mantenimiento SAP,
usuarios, materiales y stock mediante lenguaje natural. Usa Ollama para
interpretar preguntas y MySQL como fuente de datos.

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

Para habilitar el acceso, ejecutar tambien `database/migrations/001_agrega_cuentas.sql`. La migracion crea las cuentas, sesiones y conversaciones. Luego crear la cuenta inicial:

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

Las cuentas tienen los roles `operador`, `supervisor` y `administrador`. Ejecutar
tambien `database/migrations/002_agrega_roles_y_auditoria.sql` para habilitar
los roles y el registro de accesos y consultas. La cuenta inicial `admin` queda
como administradora; `GET /api/auditoria` requiere ese rol.

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
