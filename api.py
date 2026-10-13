from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

from main import procesar_pregunta
from tools import (
    ErrorConsultaBaseDatos,
    analizar_ordenes,
    analizar_prioridad_ordenes_esperando_material,
    buscar_materiales_sin_stock,
)


app = FastAPI(title="Agente IA SAP", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class MensajeHistorial(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ConsultaChat(BaseModel):
    pregunta: str = Field(min_length=1, max_length=1000)
    historial: list[MensajeHistorial] = Field(default_factory=list, max_length=10)


class RespuestaChat(BaseModel):
    respuesta: str
    herramientas_usadas: list[str]


class ResumenOperativo(BaseModel):
    total_ordenes: int
    en_espera_material: int
    materiales_sin_stock: int
    orden_mayor_prioridad: str | None


@app.post("/api/chat", response_model=RespuestaChat)
def consultar_chat(consulta: ConsultaChat):
    resultado = procesar_pregunta(
        consulta.pregunta,
        [mensaje.model_dump() for mensaje in consulta.historial],
    )
    return {
        "respuesta": resultado["respuesta"],
        "herramientas_usadas": resultado["herramientas_usadas"],
    }


@app.get("/api/resumen", response_model=ResumenOperativo)
def consultar_resumen():
    try:
        ordenes = analizar_ordenes()
        materiales_sin_stock = buscar_materiales_sin_stock()
        orden_prioritaria = analizar_prioridad_ordenes_esperando_material("mayor")
    except ErrorConsultaBaseDatos as error:
        raise HTTPException(
            status_code=503,
            detail="No se pudo consultar la base de datos.",
        ) from error

    return {
        "total_ordenes": ordenes["total_ordenes"],
        "en_espera_material": ordenes["en_espera_material"],
        "materiales_sin_stock": len(materiales_sin_stock),
        "orden_mayor_prioridad": (
            orden_prioritaria["numero_orden"] if orden_prioritaria else None
        ),
    }
