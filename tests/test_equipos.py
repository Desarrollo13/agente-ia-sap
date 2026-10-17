import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main
import tools


def test_consultar_historial_equipo_reune_equipo_avisos_y_ordenes(monkeypatch):
    respuestas = [
        {
            "equipo": "EQ-1001",
            "descripcion": "Bomba centrifuga de proceso",
            "ubicacion_tecnica": "PLANTA-01-BOMBAS-01",
            "criticidad": "Alta",
        },
        [{"numero_aviso": "80000001", "sintoma": "Vibracion"}],
        [{"numero_orden": "45001234", "prioridad": "Alta"}],
    ]
    monkeypatch.setattr(tools, "_ejecutar_consulta", lambda *_args, **_kwargs: respuestas.pop(0))

    historial = tools.consultar_historial_equipo("EQ-1001")

    assert historial["equipo"] == "EQ-1001"
    assert historial["avisos"][0]["numero_aviso"] == "80000001"
    assert historial["ordenes"][0]["numero_orden"] == "45001234"


def test_consultar_historial_equipo_inexistente(monkeypatch):
    monkeypatch.setattr(tools, "_ejecutar_consulta", lambda *_args, **_kwargs: None)

    assert tools.consultar_historial_equipo("EQ-9999") == "No se encontro el equipo."


def test_herramienta_historial_equipo_redacta_avisos(monkeypatch):
    monkeypatch.setattr(main, "consultar_historial_equipo", lambda _equipo: {
        "equipo": "EQ-1001",
        "descripcion": "Bomba",
        "ubicacion_tecnica": "PLANTA-01",
        "criticidad": "Alta",
        "avisos": [{"numero_aviso": "80000001", "fecha_aviso": "2026-09-12", "sintoma": "Vibracion", "modo_falla": "Rodamiento"}],
        "ordenes": [],
    })

    resultado = main.ejecutar_herramienta("consultar_historial_equipo", {"equipo": "EQ-1001"})
    respuesta = main.redactar_resultado_herramienta("consultar_historial_equipo", resultado)

    assert "80000001" in respuesta
    assert "Rodamiento" in respuesta


def test_analizar_riesgo_equipo_explica_los_factores(monkeypatch):
    monkeypatch.setattr(tools, "consultar_historial_equipo", lambda _equipo: {
        "equipo": "EQ-1001",
        "criticidad": "Alta",
        "avisos": [
            {"estado": "Abierto", "modo_falla": "Rodamiento"},
            {"estado": "Cerrado", "modo_falla": "Rodamiento"},
        ],
        "ordenes": [{"estado": "En reparacion", "prioridad": "Alta"}],
    })

    riesgo = tools.analizar_riesgo_equipo("EQ-1001")

    assert riesgo["puntaje"] == 85
    assert riesgo["nivel"] == "Alto"
    assert any("aviso" in razon for razon in riesgo["razones"])
    assert any("repetido" in razon for razon in riesgo["razones"])


def test_buscar_procedimientos_recupera_fuente_relevante(monkeypatch):
    consultas = []

    def consultar(consulta, parametros=(), **_kwargs):
        consultas.append((consulta, parametros))
        return [
            {"id": 1, "titulo": "Revision de bomba", "fuente": "Manual BOM-01", "contenido": "Verificar vibracion y sello mecanico."},
            {"id": 2, "titulo": "Motor", "fuente": "Manual MOT-01", "contenido": "Verificar ventilacion."},
        ]

    monkeypatch.setattr(tools, "_ejecutar_consulta", consultar)

    documentos = tools.buscar_procedimientos("vibracion de bomba")

    assert "MATCH(titulo, contenido) AGAINST" in consultas[0][0]
    assert consultas[0][1] == ("bomba* vibracion*", "bomba* vibracion*", 3)
    assert len(documentos) == 1
    assert documentos[0]["fuente"] == "Manual BOM-01"
    assert documentos[0]["relevancia"] == 2


def test_migraciones_de_equipos_y_documentos_son_repetibles():
    migracion_equipos = Path("database/migrations/004_agrega_equipos_y_avisos.sql").read_text(encoding="utf-8")
    migracion_documentos = Path("database/migrations/007_indice_busqueda_documentos.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS avisos_falla" in migracion_equipos
    assert "fk_ordenes_equipos FOREIGN KEY (equipo) REFERENCES equipos (equipo)" in migracion_equipos
    assert "idx_documentos_tecnicos_busqueda" in migracion_documentos
    assert "FULLTEXT INDEX" in migracion_documentos
