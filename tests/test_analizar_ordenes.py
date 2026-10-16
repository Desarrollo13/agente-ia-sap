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


def test_analizar_ordenes_devuelve_ceros_si_no_hay_filas(monkeypatch):
    import tools

    monkeypatch.setattr(tools, "_ejecutar_consulta", lambda *_args, **_kwargs: {
        "total_ordenes": 0,
        "en_espera_material": None,
        "en_reparacion": None,
        "finalizadas": None,
        "prioridad_alta": None,
        "prioridad_media": None,
        "prioridad_baja": None,
    })

    assert tools.analizar_ordenes()["en_espera_material"] == 0
