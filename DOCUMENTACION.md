# Documentacion Del Proyecto

## Proposito

Agente IA SAP es una demo de un asistente para mantenimiento de planta. Permite
consultar ordenes, materiales, stock y prioridades mediante lenguaje natural.
La fuente de datos es una base MySQL local que simula informacion SAP; no existe
conexion con un servidor SAP real.

El proyecto sirve para demostrar una aplicacion completa: interfaz web, API,
autenticacion, autorizacion por roles, persistencia de conversaciones,
auditoria y uso de un modelo local de IA.

## Recorrido Del Proyecto

El desarrollo avanzo desde un agente de consola hasta una demo web administrable:

1. Se creo el agente Python con consultas deterministas a ordenes, usuarios y
   materiales.
2. Se incorporo MySQL reproducible mediante el esquema y los datos de ejemplo.
3. Se expuso el agente con FastAPI y luego se agrego la interfaz React.
4. Se sumaron indicadores operativos y comprobacion de MySQL y Ollama.
5. Se incorporaron cuentas, sesiones Bearer, seguridad de contrasenas y roles.
6. Se persistieron las conversaciones y se hizo visible su historial en la web.
7. Se agrego auditoria para administradores.
8. Se incorporo la gestion de cuentas desde la interfaz administrativa.

Los commits principales estan disponibles en la rama `main`. El estado actual
incluye los commits `8e6963e`, `4779e6e` y `20b030a` para historial, auditoria
y gestion de cuentas respectivamente.

## Arquitectura

```text
Navegador (React + Vite)
        |
        | HTTP con Bearer token
        v
FastAPI (api.py)
        |-------------------> Ollama / qwen2.5:3b
        |                         interpreta la pregunta y solicita herramientas
        v
tools.py
        v
MySQL
  Datos SAP simulados: ordenes, usuarios, materiales, orden_materiales
  Aplicacion: cuentas, sesiones, conversaciones, mensajes_conversacion,
              auditoria, intentos_login
```

- `main.py`: orquesta el agente, define las herramientas disponibles para
  Ollama y despacha las consultas a `tools.py`.
- `api.py`: implementa la API REST, autenticacion, autorizacion y contratos
  HTTP.
- `tools.py`: concentra las consultas MySQL, la persistencia y las
  transacciones.
- `seguridad.py`: cifra y verifica contrasenas, genera tokens y valida datos.
- `frontend/`: contiene la interfaz React.
- `database/`: contiene el esquema, datos de ejemplo y migraciones.

## Datos De La Demo

La base incluye cuatro ordenes, tres usuarios y tres materiales de ejemplo.
Una orden puede requerir uno o mas materiales mediante `orden_materiales`.
Esto permite consultas como:

- Estado de la orden `45001234`.
- Stock de `MAT-003`.
- Materiales sin stock.
- Ordenes detenidas por materiales sin stock.
- Ordenes con mayor o menor prioridad.

La separacion entre "materiales sin stock" y "ordenes que requieren un
material sin stock" es intencional y se conserva en las herramientas del
agente.

## Flujo De Una Consulta

1. El usuario inicia sesion y React guarda localmente solo la sesion y el ID de
   su conversacion activa.
2. React envia la pregunta a `POST /api/chat` con el token Bearer.
3. FastAPI valida la sesion en MySQL.
4. Para una conversacion existente, se leen los ultimos 10 mensajes como
   contexto del modelo. Este limite evita enviar un historial ilimitado a
   Ollama.
5. `main.py` entrega la pregunta y el contexto a Ollama. El modelo puede pedir
   herramientas, que consultan MySQL desde `tools.py`.
6. La respuesta se devuelve al navegador.
7. La pregunta y la respuesta se guardan juntas en una transaccion, se
   actualiza la conversacion y se registra el evento de auditoria.

La interfaz invalida una apertura anterior al elegir otra conversacion y
cancela el chat pendiente al cambiar de conversacion, crear una nueva o cerrar
sesion. Las consultas de chat que superan 60 segundos muestran un error
recuperable para poder reintentarlas.

El historial visual no depende de `localStorage`: al abrir una conversacion,
React solicita hasta 100 mensajes a MySQL con rol, contenido y fecha.

## Autenticacion Y Seguridad

No existe registro publico. La primera cuenta se crea con `crear_cuenta.py` y
las cuentas posteriores se pueden crear desde la interfaz de administrador.

- Las contrasenas se cifran con `scrypt` y una sal aleatoria.
- Las contrasenas deben tener al menos 10 caracteres.
- Los nombres de usuario solo admiten letras, numeros, puntos, guiones y
  guiones bajos.
- Los tokens se generan de forma segura, pero en MySQL solo se guarda su hash
  SHA-256.
