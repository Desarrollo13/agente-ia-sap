# Agente IA SAP

Agente conversacional en Python para consultar ordenes de mantenimiento SAP,
usuarios, materiales y stock mediante lenguaje natural. Usa Ollama para
interpretar preguntas y MySQL como fuente de datos.

## Requisitos

- Python 3.12
- MySQL con las tablas `ordenes`, `usuarios`, `materiales` y `orden_materiales`
- Ollama en ejecucion con el modelo `qwen2.5:3b`

## Configuracion

Crear un archivo `.env` en la raiz del proyecto:

```env
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_contrasena
DB_NAME=tu_base_de_datos
```

Instalar las dependencias en un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\pip.exe install ollama mysql-connector-python python-dotenv pytest
```

Descargar el modelo de Ollama si fuera necesario:

```powershell
ollama pull qwen2.5:3b
```

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
