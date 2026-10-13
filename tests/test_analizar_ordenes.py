import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import analizar_ordenes


def test_analizar_ordenes():
    resultado = analizar_ordenes()

    assert resultado["total_ordenes"] == 4
    assert resultado["en_espera_material"] == 2
    assert resultado["en_reparacion"] == 1
    assert resultado["finalizadas"] == 1


def test_analizar_prioridades():
    resultado = analizar_ordenes()

    assert resultado["prioridad_alta"] == 1
    assert resultado["prioridad_media"] == 2
    assert resultado["prioridad_baja"] == 1