- Las sesiones vencen a las ocho horas y el cierre de sesion las revoca.
- Cinco intentos fallidos para la misma combinacion de usuario e IP bloquean el
  inicio durante quince minutos.
- Las contrasenas y tokens nunca se devuelven desde la API, ni se guardan en el
  historial, Git o la documentacion.

## Roles Y Permisos

| Funcion | Operador | Administrador |
| --- | --- | --- |
| Iniciar y cerrar sesion | Si | Si |
| Consultar chat y resumen operativo | Si | Si |
| Ver y continuar sus conversaciones | Si | Si |
| Ver estado de MySQL y Ollama | Si | Si |
| Consultar auditoria | No | Si |
| Listar cuentas | No | Si |
| Crear operadores o administradores | No | Si |
| Cambiar el rol de otra cuenta | No | Si |

Los permisos se verifican en FastAPI, no solamente ocultando botones en React.
Un administrador no puede cambiar su propio rol desde la API ni la interfaz.

## Flujos De Uso

### Operador De Demo

1. Un administrador abre `Cuentas`.
2. Crea un usuario con rol `operador` y una contrasena de al menos 10
   caracteres.
3. Comparte esas credenciales con el tecnico.
4. El tecnico inicia sesion y puede realizar consultas operativas y continuar
   sus propias conversaciones.
5. El tecnico no puede ver la auditoria ni administrar cuentas.

### Administrador

1. Inicia sesion con una cuenta administradora.
2. Desde `Cuentas`, crea usuarios y asigna los roles `operador` o
   `administrador`.
3. Puede cambiar el rol de otras cuentas. Las altas y cambios se guardan en
   auditoria.
4. Desde `Auditoria`, revisa los 100 eventos mas recientes: usuario, fecha,
   evento y detalle.

### Historial De Conversaciones

1. Despues del inicio de sesion, la barra lateral carga las conversaciones del
   usuario ordenadas por actualizacion.
2. Al seleccionar una, se solicitan sus mensajes a MySQL en orden cronologico.
3. Al continuar una conversacion, su contexto reciente se usa para responder y
   la conversacion vuelve a actualizarse.
4. `Nueva conversacion` solo elimina el ID activo local; crea el registro en
   MySQL al enviar la primera pregunta.

## API Principal

Todos los endpoints excepto `POST /api/login` requieren `Authorization: Bearer
<token>`.

| Metodo y ruta | Rol | Proposito |
| --- | --- | --- |
| `POST /api/login` | Publico | Crea una sesion de ocho horas. |
| `POST /api/logout` | Autenticado | Revoca la sesion. |
| `POST /api/chat` | Autenticado | Consulta el agente y persiste el intercambio. |
| `GET /api/resumen` | Autenticado | Devuelve indicadores operativos. |
| `GET /api/estado` | Autenticado | Comprueba MySQL y Ollama. |
| `GET /api/conversaciones` | Autenticado | Lista las conversaciones propias. |
| `GET /api/conversaciones/{id}` | Autenticado | Devuelve mensajes de una conversacion propia. |
| `GET /api/auditoria` | Administrador | Lista eventos recientes. |
| `GET /api/cuentas` | Administrador | Lista usuarios y roles. |
| `POST /api/cuentas` | Administrador | Crea una cuenta. |
| `PATCH /api/cuentas/{usuario}` | Administrador | Cambia el rol de otra cuenta. |

La documentacion interactiva de FastAPI esta disponible en
`http://127.0.0.1:8000/docs` durante el desarrollo.

## Instalacion Y Ejecucion

1. Copiar `.env.example` a `.env` y completar las credenciales MySQL.
2. Crear la base de datos y ejecutar `database/schema.sql` y
   `database/seed.sql`.
3. Ejecutar en orden las migraciones `001_agrega_cuentas.sql`,
   `002_agrega_roles_y_auditoria.sql` y `003_refuerza_seguridad.sql`.
4. Crear la primera cuenta con:

```powershell
.\venv\Scripts\python.exe crear_cuenta.py admin
```

5. Instalar `qwen2.5:3b` con `ollama pull qwen2.5:3b`.
6. Iniciar API y frontend desde la raiz:

```powershell
.\iniciar_desarrollo.bat
```

Abrir la URL que muestre Vite, normalmente `http://127.0.0.1:5173`.

## Calidad Y Limites

- La suite se ejecuta con `./venv/Scripts/python.exe -m pytest -q` y usa la
  base MySQL local configurada en `.env`.
- Las pruebas de interfaz se ejecutan con `npm.cmd test` dentro de `frontend/`
  y simulan las respuestas HTTP de la API.
- El frontend se valida con `npm.cmd run build` dentro de `frontend/`.
- El proyecto usa datos simulados y Ollama local. No debe presentarse como una
  integracion con SAP productivo.
- No hay borrado de conversaciones ni administracion de contrasenas desde la
  interfaz por el momento.
