from fastapi import FastAPI
from pydantic import BaseModel, Field

from main import procesar_pregunta


app = FastAPI(title="Agente IA SAP", version="1.0.0")


class ConsultaChat(BaseModel):
    pregunta: str = Field(min_length=1, max_length=1000)


class RespuestaChat(BaseModel):
    respuesta: str
    herramientas_usadas: list[str]


@app.post("/api/chat", response_model=RespuestaChat)
def consultar_chat(consulta: ConsultaChat):
    resultado = procesar_pregunta(consulta.pregunta)
    return {
        "respuesta": resultado["respuesta"],
        "herramientas_usadas": resultado["herramientas_usadas"],
    }
