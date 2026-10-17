from database import obtener_conexion
from mysql.connector import Error as MySQLError, IntegrityError
from seguridad import verificar_contrasena
import re
import unicodedata


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


def intentar_inicio_sesion(usuario, contrasena, direccion_ip):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT GET_LOCK(%s, 5) AS bloqueado", (f"login:{usuario}:{direccion_ip}",))
        if cursor.fetchone()["bloqueado"] != 1:
            raise ErrorConsultaBaseDatos()
        cursor.execute(
            """SELECT COUNT(*) AS total FROM intentos_login
               WHERE usuario = %s AND direccion_ip = %s AND exitoso = FALSE
               AND creado_en > DATE_SUB(UTC_TIMESTAMP(), INTERVAL 15 MINUTE)""",
            (usuario, direccion_ip),
        )
        if cursor.fetchone()["total"] >= 5:
            return None
        cursor.execute("SELECT contrasena_cifrada, rol FROM cuentas WHERE usuario = %s", (usuario,))
        cuenta = cursor.fetchone()
        autenticada = cuenta is not None and verificar_contrasena(contrasena, cuenta["contrasena_cifrada"])
        cursor.execute("INSERT INTO intentos_login (usuario, direccion_ip, exitoso) VALUES (%s, %s, %s)", (usuario, direccion_ip, autenticada))
        conexion.commit()
        return cuenta["rol"] if autenticada else False
    except MySQLError as error:
        if conexion is not None:
            conexion.rollback()
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            try:
                cursor.execute("SELECT RELEASE_LOCK(%s)", (f"login:{usuario}:{direccion_ip}",))
                cursor.fetchone()
            except MySQLError:
                pass
            cursor.close()
        if conexion is not None:
            conexion.close()


def obtener_rol_cuenta(usuario):
    cuenta = _ejecutar_consulta(
        "SELECT rol FROM cuentas WHERE usuario = %s", (usuario,), una_fila=True
    )
    return cuenta["rol"] if cuenta else None


def listar_cuentas():
    return _ejecutar_consulta(
        "SELECT usuario, rol, creado_en FROM cuentas ORDER BY usuario"
    )


def crear_cuenta_administrada(usuario, contrasena_cifrada, rol, administrador):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO cuentas (usuario, contrasena_cifrada, rol) VALUES (%s, %s, %s)",
            (usuario, contrasena_cifrada, rol),
        )
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (administrador, "cuenta_creada", f"{usuario} ({rol})"),
        )
        conexion.commit()
        return True
    except IntegrityError:
        if conexion is not None:
            conexion.rollback()
        return False
    except MySQLError as error:
        if conexion is not None:
            conexion.rollback()
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


def actualizar_rol_cuenta(usuario, rol, administrador):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        if rol != "administrador":
            cursor.execute("SELECT usuario FROM cuentas WHERE rol = 'administrador' FOR UPDATE")
            administradores = cursor.fetchall()
            if any(cuenta["usuario"] == usuario for cuenta in administradores) and len(administradores) == 1:
                conexion.rollback()
                return None
        cursor.execute("UPDATE cuentas SET rol = %s WHERE usuario = %s", (rol, usuario))
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (administrador, "rol_cuenta_actualizado", f"{usuario} ({rol})"),
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


def restablecer_contrasena_cuenta(usuario, contrasena_cifrada, administrador):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE cuentas SET contrasena_cifrada = %s WHERE usuario = %s",
            (contrasena_cifrada, usuario),
        )
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        cursor.execute("DELETE FROM sesiones WHERE usuario = %s", (usuario,))
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (administrador, "contrasena_restablecida", usuario),
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


def eliminar_conversacion(conversacion_id, usuario):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE FROM conversaciones WHERE id = %s AND usuario = %s",
            (conversacion_id, usuario),
        )
        if cursor.rowcount == 0:
            conexion.rollback()
            return False
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (usuario, "conversacion_eliminada", f"Conversacion {conversacion_id}"),
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


