import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import buscar_materiales_sin_stock


def test_buscar_materiales_sin_stock():
    resultado = buscar_materiales_sin_stock()

    assert len(resultado) == 1

    material = resultado[0]

    assert material["material"] == "MAT-003"
    assert material["descripcion"] == "Aceite hidraulico"
    assert material["stock"] == 0
    assert material["unidad"] == "L"