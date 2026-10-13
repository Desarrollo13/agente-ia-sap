import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


def test_consultar_chat_devuelve_respuesta_y_herramientas(monkeypatch):
    historial_recibido = []

    def procesar(pregunta, historial):
        historial_recibido.extend(historial)
        return {
            "respuesta": f"Respuesta para: {pregunta}",
            "herramientas_usadas": ["consultar_stock"],
            "resultados": [],
        }

    monkeypatch.setattr(
        api,
        "procesar_pregunta",
        procesar,
    )
    cliente = TestClient(api.app)

    respuesta = cliente.post("/api/chat", json={"pregunta": "Stock de MAT-003"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "respuesta": "Respuesta para: Stock de MAT-003",
        "herramientas_usadas": ["consultar_stock"],
    }
    assert historial_recibido == []


def test_consultar_chat_envia_el_historial_al_agente(monkeypatch):
    historial_recibido = []

    def procesar(_pregunta, historial):
        historial_recibido.extend(historial)
        return {"respuesta": "Correcto.", "herramientas_usadas": [], "resultados": []}

    monkeypatch.setattr(api, "procesar_pregunta", procesar)
    cliente = TestClient(api.app)

    respuesta = cliente.post("/api/chat", json={
        "pregunta": "Y cual es su prioridad?",
        "historial": [{"role": "user", "content": "Consulta la orden 45001234"}],
    })

    assert respuesta.status_code == 200
    assert historial_recibido == [
        {"role": "user", "content": "Consulta la orden 45001234"}
    ]


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


def test_consultar_resumen_devuelve_indicadores(monkeypatch):
    monkeypatch.setattr(api, "analizar_ordenes", lambda: {
        "total_ordenes": 4,
        "en_espera_material": 2,
    })
    monkeypatch.setattr(api, "buscar_materiales_sin_stock", lambda: [{"material": "MAT-003"}])
    monkeypatch.setattr(
        api,
        "analizar_prioridad_ordenes_esperando_material",
        lambda _tipo: {"numero_orden": "45001234"},
    )
    cliente = TestClient(api.app)

    respuesta = cliente.get("/api/resumen")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "total_ordenes": 4,
        "en_espera_material": 2,
        "materiales_sin_stock": 1,
        "orden_mayor_prioridad": "45001234",
    }


def test_consultar_estado_verifica_base_y_modelo(monkeypatch):
    class RespuestaModelos:
        models = [type("Modelo", (), {"model": "qwen2.5:3b"})()]

    monkeypatch.setattr(api, "analizar_ordenes", lambda: {})
    monkeypatch.setattr(api, "listar_modelos", lambda: RespuestaModelos())
    cliente = TestClient(api.app)

    respuesta = cliente.get("/api/estado")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "disponible": True,
        "base_datos": True,
        "ollama": True,
    }
