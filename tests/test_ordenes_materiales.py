import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import buscar_ordenes_con_material_sin_stock


def test_buscar_ordenes_con_material_sin_stock():
    resultado = buscar_ordenes_con_material_sin_stock()

    assert len(resultado) == 1

    orden = resultado[0]

    assert orden["numero_orden"] == "45001234"
    assert orden["estado"] == "En espera de material"
    assert orden["prioridad"] == "Alta"
    assert orden["material"] == "MAT-003"
    assert orden["descripcion_material"] == "Aceite hidraulico"
    assert orden["stock"] == 0