def consultar_historial_equipo(equipo):
    datos_equipo = _ejecutar_consulta(
        """
        SELECT equipo, descripcion, ubicacion_tecnica, criticidad
        FROM equipos WHERE equipo = %s
        """,
        (equipo,),
        una_fila=True,
    )
    if datos_equipo is None:
        return "No se encontro el equipo."
    avisos = _ejecutar_consulta(
        """
        SELECT numero_aviso, numero_orden, fecha_aviso, estado, sintoma, modo_falla, causa
        FROM avisos_falla WHERE equipo = %s
        ORDER BY fecha_aviso DESC LIMIT 10
        """,
        (equipo,),
    )
    ordenes = _ejecutar_consulta(
        """
        SELECT numero_orden, estado, prioridad, descripcion
        FROM ordenes WHERE equipo = %s
        ORDER BY numero_orden DESC LIMIT 10
        """,
        (equipo,),
    )
    return {**datos_equipo, "avisos": avisos, "ordenes": ordenes}


def analizar_riesgo_equipo(equipo):
    historial = consultar_historial_equipo(equipo)
    if isinstance(historial, str):
        return historial

    puntaje = {"Alta": 30, "Media": 20, "Baja": 10}[historial["criticidad"]]
    razones = [f"Criticidad {historial['criticidad']}: {puntaje} puntos."]
    avisos_activos = [aviso for aviso in historial["avisos"] if aviso["estado"] != "Cerrado"]
    if avisos_activos:
        puntos_avisos = min(len(avisos_activos) * 20, 40)
        puntaje += puntos_avisos
        razones.append(f"{len(avisos_activos)} aviso(s) de falla activo(s): {puntos_avisos} puntos.")

    prioridades = {orden["prioridad"] for orden in historial["ordenes"] if orden["estado"] != "Finalizada"}
    if "Alta" in prioridades:
        puntaje += 20
        razones.append("Orden de prioridad Alta en curso: 20 puntos.")
    elif "Media" in prioridades:
        puntaje += 10
        razones.append("Orden de prioridad Media en curso: 10 puntos.")

    modos_falla = {}
    for aviso in historial["avisos"]:
        modo = aviso.get("modo_falla")
        if modo:
            modos_falla[modo] = modos_falla.get(modo, 0) + 1
    repetidos = [modo for modo, cantidad in modos_falla.items() if cantidad >= 2]
    if repetidos:
        puntaje += 15
        razones.append(f"Modo de falla repetido ({', '.join(repetidos)}): 15 puntos.")

    puntaje = min(puntaje, 100)
    nivel = "Alto" if puntaje >= 70 else "Medio" if puntaje >= 40 else "Bajo"
    return {
        "equipo": historial["equipo"],
        "puntaje": puntaje,
        "nivel": nivel,
        "razones": razones,
    }


