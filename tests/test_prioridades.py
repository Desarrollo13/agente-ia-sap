
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import analizar_prioridad_ordenes_esperando_material

def test_orden_mayor_prioridad():
    resultado = analizar_prioridad_ordenes_esperando_material("mayor")

    assert resultado["numero_orden"] == "45001234"
    assert resultado["prioridad"] == "Alta"


def test_orden_menor_prioridad():
    resultado = analizar_prioridad_ordenes_esperando_material("menor")

    assert resultado["numero_orden"] == "45001237"
    assert resultado["prioridad"] == "Media"


if __name__ == "__main__":
    test_orden_mayor_prioridad()
    test_orden_menor_prioridad()

    print("Todas las pruebas de prioridades pasaron correctamente.")