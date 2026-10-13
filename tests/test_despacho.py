import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main


def test_ejecutar_herramienta_despacha_la_consulta(monkeypatch):
    monkeypatch.setattr(main, "consultar_stock", lambda material: {"material": material})

    resultado = main.ejecutar_herramienta(
        "consultar_stock", {"material": "MAT-003"}
    )

    assert resultado == {"material": "MAT-003"}


def test_ejecutar_herramienta_informa_argumento_faltante():
    resultado = main.ejecutar_herramienta("consultar_orden", {})

    assert resultado == "Falta el argumento obligatorio: numero_orden."


def test_consulta_compuesta_menor_prioridad_usa_el_tipo_correcto(monkeypatch):
    tipos_recibidos = []
    monkeypatch.setattr(main, "analizar_ordenes_esperando_material", lambda: [])
    monkeypatch.setattr(
        main,
        "analizar_prioridad_ordenes_esperando_material",
        lambda tipo: tipos_recibidos.append(tipo) or {},
    )

    resultados, instruccion = main.ejecutar_consulta_compuesta(
        "esperando_material_prioridad_menor"
    )

    assert tipos_recibidos == ["menor"]
    assert len(resultados) == 2
    assert "menor prioridad" in instruccion
