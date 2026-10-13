import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import buscar_ordenes


def test_buscar_todas_las_ordenes():
    resultado = buscar_ordenes()

    assert len(resultado) == 4


def test_buscar_ordenes_por_estado():
    resultado = buscar_ordenes(estado="En espera de material")

    assert len(resultado) == 2

    numeros = [orden["numero_orden"] for orden in resultado]

    assert "45001234" in numeros
    assert "45001237" in numeros


def test_buscar_ordenes_por_prioridad():
    resultado = buscar_ordenes(prioridad="Alta")

    assert len(resultado) == 1
    assert resultado[0]["numero_orden"] == "45001234"
    assert resultado[0]["prioridad"] == "Alta"