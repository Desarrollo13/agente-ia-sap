from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from ollama import list as listar_modelos
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

from main import procesar_pregunta
from tools import (
    ErrorConsultaBaseDatos,
    analizar_ordenes,
    analizar_prioridad_ordenes_esperando_material,
    buscar_materiales_sin_stock,
    consultar_historial_equipo,
    analizar_riesgo_equipo,
    crear_alerta_riesgo_alto,
    listar_alertas,
    atender_alerta,
    buscar_procedimientos,
    listar_documentos_tecnicos,
    crear_documento_tecnico,
    autenticar_cuenta,
    crear_conversacion,
    eliminar_conversacion,
    crear_sesion,
    eliminar_sesion,
    guardar_interaccion_chat,
    listar_conversaciones,
    obtener_historial_conversacion,
    obtener_mensajes_conversacion,
    obtener_rol_cuenta,
    obtener_usuario_por_sesion,
    listar_cuentas,
    crear_cuenta_administrada,
    actualizar_rol_cuenta,
    restablecer_contrasena_cuenta,
    registrar_evento,
    listar_auditoria,
    contar_intentos_login,
    registrar_intento_login,
    intentar_inicio_sesion,
)
from seguridad import cifrar_contrasena, generar_token, resumir_token, validar_contrasena, validar_usuario


app = FastAPI(title="Agente IA SAP", version="1.0.0")
MAXIMO_RESPUESTA_CHAT_BYTES = 60000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
esquema_bearer = HTTPBearer(auto_error=False)


class MensajeHistorial(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ConsultaChat(BaseModel):
    pregunta: str = Field(min_length=1, max_length=1000)
    conversacion_id: int | None = Field(default=None, gt=0)


class RespuestaChat(BaseModel):
    respuesta: str
    herramientas_usadas: list[str]
    conversacion_id: int


class Credenciales(BaseModel):
    usuario: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    contrasena: str = Field(min_length=1, max_length=200)


class Sesion(BaseModel):
    token: str
    usuario: str
    rol: str


class Conversacion(BaseModel):
    id: int
    titulo: str
    actualizado_en: datetime


class MensajeConversacion(BaseModel):
    rol: Literal["user", "assistant"]
    contenido: str
    creado_en: datetime


class HistorialConversacion(BaseModel):
    id: int
    mensajes: list[MensajeConversacion]


class HistorialEquipo(BaseModel):
    equipo: str
    descripcion: str
    ubicacion_tecnica: str
    criticidad: Literal["Alta", "Media", "Baja"]
    avisos: list[dict]
    ordenes: list[dict]


class RiesgoEquipo(BaseModel):
    equipo: str
    puntaje: int
    nivel: Literal["Alto", "Medio", "Bajo"]
    razones: list[str]


class AlertaMantenimiento(BaseModel):
    id: int
    equipo: str
    descripcion_equipo: str
    nivel: Literal["Alto"]
    puntaje: int
    detalle: str
    estado: Literal["Pendiente", "Atendida"]
    creada_por: str
    creada_en: datetime
    atendida_por: str | None
    atendida_en: datetime | None


class DocumentoTecnico(BaseModel):
    id: int
    titulo: str
    fuente: str
    contenido: str
    relevancia: int


class DocumentoTecnicoAdministrado(BaseModel):
    id: int
    titulo: str
    fuente: str
    contenido: str
    creado_en: datetime


class NuevoDocumentoTecnico(BaseModel):
    titulo: str = Field(min_length=3, max_length=255)
    fuente: str = Field(min_length=3, max_length=255)
    contenido: str = Field(min_length=20, max_length=10000)


class EventoAuditoria(BaseModel):
    usuario: str
    evento: str
    detalle: str | None
    creado_en: datetime


class Cuenta(BaseModel):
    usuario: str
    rol: Literal["operador", "administrador"]
    creado_en: datetime


class NuevaCuenta(BaseModel):
    usuario: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    contrasena: str = Field(min_length=1, max_length=200)
    rol: Literal["operador", "administrador"] = "operador"


class CambioRol(BaseModel):
    rol: Literal["operador", "administrador"]


class NuevaContrasena(BaseModel):
    contrasena: str = Field(min_length=1, max_length=200)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
):
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado.")
    try:
        usuario = obtener_usuario_por_sesion(resumir_token(credenciales.credentials))
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo validar la sesion.") from error
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion invalida o vencida.")
    return usuario


