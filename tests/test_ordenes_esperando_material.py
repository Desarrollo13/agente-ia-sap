import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from tools import analizar_ordenes_esperando_material


def test_ordenes_esperando_material():
    resultado = analizar_ordenes_esperando_material()

    assert len(resultado) == 2

    ordenes = {
        orden["numero_orden"]: orden
        for orden in resultado
    }

    assert "45001234" in ordenes
    assert "45001237" in ordenes

    assert ordenes["45001234"]["prioridad"] == "Alta"
    assert ordenes["45001234"]["stock"] == 0
    assert ordenes["45001234"]["unidad"] == "L"

    assert ordenes["45001237"]["prioridad"] == "Media"
    assert ordenes["45001237"]["stock"] == 12
    assert ordenes["45001237"]["unidad"] == "UN"