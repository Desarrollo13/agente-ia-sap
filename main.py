from ollama import chat

import routing
from tools import (
    analizar_ordenes,
    analizar_ordenes_esperando_material,
    analizar_prioridad_ordenes_esperando_material,
    buscar_materiales_sin_stock,
    buscar_ordenes,
    buscar_ordenes_con_material_sin_stock,
    consultar_orden,
    consultar_stock,
    consultar_usuario,
    ErrorConsultaBaseDatos,
)


MODELO = "qwen2.5:3b"

TOOLS = [
    {"type": "function", "function": {"name": "consultar_orden", "description": "Consulta estado, prioridad y descripcion de una orden SAP.", "parameters": {"type": "object", "properties": {"numero_orden": {"type": "string"}}, "required": ["numero_orden"]}}},
    {"type": "function", "function": {"name": "consultar_usuario", "description": "Consulta datos de un usuario por legajo.", "parameters": {"type": "object", "properties": {"legajo": {"type": "string"}}, "required": ["legajo"]}}},
    {"type": "function", "function": {"name": "consultar_stock", "description": "Consulta la disponibilidad de un material especifico.", "parameters": {"type": "object", "properties": {"material": {"type": "string"}}, "required": ["material"]}}},
    {"type": "function", "function": {"name": "buscar_ordenes", "description": "Lista ordenes SAP filtrando opcionalmente por estado y prioridad.", "parameters": {"type": "object", "properties": {"estado": {"type": "string"}, "prioridad": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "analizar_ordenes", "description": "Resume cantidades y total de ordenes por estado y prioridad; no lista ordenes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "buscar_materiales_sin_stock", "description": "Lista exclusivamente materiales con stock igual a cero, no ordenes.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "buscar_ordenes_con_material_sin_stock", "description": "Lista ordenes en espera de material que requieren un material con stock cero.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "analizar_ordenes_esperando_material", "description": "Lista ordenes en espera de material con material requerido, cantidad y stock actual.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "analizar_prioridad_ordenes_esperando_material", "description": "Encuentra la orden de mayor o menor prioridad entre las que esperan material.", "parameters": {"type": "object", "properties": {"tipo": {"type": "string", "enum": ["mayor", "menor"]}}, "required": ["tipo"]}}},
]

SISTEMA = """
Sos un asistente especializado en mantenimiento SAP. Usa herramientas para consultar
ordenes, usuarios, materiales, stock y relaciones entre ordenes y materiales.

Usa analizar_ordenes para totales o cantidades por estado/prioridad; buscar_ordenes
para listar ordenes filtradas; buscar_materiales_sin_stock solo para materiales
agotados; y buscar_ordenes_con_material_sin_stock para ordenes que requieren un
material sin stock. No confundas estos dos ultimos casos.

No inventes informacion. Los resultados de las herramientas son la fuente de verdad.
Respeta codigos, cantidades, unidades y stock exactamente. Si una pregunta tiene
varias necesidades, usa todas las herramientas necesarias y combina los resultados.
Responde en forma clara y breve sin mencionar nombres internos de herramientas.
"""


def ejecutar_herramienta(nombre, argumentos):
    ejecutores = {
        "consultar_orden": lambda: consultar_orden(argumentos["numero_orden"]),
        "consultar_usuario": lambda: consultar_usuario(argumentos["legajo"]),
        "consultar_stock": lambda: consultar_stock(argumentos["material"]),
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
    if ejecutor is None:
        return "Herramienta no reconocida."
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
    if not respuesta.message.tool_calls:
        return {"respuesta": respuesta.message.content, "herramientas_usadas": [], "resultados": []}

    messages.append(respuesta.message)
    resultados_tools = []
    for tool_call in respuesta.message.tool_calls:
        nombre = tool_call.function.name
        argumentos = tool_call.function.arguments
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
    return {
        "respuesta": respuesta_final.message.content,
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
