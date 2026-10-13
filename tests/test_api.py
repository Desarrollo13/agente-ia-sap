import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


def test_consultar_chat_devuelve_respuesta_y_herramientas(monkeypatch):
    monkeypatch.setattr(
        api,
        "procesar_pregunta",
        lambda pregunta: {
            "respuesta": f"Respuesta para: {pregunta}",
            "herramientas_usadas": ["consultar_stock"],
            "resultados": [],
        },
    )
    cliente = TestClient(api.app)

    respuesta = cliente.post("/api/chat", json={"pregunta": "Stock de MAT-003"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "respuesta": "Respuesta para: Stock de MAT-003",
        "herramientas_usadas": ["consultar_stock"],
    }


def test_consultar_chat_rechaza_pregunta_vacia():
    cliente = TestClient(api.app)

    respuesta = cliente.post("/api/chat", json={"pregunta": ""})

    assert respuesta.status_code == 422


def test_api_permite_el_origen_del_frontend():
    cliente = TestClient(api.app)

    respuesta = cliente.options(
        "/api/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == "http://localhost:5173"
