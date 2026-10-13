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

## Uso

```powershell
.\venv\Scripts\python.exe main.py
```

Ejemplos de preguntas:

- `Consulta la orden 45001234`
- `Cual es el stock de MAT-003?`
- `Que materiales estan sin stock?`
- `Cuantas ordenes hay y que ordenes tienen materiales sin stock?`
- `Que ordenes esperando material tienen la prioridad mas baja?`

## Pruebas

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan la base MySQL configurada en `.env` y esperan los datos SAP de
ejemplo incluidos en sus aserciones.
