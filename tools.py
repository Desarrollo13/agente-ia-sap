from database import obtener_conexion
from mysql.connector import Error as MySQLError


class ErrorConsultaBaseDatos(Exception):
    pass


def _ejecutar_consulta(consulta, parametros=(), una_fila=False):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(consulta, parametros)
        return cursor.fetchone() if una_fila else cursor.fetchall()
    except MySQLError as error:
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


def consultar_orden(numero_orden):
    resultado = _ejecutar_consulta(
        """
        SELECT numero_orden, estado, prioridad, descripcion
        FROM ordenes
        WHERE numero_orden = %s
        """,
        (numero_orden,),
        una_fila=True,
    )
    return resultado or "No se encontro la orden."


def consultar_usuario(legajo):
    resultado = _ejecutar_consulta(
        """
        SELECT legajo, nombre, sector, estado
        FROM usuarios
        WHERE legajo = %s
        """,
        (legajo,),
        una_fila=True,
    )
    return resultado or "No se encontro el usuario."


def consultar_stock(material):
    resultado = _ejecutar_consulta(
        """
        SELECT material, descripcion, stock, unidad
        FROM materiales
        WHERE material = %s
        """,
        (material,),
        una_fila=True,
    )
    return resultado or "No se encontro el material."


def buscar_ordenes(estado=None, prioridad=None):
    consulta = """
        SELECT numero_orden, estado, prioridad, descripcion
        FROM ordenes
        WHERE 1=1
    """
    parametros = []

    if estado:
        consulta += " AND estado = %s"
        parametros.append(estado)
    if prioridad:
        consulta += " AND prioridad = %s"
        parametros.append(prioridad)

    consulta += " ORDER BY numero_orden"
    return _ejecutar_consulta(consulta, parametros)


def analizar_ordenes():
    resultado = _ejecutar_consulta(
        """
        SELECT
            COUNT(*) AS total_ordenes,
            SUM(estado = 'En espera de material') AS en_espera_material,
            SUM(estado = 'En reparacion') AS en_reparacion,
            SUM(estado = 'Finalizada') AS finalizadas,
            SUM(prioridad = 'Alta') AS prioridad_alta,
            SUM(prioridad = 'Media') AS prioridad_media,
            SUM(prioridad = 'Baja') AS prioridad_baja
        FROM ordenes
        """,
        una_fila=True,
    )
    return {clave: int(valor) for clave, valor in resultado.items()}


def buscar_materiales_sin_stock():
    return _ejecutar_consulta(
        """
        SELECT material, descripcion, stock, unidad
        FROM materiales
        WHERE stock = 0
        ORDER BY material
        """
    )


def buscar_ordenes_con_material_sin_stock():
    return _ejecutar_consulta(
        """
        SELECT
            om.numero_orden, o.estado, o.prioridad,
            o.descripcion AS descripcion_orden, om.material,
            m.descripcion AS descripcion_material, om.cantidad_requerida,
            m.stock, m.unidad
        FROM orden_materiales om
        INNER JOIN ordenes o ON om.numero_orden = o.numero_orden
        INNER JOIN materiales m ON om.material = m.material
        WHERE o.estado = 'En espera de material' AND m.stock = 0
        ORDER BY om.numero_orden, om.material
        """
    )


def analizar_ordenes_esperando_material():
    return _ejecutar_consulta(
        """
        SELECT
            om.numero_orden, o.estado, o.prioridad,
            o.descripcion AS descripcion_orden, om.material,
            m.descripcion AS descripcion_material, om.cantidad_requerida,
            m.stock, m.unidad
        FROM orden_materiales om
        INNER JOIN ordenes o ON om.numero_orden = o.numero_orden
        INNER JOIN materiales m ON om.material = m.material
        WHERE o.estado = 'En espera de material'
        ORDER BY om.numero_orden, om.material
        """
    )


def analizar_prioridad_ordenes_esperando_material(tipo="mayor"):
    ordenes = analizar_ordenes_esperando_material()
    if not ordenes:
        return []

    prioridad_valor = {"Alta": 3, "Media": 2, "Baja": 1}
    seleccion = max if tipo == "mayor" else min
    return seleccion(
        ordenes,
        key=lambda orden: prioridad_valor.get(orden["prioridad"], 0),
    )
