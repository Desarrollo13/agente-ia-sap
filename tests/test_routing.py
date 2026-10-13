import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routing import detectar_consulta_compuesta


def test_detectar_total_y_ordenes_con_material_sin_stock():
    pregunta = "Cuantas ordenes hay y que ordenes tienen materiales sin stock?"

    assert detectar_consulta_compuesta(pregunta) == "total_sin_stock"


def test_detectar_ordenes_esperando_material_y_mayor_prioridad():
    pregunta = "Que ordenes esperando material tienen mayor prioridad?"

    assert detectar_consulta_compuesta(pregunta) == "esperando_material_prioridad"


def test_detectar_ordenes_esperando_material_y_menor_prioridad():
    pregunta = "Que ordenes esperando material tienen la prioridad mas baja?"

    assert (
        detectar_consulta_compuesta(pregunta)
        == "esperando_material_prioridad_menor"
    )


def test_no_detectar_consulta_compuesta_cuando_falta_una_necesidad():
    assert detectar_consulta_compuesta("Cual es la mayor prioridad?") is None
