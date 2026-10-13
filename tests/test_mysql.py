import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import obtener_conexion


def test_conexion_mysql():
    conexion = obtener_conexion()

    assert conexion.is_connected()

    conexion.close()


def test_consultar_orden_mysql():
    conexion = obtener_conexion()

    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT numero_orden, estado, prioridad, descripcion
        FROM ordenes
        WHERE numero_orden = %s
    """, ("45001234",))

    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()

    assert resultado is not None
    assert resultado["numero_orden"] == "45001234"
    assert resultado["estado"] == "En espera de material"
    assert resultado["prioridad"] == "Alta"