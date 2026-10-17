from ollama import Client

import routing
from tools import (
    analizar_ordenes,
    analizar_ordenes_esperando_material,
    analizar_prioridad_ordenes_esperando_material,
    buscar_materiales_sin_stock,
    buscar_ordenes,
    buscar_ordenes_con_material_sin_stock,
    consultar_orden,
    consultar_historial_equipo,
    analizar_riesgo_equipo,
    buscar_procedimientos,
    consultar_stock,
    consultar_usuario,
    ErrorConsultaBaseDatos,
)


MODELO = "qwen2.5:3b"
chat = Client(timeout=60).chat

TOOLS = [
    {"type": "function", "function": {"name": "consultar_orden", "description": "Consulta estado, prioridad y descripcion de una orden SAP.", "parameters": {"type": "object", "properties": {"numero_orden": {"type": "string"}}, "required": ["numero_orden"]}}},
    {"type": "function", "function": {"name": "consultar_usuario", "description": "Consulta datos de un usuario por legajo.", "parameters": {"type": "object", "properties": {"legajo": {"type": "string"}}, "required": ["legajo"]}}},
    {"type": "function", "function": {"name": "consultar_stock", "description": "Consulta la disponibilidad de un material especifico.", "parameters": {"type": "object", "properties": {"material": {"type": "string"}}, "required": ["material"]}}},
    {"type": "function", "function": {"name": "consultar_historial_equipo", "description": "Consulta datos, ordenes y avisos de falla recientes de un equipo SAP PM.", "parameters": {"type": "object", "properties": {"equipo": {"type": "string"}}, "required": ["equipo"]}}},
    {"type": "function", "function": {"name": "analizar_riesgo_equipo", "description": "Calcula un nivel de riesgo explicable para un equipo usando criticidad, avisos activos, prioridad de ordenes y fallas repetidas.", "parameters": {"type": "object", "properties": {"equipo": {"type": "string"}}, "required": ["equipo"]}}},
    {"type": "function", "function": {"name": "buscar_procedimientos", "description": "Busca procedimientos tecnicos y pasos de seguridad en documentos locales de mantenimiento. Incluye siempre la fuente al responder.", "parameters": {"type": "object", "properties": {"consulta": {"type": "string"}}, "required": ["consulta"]}}},
    {"type": "function", "function": {"name": "buscar_ordenes", "description": "Lista ordenes SAP filtrando opcionalmente por estado y prioridad.", "parameters": {"type": "object", "properties": {"estado": {"type": "string"}, "prioridad": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "analizar_ordenes", "description": "Resume cantidades y total de ordenes por estado y prioridad; no lista ordenes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "buscar_materiales_sin_stock", "description": "Lista exclusivamente materiales con stock igual a cero, no ordenes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "buscar_ordenes_con_material_sin_stock", "description": "Lista ordenes en espera de material que requieren un material con stock cero.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "analizar_ordenes_esperando_material", "description": "Lista ordenes en espera de material con material requerido, cantidad y stock actual.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "analizar_prioridad_ordenes_esperando_material", "description": "Encuentra la orden de mayor o menor prioridad entre las que esperan material.", "parameters": {"type": "object", "properties": {"tipo": {"type": "string", "enum": ["mayor", "menor"]}}, "required": ["tipo"]}}},
]

SISTEMA = """
Sos un asistente especializado en mantenimiento SAP. Usa herramientas para consultar
ordenes, usuarios, equipos, avisos de falla, materiales, stock y relaciones entre ordenes y materiales.

Usa analizar_ordenes para totales o cantidades por estado/prioridad; buscar_ordenes
para listar ordenes filtradas; buscar_materiales_sin_stock solo para materiales
agotados; y buscar_ordenes_con_material_sin_stock para ordenes que requieren un
material sin stock. No confundas estos dos ultimos casos.

No inventes informacion. Los resultados de las herramientas son la fuente de verdad.
Respeta codigos, cantidades, unidades y stock exactamente. Si una pregunta tiene
varias necesidades, usa todas las herramientas necesarias y combina los resultados.
Para historial, sintomas o fallas de un equipo usa consultar_historial_equipo. Describe
antecedentes, pero no presentes hipotesis como una prediccion confirmada.
Para priorizar la atencion de un equipo usa analizar_riesgo_equipo y explica que es
un puntaje operativo basado en reglas, no una prediccion estadistica.
Para recomendar procedimientos usa buscar_procedimientos y menciona la fuente devuelta.
Responde en forma clara y breve sin mencionar nombres internos de herramientas.
"""


def ejecutar_herramienta(nombre, argumentos):
    argumentos_requeridos = {
        "consultar_orden": {"numero_orden"},
        "consultar_usuario": {"legajo"},
        "consultar_stock": {"material"},
        "consultar_historial_equipo": {"equipo"},
        "analizar_riesgo_equipo": {"equipo"},
        "buscar_procedimientos": {"consulta"},
        "buscar_ordenes": set(),
        "analizar_ordenes": set(),
        "buscar_materiales_sin_stock": set(),
        "buscar_ordenes_con_material_sin_stock": set(),
        "analizar_ordenes_esperando_material": set(),
        "analizar_prioridad_ordenes_esperando_material": {"tipo"},
    }
    if nombre not in argumentos_requeridos:
        return "Herramienta no reconocida."
    if not isinstance(argumentos, dict):
        return "Los argumentos de la herramienta no son validos."
    faltantes = argumentos_requeridos[nombre] - argumentos.keys()
    if faltantes:
        return f"Falta el argumento obligatorio: {next(iter(faltantes))}."
    if any(not isinstance(valor, str) or not valor.strip() for valor in argumentos.values()):
        return "Los argumentos de la herramienta no son validos."
    ejecutores = {
        "consultar_orden": lambda: consultar_orden(argumentos["numero_orden"]),
        "consultar_usuario": lambda: consultar_usuario(argumentos["legajo"]),
        "consultar_stock": lambda: consultar_stock(argumentos["material"]),
        "consultar_historial_equipo": lambda: consultar_historial_equipo(argumentos["equipo"]),
        "analizar_riesgo_equipo": lambda: analizar_riesgo_equipo(argumentos["equipo"]),
        "buscar_procedimientos": lambda: buscar_procedimientos(argumentos["consulta"]),
        "buscar_ordenes": lambda: buscar_ordenes(
            estado=argumentos.get("estado"), prioridad=argumentos.get("prioridad")
        ),
        "analizar_ordenes": analizar_ordenes,
        "buscar_materiales_sin_stock": buscar_materiales_sin_stock,
        "buscar_ordenes_con_material_sin_stock": buscar_ordenes_con_material_sin_stock,
        "analizar_ordenes_esperando_material": analizar_ordenes_esperando_material,
        "analizar_prioridad_ordenes_esperando_material": lambda: (
            analizar_prioridad_ordenes_esperando_material(argumentos.get("tipo", "mayor"))
        ),
    }
    ejecutor = ejecutores.get(nombre)
    try:
        return ejecutor()
    except KeyError as error:
        return f"Falta el argumento obligatorio: {error.args[0]}."
    except ErrorConsultaBaseDatos:
        return "No se pudo consultar la base de datos."


def ejecutar_consulta_compuesta(tipo_consulta):
    if tipo_consulta == "total_sin_stock":
        return [
            ("analizar_ordenes", analizar_ordenes()),
            (
                "buscar_ordenes_con_material_sin_stock",
                buscar_ordenes_con_material_sin_stock(),
            ),
        ]

    tipo_prioridad = "menor" if tipo_consulta.endswith("_menor") else "mayor"
    return [
        ("analizar_ordenes_esperando_material", analizar_ordenes_esperando_material()),
        (
            "analizar_prioridad_ordenes_esperando_material",
            analizar_prioridad_ordenes_esperando_material(tipo_prioridad),
        ),
    ]


def formatear_orden_esperando_material(orden):
    return (
        f"- Orden {orden['numero_orden']} ({orden['prioridad']}): "
        f"{orden['descripcion_orden']}. Requiere {orden['cantidad_requerida']} "
        f"{orden['unidad']} de {orden['material']} "
        f"({orden['descripcion_material']}); stock actual: {orden['stock']} "
        f"{orden['unidad']}."
    )


def redactar_consulta_compuesta(tipo_consulta, resultados):
    resultados_por_nombre = dict(resultados)

    if tipo_consulta == "total_sin_stock":
        total = resultados_por_nombre["analizar_ordenes"]["total_ordenes"]
        ordenes = resultados_por_nombre["buscar_ordenes_con_material_sin_stock"]
        respuesta = f"Hay {total} ordenes en total."
        if not ordenes:
            return respuesta + "\n\nNo hay ordenes con materiales sin stock."
        detalle = "\n".join(formatear_orden_esperando_material(orden) for orden in ordenes)
        return respuesta + "\n\nOrdenes con materiales sin stock:\n" + detalle

    ordenes = resultados_por_nombre["analizar_ordenes_esperando_material"]
    orden_prioritaria = resultados_por_nombre[
        "analizar_prioridad_ordenes_esperando_material"
    ]
    if not ordenes:
        return "No hay ordenes esperando material."

    tipo_prioridad = "menor" if tipo_consulta.endswith("_menor") else "mayor"
    detalle = "\n".join(formatear_orden_esperando_material(orden) for orden in ordenes)
    return (
        "Ordenes esperando material:\n"
        + detalle
        + f"\n\nLa orden de {tipo_prioridad} prioridad es "
        + f"{orden_prioritaria['numero_orden']} ({orden_prioritaria['prioridad']})."
    )


def redactar_consulta_stock(resultado):
    if isinstance(resultado, str):
        return resultado
    return (
        f"El material {resultado['material']} ({resultado['descripcion']}) "
        f"tiene un stock actual de {resultado['stock']} {resultado['unidad']}."
    )


def redactar_lista_ordenes(ordenes):
    if not ordenes:
        return "No se encontraron ordenes."
    return "\n".join(
        f"- Orden {orden['numero_orden']} ({orden['prioridad']}, {orden['estado']}): "
        f"{orden['descripcion']}."
        for orden in ordenes
    )


def redactar_historial_equipo(resultado):
    if isinstance(resultado, str):
        return resultado
    respuesta = (
        f"El equipo {resultado['equipo']} ({resultado['descripcion']}) esta en "
        f"{resultado['ubicacion_tecnica']} y tiene criticidad {resultado['criticidad']}."
    )
    if resultado["avisos"]:
        avisos = "\n".join(
            f"- Aviso {aviso['numero_aviso']} ({aviso['fecha_aviso']}): {aviso['sintoma']}. "
            f"Modo de falla: {aviso['modo_falla'] or 'sin registrar'}."
            for aviso in resultado["avisos"]
        )
        respuesta += "\n\nAvisos recientes:\n" + avisos
    else:
        respuesta += "\n\nNo hay avisos de falla registrados."
    return respuesta


def redactar_riesgo_equipo(resultado):
    if isinstance(resultado, str):
        return resultado
    razones = "\n".join(f"- {razon}" for razon in resultado["razones"])
    return (
        f"El equipo {resultado['equipo']} tiene riesgo {resultado['nivel']} "
        f"({resultado['puntaje']}/100).\n\nFactores considerados:\n{razones}\n\n"
        "Es un puntaje operativo basado en reglas, no una prediccion estadistica."
    )


def redactar_procedimientos(documentos):
    if not documentos:
        return "No se encontraron procedimientos tecnicos relacionados."
    return "\n\n".join(
        f"{documento['titulo']}\n{documento['contenido']}\nFuente: {documento['fuente']}."
        for documento in documentos
    )


def redactar_resultado_herramienta(nombre, resultado):
    if isinstance(resultado, str):
        return resultado

    if nombre == "consultar_orden":
        return (
            f"La orden {resultado['numero_orden']} esta en estado "
            f"{resultado['estado']} con prioridad {resultado['prioridad']}. "
            f"Descripcion: {resultado['descripcion']}."
        )
    if nombre == "consultar_usuario":
        return (
            f"El usuario {resultado['legajo']} es {resultado['nombre']}, "
            f"del sector {resultado['sector']}, con estado {resultado['estado']}."
        )
    if nombre == "consultar_stock":
        return redactar_consulta_stock(resultado)
    if nombre == "consultar_historial_equipo":
        return redactar_historial_equipo(resultado)
    if nombre == "analizar_riesgo_equipo":
        return redactar_riesgo_equipo(resultado)
    if nombre == "buscar_procedimientos":
        return redactar_procedimientos(resultado)
    if nombre == "buscar_ordenes":
        return redactar_lista_ordenes(resultado)
    if nombre == "buscar_materiales_sin_stock":
        if not resultado:
            return "No hay materiales sin stock."
        return "\n".join(
            f"- {material['material']} ({material['descripcion']}): "
            f"stock {material['stock']} {material['unidad']}."
            for material in resultado
        )
    if nombre == "analizar_ordenes":
        return (
            f"Total de ordenes: {resultado['total_ordenes']}. "
            f"En espera de material: {resultado['en_espera_material']}; "
            f"en reparacion: {resultado['en_reparacion']}; "
            f"finalizadas: {resultado['finalizadas']}."
        )
    return None


def ejecutar_chat(**argumentos):
    try:
        return chat(**argumentos)
    except Exception:
        return None


def procesar_pregunta(pregunta, historial=None):
    mensajes_historial = historial or []
    messages = [{"role": "system", "content": SISTEMA}]
    messages.extend(mensajes_historial[-10:])
    messages.append({"role": "user", "content": pregunta})
    tipo_consulta = routing.detectar_consulta_compuesta(pregunta)

    if tipo_consulta:
        try:
            resultados = ejecutar_consulta_compuesta(tipo_consulta)
        except ErrorConsultaBaseDatos:
            return {"respuesta": "No se pudo consultar la base de datos.", "herramientas_usadas": [], "resultados": []}
        return {
            "respuesta": redactar_consulta_compuesta(tipo_consulta, resultados),
            "herramientas_usadas": [nombre for nombre, _ in resultados],
            "resultados": resultados,
        }

    respuesta = ejecutar_chat(model=MODELO, messages=messages, tools=TOOLS)
    if respuesta is None:
        return {"respuesta": "No se pudo conectar con Ollama. Verifica que este iniciado y que el modelo este instalado.", "herramientas_usadas": [], "resultados": []}
    mensaje = getattr(respuesta, "message", None)
    if mensaje is None:
        return {"respuesta": "Ollama devolvio una respuesta no valida.", "herramientas_usadas": [], "resultados": []}
    tool_calls = getattr(mensaje, "tool_calls", None)
    if not tool_calls:
        contenido = getattr(mensaje, "content", None)
        if not isinstance(contenido, str):
            return {"respuesta": "Ollama devolvio una respuesta no valida.", "herramientas_usadas": [], "resultados": []}
        return {"respuesta": contenido, "herramientas_usadas": [], "resultados": []}

    messages.append(mensaje)
    resultados_tools = []
    for tool_call in tool_calls:
        funcion = getattr(tool_call, "function", None)
        nombre = getattr(funcion, "name", None)
        argumentos = getattr(funcion, "arguments", None)
        if not isinstance(nombre, str):
            return {"respuesta": "Ollama solicito una herramienta no valida.", "herramientas_usadas": [], "resultados": []}
        resultado = ejecutar_herramienta(nombre, argumentos)
        resultados_tools.append((nombre, argumentos, resultado))
        messages.append({"role": "tool", "tool_name": nombre, "content": str(resultado)})

    if len(resultados_tools) == 1:
        nombre, _, resultado = resultados_tools[0]
        respuesta_directa = redactar_resultado_herramienta(nombre, resultado)
        if respuesta_directa is not None:
            return {
                "respuesta": respuesta_directa,
                "herramientas_usadas": [nombre],
                "resultados": resultados_tools,
            }

    respuesta_final = ejecutar_chat(model=MODELO, messages=messages, tools=TOOLS)
    if respuesta_final is None:
        return {"respuesta": "No se pudo conectar con Ollama. Verifica que este iniciado y que el modelo este instalado.", "herramientas_usadas": [nombre for nombre, _, _ in resultados_tools], "resultados": resultados_tools}
    contenido_final = getattr(getattr(respuesta_final, "message", None), "content", None)
    if not isinstance(contenido_final, str):
        contenido_final = "Ollama devolvio una respuesta no valida."
    return {
        "respuesta": contenido_final,
        "herramientas_usadas": [nombre for nombre, _, _ in resultados_tools],
        "resultados": resultados_tools,
    }


def main():
    pregunta = input("Escribi tu pregunta: ")
    respuesta = procesar_pregunta(pregunta)
    for resultado in respuesta["resultados"]:
        if len(resultado) == 2:
            nombre, datos = resultado
            print(f"Tool utilizada: {nombre}")
            print(f"Resultado de la Tool: {datos}")
        else:
            nombre, argumentos, datos = resultado
            print(f"Tool utilizada: {nombre}")
            print(f"Argumentos: {argumentos}")
            print(f"Resultado de la Tool: {datos}")
    print("\nRespuesta final:")
    print(respuesta["respuesta"])


if __name__ == "__main__":
    main()
