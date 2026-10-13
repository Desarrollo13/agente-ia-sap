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


def ejecutar_consulta_compuesta(tipo_consulta):
    if tipo_consulta == "total_sin_stock":
        return [
            ("analizar_ordenes", analizar_ordenes()),
            (
                "buscar_ordenes_con_material_sin_stock",
                buscar_ordenes_con_material_sin_stock(),
            ),
        ], """Indica el total de ordenes y todas las ordenes que requieren un material con stock cero. Responde exclusivamente con los resultados recibidos."""

    tipo_prioridad = "menor" if tipo_consulta.endswith("_menor") else "mayor"
    descripcion_prioridad = "menor" if tipo_prioridad == "menor" else "mayor"
    return [
        ("analizar_ordenes_esperando_material", analizar_ordenes_esperando_material()),
        (
            "analizar_prioridad_ordenes_esperando_material",
            analizar_prioridad_ordenes_esperando_material(tipo_prioridad),
        ),
    ], f"""Enumera todas las ordenes que esperan material y luego identifica la de {descripcion_prioridad} prioridad. Respeta exactamente materiales, cantidades, stock y unidades. Responde exclusivamente con los resultados recibidos."""


def main():
    pregunta = input("Escribi tu pregunta: ")
    messages = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": pregunta}]
    tipo_consulta = routing.detectar_consulta_compuesta(pregunta)

    if tipo_consulta:
        resultados, instruccion = ejecutar_consulta_compuesta(tipo_consulta)
        messages.append({"role": "system", "content": instruccion})
        for nombre, resultado in resultados:
            print(f"Tool utilizada: {nombre}")
            print(f"Resultado de la Tool: {resultado}")
            messages.append({"role": "tool", "tool_name": nombre, "content": str(resultado)})
        respuesta_final = chat(model=MODELO, messages=messages)
        print("\nRespuesta final:")
        print(respuesta_final.message.content)
        return

    respuesta = chat(model=MODELO, messages=messages, tools=TOOLS)
    if not respuesta.message.tool_calls:
        print("\nNo se utilizo ninguna herramienta.\n\nRespuesta:")
        print(respuesta.message.content)
        return

    messages.append(respuesta.message)
    for tool_call in respuesta.message.tool_calls:
        nombre = tool_call.function.name
        argumentos = tool_call.function.arguments
        resultado = ejecutar_herramienta(nombre, argumentos)
        print(f"Tool utilizada: {nombre}")
        print(f"Argumentos: {argumentos}")
        print(f"Resultado de la Tool: {resultado}")
        messages.append({"role": "tool", "tool_name": nombre, "content": str(resultado)})

    respuesta_final = chat(model=MODELO, messages=messages, tools=TOOLS)
    print("\nRespuesta final:")
    print(respuesta_final.message.content)


if __name__ == "__main__":
    main()