def crear_alerta_riesgo_alto(equipo, usuario):
    riesgo = analizar_riesgo_equipo(equipo)
    if isinstance(riesgo, str):
        return riesgo
    if riesgo["nivel"] != "Alto":
        return {"creada": False, "motivo": "El equipo no tiene riesgo alto.", "riesgo": riesgo}

    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT equipo FROM equipos WHERE equipo = %s FOR UPDATE", (equipo,))
        if cursor.fetchone() is None:
            conexion.rollback()
            return "No se encontro el equipo."
        cursor.execute(
            "SELECT id FROM alertas_mantenimiento WHERE equipo = %s AND estado = 'Pendiente'",
            (equipo,),
        )
        alerta_existente = cursor.fetchone()
        if alerta_existente:
            conexion.rollback()
            return {
                "creada": False,
                "motivo": "Ya existe una alerta pendiente para este equipo.",
                "alerta_id": alerta_existente["id"],
                "riesgo": riesgo,
            }
        detalle = " ".join(riesgo["razones"])
        cursor.execute(
            """
            INSERT INTO alertas_mantenimiento (equipo, nivel, puntaje, detalle, creada_por)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (equipo, riesgo["nivel"], riesgo["puntaje"], detalle, usuario),
        )
        alerta_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (usuario, "alerta_riesgo_creada", f"Alerta {alerta_id} para {equipo}"),
        )
        conexion.commit()
        return {"creada": True, "alerta_id": alerta_id, "riesgo": riesgo}
    except MySQLError as error:
        if conexion is not None:
            conexion.rollback()
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


def listar_alertas(estado="Pendiente"):
    return _ejecutar_consulta(
        """
        SELECT a.id, a.equipo, e.descripcion AS descripcion_equipo, a.nivel, a.puntaje,
            a.detalle, a.estado, a.creada_por, a.creada_en, a.atendida_por, a.atendida_en
        FROM alertas_mantenimiento a
        INNER JOIN equipos e ON e.equipo = a.equipo
        WHERE a.estado = %s
        ORDER BY a.creada_en DESC
        """,
        (estado,),
    )


def atender_alerta(alerta_id, usuario):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT equipo FROM alertas_mantenimiento WHERE id = %s FOR UPDATE", (alerta_id,))
        alerta = cursor.fetchone()
        if alerta is None:
            conexion.rollback()
            return False
        cursor.execute(
            """
            UPDATE alertas_mantenimiento
            SET estado = 'Atendida', atendida_por = %s, atendida_en = UTC_TIMESTAMP()
            WHERE id = %s AND estado = 'Pendiente'
            """,
            (usuario, alerta_id),
        )
        if cursor.rowcount == 0:
            conexion.rollback()
            return None
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (usuario, "alerta_riesgo_atendida", f"Alerta {alerta_id} para {alerta['equipo']}"),
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


def buscar_procedimientos(consulta, limite=3):
    texto_normalizado = unicodedata.normalize("NFKD", consulta.lower())
    texto_normalizado = "".join(caracter for caracter in texto_normalizado if not unicodedata.combining(caracter))
    palabras = {
        palabra for palabra in re.findall(r"[a-z0-9]+", texto_normalizado)
        if len(palabra) >= 3 and palabra not in {"para", "como", "con", "del", "las", "los", "una", "que", "equipo"}
    }
    if not palabras:
        return []
    consulta_busqueda = " ".join(f"{palabra}*" for palabra in sorted(palabras))
    documentos = _ejecutar_consulta(
        """
        SELECT id, titulo, fuente, contenido
        FROM documentos_tecnicos
        WHERE MATCH(titulo, contenido) AGAINST (%s IN BOOLEAN MODE)
        ORDER BY MATCH(titulo, contenido) AGAINST (%s IN BOOLEAN MODE) DESC, titulo
        LIMIT %s
        """,
        (consulta_busqueda, consulta_busqueda, limite),
    )
    resultados = []
    for documento in documentos:
        contenido_normalizado = unicodedata.normalize(
            "NFKD", f"{documento['titulo']} {documento['contenido']}".lower()
        )
        contenido_normalizado = "".join(
            caracter for caracter in contenido_normalizado if not unicodedata.combining(caracter)
        )
        coincidencias = sum(palabra in contenido_normalizado for palabra in palabras)
        if coincidencias:
            resultados.append({
                "id": documento["id"],
                "titulo": documento["titulo"],
                "fuente": documento["fuente"],
                "contenido": documento["contenido"],
                "relevancia": coincidencias,
            })
    return sorted(resultados, key=lambda documento: (-documento["relevancia"], documento["titulo"]))


def listar_documentos_tecnicos():
    return _ejecutar_consulta(
        "SELECT id, titulo, fuente, contenido, creado_en FROM documentos_tecnicos ORDER BY id DESC"
    )


def crear_documento_tecnico(titulo, fuente, contenido, administrador):
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO documentos_tecnicos (titulo, fuente, contenido) VALUES (%s, %s, %s)",
            (titulo, fuente, contenido),
        )
        documento_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO auditoria (usuario, evento, detalle) VALUES (%s, %s, %s)",
            (administrador, "documento_tecnico_creado", f"Documento {documento_id}: {titulo}"),
        )
        conexion.commit()
        return documento_id
    except IntegrityError:
        if conexion is not None:
            conexion.rollback()
        return None
    except MySQLError as error:
        if conexion is not None:
            conexion.rollback()
        raise ErrorConsultaBaseDatos from error
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


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
    return {clave: int(valor or 0) for clave, valor in resultado.items()}


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
