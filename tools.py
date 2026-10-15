from database import obtener_conexion
from mysql.connector import Error as MySQLError
from seguridad import verificar_contrasena


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


def _ejecutar_modificacion(consulta, parametros=(), devolver_id=False):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros)
        conexion.commit()
        return cursor.lastrowid if devolver_id else cursor.rowcount
    except MySQLError as error:
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


def autenticar_cuenta(usuario, contrasena):
    cuenta = _ejecutar_consulta(
        "SELECT contrasena_cifrada FROM cuentas WHERE usuario = %s",
        (usuario,),
        una_fila=True,
    )
    return cuenta is not None and verificar_contrasena(contrasena, cuenta["contrasena_cifrada"])


def crear_sesion(usuario, token_hash):
    _ejecutar_modificacion(
        """
        INSERT INTO sesiones (token_hash, usuario, vence_en)
        VALUES (%s, %s, DATE_ADD(UTC_TIMESTAMP(), INTERVAL 8 HOUR))
        """,
        (token_hash, usuario),
    )


def obtener_usuario_por_sesion(token_hash):
    sesion = _ejecutar_consulta(
        """
        SELECT usuario FROM sesiones
        WHERE token_hash = %s AND vence_en > UTC_TIMESTAMP()
        """,
        (token_hash,),
        una_fila=True,
    )
    return sesion["usuario"] if sesion else None


def eliminar_sesion(token_hash):
    _ejecutar_modificacion("DELETE FROM sesiones WHERE token_hash = %s", (token_hash,))


def contar_intentos_login(usuario, direccion_ip):
    resultado = _ejecutar_consulta(
        """
        SELECT COUNT(*) AS total FROM intentos_login
        WHERE usuario = %s AND direccion_ip = %s AND exitoso = FALSE
        AND creado_en > DATE_SUB(UTC_TIMESTAMP(), INTERVAL 15 MINUTE)
        """,
        (usuario, direccion_ip),
        una_fila=True,
    )
    return resultado["total"]


def registrar_intento_login(usuario, direccion_ip, exitoso):
    _ejecutar_modificacion(
        "INSERT INTO intentos_login (usuario, direccion_ip, exitoso) VALUES (%s, %s, %s)",
        (usuario, direccion_ip, exitoso),
    )


def obtener_rol_cuenta(usuario):
    cuenta = _ejecutar_consulta(
        "SELECT rol FROM cuentas WHERE usuario = %s", (usuario,), una_fila=True
    )
    return cuenta["rol"] if cuenta else None


def registrar_evento(usuario, evento, detalle=None):
    _ejecutar_modificacion(
        "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
        (usuario, evento, detalle),
    )


def listar_auditoria(limite=100):
    return _ejecutar_consulta(
        """
        SELECT usuario, evento, detalle, creado_en
        FROM auditoria ORDER BY id DESC LIMIT %s
        """,
        (limite,),
    )


def crear_conversacion(usuario):
    return _ejecutar_modificacion(
        "INSERT INTO conversaciones (usuario) VALUES (%s)", (usuario,), devolver_id=True
    )


def guardar_interaccion_chat(conversacion_id, usuario, pregunta, respuesta):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM conversaciones WHERE id = %s AND usuario = %s",
            (conversacion_id, usuario),
        )
        if cursor.fetchone() is None:
            conexion.rollback()
            return False
        cursor.executemany(
            "INSERT INTO mensajes_conversacion (conversacion_id, rol, contenido) VALUES (%s, %s, %s)",
            [
                (conversacion_id, "user", pregunta),
                (conversacion_id, "assistant", respuesta),
            ],
        )
        cursor.execute(
            "UPDATE conversaciones SET actualizado_en = CURRENT_TIMESTAMP WHERE id = %s",
            (conversacion_id,),
        )
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (usuario, "consulta_chat", f"Conversacion {conversacion_id}"),
        )
        conexion.commit()
        return True
    except MySQLError as error:
        if conexion is not None:
            conexion.rollback()
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


def obtener_historial_conversacion(conversacion_id, usuario):
    pertenece = _ejecutar_consulta(
        "SELECT id FROM conversaciones WHERE id = %s AND usuario = %s",
        (conversacion_id, usuario),
        una_fila=True,
    )
    if pertenece is None:
        return None
    return _ejecutar_consulta(
        """
        SELECT rol AS role, contenido AS content
        FROM mensajes_conversacion WHERE conversacion_id = %s
        ORDER BY id DESC LIMIT 10
        """,
        (conversacion_id,),
    )[::-1]


def obtener_mensajes_conversacion(conversacion_id, usuario, limite=100):
    pertenece = _ejecutar_consulta(
        "SELECT id FROM conversaciones WHERE id = %s AND usuario = %s",
        (conversacion_id, usuario),
        una_fila=True,
    )
    if pertenece is None:
        return None
    return _ejecutar_consulta(
        """
        SELECT rol, contenido, creado_en
        FROM mensajes_conversacion WHERE conversacion_id = %s
        ORDER BY id DESC LIMIT %s
        """,
        (conversacion_id, limite),
    )[::-1]


def listar_conversaciones(usuario):
    return _ejecutar_consulta(
        """
        SELECT c.id, c.actualizado_en,
            LEFT(COALESCE(m.contenido, 'Nueva conversacion'), 80) AS titulo
        FROM conversaciones c
        LEFT JOIN mensajes_conversacion m ON m.id = (
            SELECT id FROM mensajes_conversacion
            WHERE conversacion_id = c.id AND rol = 'user' ORDER BY id LIMIT 1
        )
        WHERE c.usuario = %s ORDER BY c.actualizado_en DESC
        """,
        (usuario,),
    )




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
