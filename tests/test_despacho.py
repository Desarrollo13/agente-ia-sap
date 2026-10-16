import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main
from tools import ErrorConsultaBaseDatos


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

    resultados = main.ejecutar_consulta_compuesta(
        "esperando_material_prioridad_menor"
    )

    assert tipos_recibidos == ["menor"]
    assert len(resultados) == 2


def test_redactar_consulta_compuesta_respeta_las_unidades_y_todas_las_ordenes():
    resultados = [
        ("analizar_ordenes_esperando_material", [
            {
                "numero_orden": "45001234",
                "prioridad": "Alta",
                "descripcion_orden": "Reparacion de bomba",
                "material": "MAT-003",
                "descripcion_material": "Aceite hidraulico",
                "cantidad_requerida": 2,
                "stock": 0,
                "unidad": "L",
            },
            {
                "numero_orden": "45001237",
                "prioridad": "Media",
                "descripcion_orden": "Cambio de rodamiento",
                "material": "MAT-002",
                "descripcion_material": "Rodamiento",
                "cantidad_requerida": 1,
                "stock": 12,
                "unidad": "UN",
            },
        ]),
        ("analizar_prioridad_ordenes_esperando_material", {
            "numero_orden": "45001234", "prioridad": "Alta"
        }),
    ]

    respuesta = main.redactar_consulta_compuesta(
        "esperando_material_prioridad", resultados
    )

    assert "45001234" in respuesta
    assert "45001237" in respuesta
    assert "2 L" in respuesta
    assert "12 UN" in respuesta
    assert "mayor prioridad es 45001234 (Alta)" in respuesta


def test_redactar_consulta_stock_conserva_stock_cero_y_unidad():
    respuesta = main.redactar_consulta_stock(
        {
            "material": "MAT-003",
            "descripcion": "Aceite hidraulico",
            "stock": 0,
            "unidad": "L",
        }
    )

    assert respuesta == (
        "El material MAT-003 (Aceite hidraulico) tiene un stock actual de 0 L."
    )


def test_redactar_materiales_sin_stock_conserva_la_unidad():
    respuesta = main.redactar_resultado_herramienta(
        "buscar_materiales_sin_stock",
        [{"material": "MAT-003", "descripcion": "Aceite hidraulico", "stock": 0, "unidad": "L"}],
    )

    assert respuesta == "- MAT-003 (Aceite hidraulico): stock 0 L."


def test_ejecutar_herramienta_informa_error_de_base_de_datos(monkeypatch):
    def fallar(_material):
        raise ErrorConsultaBaseDatos

    monkeypatch.setattr(main, "consultar_stock", fallar)

    resultado = main.ejecutar_herramienta(
        "consultar_stock", {"material": "MAT-003"}
    )

    assert resultado == "No se pudo consultar la base de datos."


def test_ejecutar_herramienta_rechaza_argumentos_malformados():
    assert main.ejecutar_herramienta("consultar_stock", ["MAT-003"]) == "Los argumentos de la herramienta no son validos."


def test_ejecutar_chat_devuelve_none_si_ollama_falla(monkeypatch):
    def fallar(**_argumentos):
        raise ConnectionError

    monkeypatch.setattr(main, "chat", fallar)

    assert main.ejecutar_chat(model="modelo-prueba", messages=[]) is None