def requiere_administrador(usuario: str = Depends(obtener_usuario_actual)):
    try:
        rol = obtener_rol_cuenta(usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo verificar el rol.") from error
    if rol != "administrador":
        raise HTTPException(status_code=403, detail="Requiere rol de administrador.")
    return usuario


def registrar_evento_sin_bloquear(usuario, evento, detalle=None):
    try:
        registrar_evento(usuario, evento, detalle)
    except ErrorConsultaBaseDatos:
        pass


class ResumenOperativo(BaseModel):
    total_ordenes: int
    en_espera_material: int
    materiales_sin_stock: int
    orden_mayor_prioridad: str | None


class EstadoServicios(BaseModel):
    disponible: bool
    base_datos: bool
    ollama: bool



@app.post("/api/login", response_model=Sesion)
def iniciar_sesion(credenciales: Credenciales, request: Request):
    direccion_ip = request.client.host if request.client else "desconocida"
    try:
        resultado_login = intentar_inicio_sesion(credenciales.usuario, credenciales.contrasena, direccion_ip)
        if resultado_login is None:
            raise HTTPException(status_code=429, detail="Demasiados intentos. Intenta nuevamente en 15 minutos.")
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo iniciar sesion.") from error
    if not resultado_login:
        raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos.")
    token = generar_token()
    try:
        crear_sesion(credenciales.usuario, resumir_token(token))
        rol = resultado_login
        registrar_evento_sin_bloquear(credenciales.usuario, "inicio_sesion")
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo iniciar sesion.") from error
    return {"token": token, "usuario": credenciales.usuario, "rol": rol}


@app.post("/api/logout", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion(usuario: str = Depends(obtener_usuario_actual), credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer)):
    eliminar_sesion(resumir_token(credenciales.credentials))
    registrar_evento_sin_bloquear(usuario, "cierre_sesion")


@app.get("/api/conversaciones", response_model=list[Conversacion])
def consultar_conversaciones(usuario: str = Depends(obtener_usuario_actual)):
    try:
        return listar_conversaciones(usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudieron consultar las conversaciones.") from error


@app.get("/api/conversaciones/{conversacion_id}", response_model=HistorialConversacion)
def consultar_conversacion(conversacion_id: int, usuario: str = Depends(obtener_usuario_actual)):
    try:
        mensajes = obtener_mensajes_conversacion(conversacion_id, usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo consultar la conversacion.") from error
    if mensajes is None:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada.")
    return {"id": conversacion_id, "mensajes": mensajes}


@app.delete("/api/conversaciones/{conversacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_conversacion(conversacion_id: int, usuario: str = Depends(obtener_usuario_actual)):
    try:
        eliminada = eliminar_conversacion(conversacion_id, usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo eliminar la conversacion.") from error
    if not eliminada:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada.")


@app.get("/api/equipos/{equipo}/historial", response_model=HistorialEquipo)
def consultar_historial_tecnico_equipo(equipo: str, _usuario: str = Depends(obtener_usuario_actual)):
    try:
        historial = consultar_historial_equipo(equipo)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo consultar el historial del equipo.") from error
    if isinstance(historial, str):
        raise HTTPException(status_code=404, detail=historial)
    return historial


@app.get("/api/equipos/{equipo}/riesgo", response_model=RiesgoEquipo)
def consultar_riesgo_equipo(equipo: str, _usuario: str = Depends(obtener_usuario_actual)):
    try:
        riesgo = analizar_riesgo_equipo(equipo)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo analizar el riesgo del equipo.") from error
    if isinstance(riesgo, str):
        raise HTTPException(status_code=404, detail=riesgo)
    return riesgo


@app.post("/api/equipos/{equipo}/alertas")
def crear_alerta_equipo(equipo: str, usuario: str = Depends(obtener_usuario_actual)):
    try:
        resultado = crear_alerta_riesgo_alto(equipo, usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo crear la alerta.") from error
    if isinstance(resultado, str):
        raise HTTPException(status_code=404, detail=resultado)
    return resultado


@app.get("/api/alertas", response_model=list[AlertaMantenimiento])
def consultar_alertas(_usuario: str = Depends(obtener_usuario_actual)):
    try:
        return listar_alertas()
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudieron consultar las alertas.") from error


@app.patch("/api/alertas/{alerta_id}", status_code=status.HTTP_204_NO_CONTENT)
def marcar_alerta_atendida(alerta_id: int, usuario: str = Depends(obtener_usuario_actual)):
    try:
        atendida = atender_alerta(alerta_id, usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo actualizar la alerta.") from error
    if atendida is False:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")
    if atendida is None:
        raise HTTPException(status_code=409, detail="La alerta ya fue atendida.")


@app.get("/api/conocimiento/buscar", response_model=list[DocumentoTecnico])
def buscar_conocimiento(q: str = Query(min_length=3, max_length=200), _usuario: str = Depends(obtener_usuario_actual)):
    try:
        return buscar_procedimientos(q)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo consultar el conocimiento tecnico.") from error


@app.get("/api/documentos-tecnicos", response_model=list[DocumentoTecnicoAdministrado])
def consultar_documentos_tecnicos(_usuario: str = Depends(requiere_administrador)):
    try:
        return listar_documentos_tecnicos()
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudieron consultar los documentos tecnicos.") from error


@app.post("/api/documentos-tecnicos", response_model=DocumentoTecnicoAdministrado, status_code=status.HTTP_201_CREATED)
def crear_documento_tecnico_api(documento: NuevoDocumentoTecnico, administrador: str = Depends(requiere_administrador)):
    try:
        documento_id = crear_documento_tecnico(
            documento.titulo, documento.fuente, documento.contenido, administrador
        )
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo crear el documento tecnico.") from error
    if documento_id is None:
        raise HTTPException(status_code=409, detail="Ya existe un documento con ese titulo y fuente.")
    return {
        "id": documento_id,
        "titulo": documento.titulo,
        "fuente": documento.fuente,
        "contenido": documento.contenido,
        "creado_en": datetime.now(),
    }


@app.get("/api/auditoria", response_model=list[EventoAuditoria])
def consultar_auditoria(_usuario: str = Depends(requiere_administrador)):
    try:
        return listar_auditoria()
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo consultar la auditoria.") from error


@app.get("/api/cuentas", response_model=list[Cuenta])
def consultar_cuentas(_usuario: str = Depends(requiere_administrador)):
    try:
        return listar_cuentas()
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudieron consultar las cuentas.") from error


@app.post("/api/cuentas", response_model=Cuenta, status_code=status.HTTP_201_CREATED)
def crear_cuenta(cuenta: NuevaCuenta, administrador: str = Depends(requiere_administrador)):
    error_contrasena = validar_contrasena(cuenta.contrasena)
    if error_contrasena:
        raise HTTPException(status_code=422, detail=error_contrasena)
    try:
        creada = crear_cuenta_administrada(
            cuenta.usuario,
            cifrar_contrasena(cuenta.contrasena),
            cuenta.rol,
            administrador,
        )
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo crear la cuenta.") from error
    if not creada:
        raise HTTPException(status_code=409, detail="El usuario ya existe.")
    return {"usuario": cuenta.usuario, "rol": cuenta.rol, "creado_en": datetime.now()}


@app.patch("/api/cuentas/{usuario}", response_model=Cuenta)
def cambiar_rol_cuenta(usuario: str, cambio: CambioRol, administrador: str = Depends(requiere_administrador)):
    error_usuario = validar_usuario(usuario)
    if error_usuario:
        raise HTTPException(status_code=422, detail=error_usuario)
    if usuario == administrador:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol.")
    try:
        actualizada = actualizar_rol_cuenta(usuario, cambio.rol, administrador)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo actualizar el rol.") from error
    if actualizada is None:
        raise HTTPException(status_code=409, detail="Debe existir al menos un administrador.")
    if not actualizada:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    return {"usuario": usuario, "rol": cambio.rol, "creado_en": datetime.now()}


@app.patch("/api/cuentas/{usuario}/contrasena", status_code=status.HTTP_204_NO_CONTENT)
def restablecer_contrasena(usuario: str, datos: NuevaContrasena, administrador: str = Depends(requiere_administrador)):
    error_usuario = validar_usuario(usuario)
    if error_usuario:
        raise HTTPException(status_code=422, detail=error_usuario)
    if usuario == administrador:
        raise HTTPException(status_code=400, detail="No puedes restablecer tu propia contrasena desde esta pantalla.")
    error_contrasena = validar_contrasena(datos.contrasena)
    if error_contrasena:
        raise HTTPException(status_code=422, detail=error_contrasena)
    try:
        restablecida = restablecer_contrasena_cuenta(
            usuario, cifrar_contrasena(datos.contrasena), administrador
        )
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo restablecer la contrasena.") from error
    if not restablecida:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")


@app.post("/api/chat", response_model=RespuestaChat)
def consultar_chat(consulta: ConsultaChat, usuario: str = Depends(obtener_usuario_actual)):
    try:
        conversacion_id = consulta.conversacion_id or crear_conversacion(usuario)
        historial = obtener_historial_conversacion(conversacion_id, usuario)
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo preparar la conversacion.") from error
    if historial is None:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada.")
    resultado = procesar_pregunta(
        consulta.pregunta,
        historial,
    )
    respuesta_agente = resultado["respuesta"].encode("utf-8")[:MAXIMO_RESPUESTA_CHAT_BYTES].decode("utf-8", "ignore")
    try:
        guardada = guardar_interaccion_chat(
            conversacion_id, usuario, consulta.pregunta, respuesta_agente
        )
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(status_code=503, detail="No se pudo guardar la conversacion.") from error
    if not guardada:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada.")
    return {
        "respuesta": respuesta_agente,
        "herramientas_usadas": resultado["herramientas_usadas"],
        "conversacion_id": conversacion_id,
    }


@app.get("/api/resumen", response_model=ResumenOperativo)
def consultar_resumen(_usuario: str = Depends(obtener_usuario_actual)):
    try:
        ordenes = analizar_ordenes()
        materiales_sin_stock = buscar_materiales_sin_stock()
        orden_prioritaria = analizar_prioridad_ordenes_esperando_material("mayor")
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(
            status_code=503,
            detail="No se pudo consultar la base de datos.",
        ) from error

    registrar_evento_sin_bloquear(_usuario, "consulta_resumen")
    return {
        "total_ordenes": ordenes["total_ordenes"],
        "en_espera_material": ordenes["en_espera_material"],
        "materiales_sin_stock": len(materiales_sin_stock),
        "orden_mayor_prioridad": (
            orden_prioritaria["numero_orden"] if orden_prioritaria else None
        ),
    }


@app.get("/api/estado", response_model=EstadoServicios)
def consultar_estado(_usuario: str = Depends(obtener_usuario_actual)):
    try:
        analizar_ordenes()
        base_datos = True
    except ErrorConsultaBaseDatos:
        base_datos = False

    try:
        modelos = listar_modelos().models
        ollama_disponible = any(modelo.model == "qwen2.5:3b" for modelo in modelos)
    except Exception:
        ollama_disponible = False

    registrar_evento_sin_bloquear(_usuario, "consulta_estado")
    return {
        "disponible": base_datos and ollama_disponible,
        "base_datos": base_datos,
        "ollama": ollama_disponible,
    }
