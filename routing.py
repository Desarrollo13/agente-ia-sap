def detectar_consulta_compuesta(pregunta):
    pregunta = pregunta.lower()

    contiene_total = (
        "cuántas órdenes" in pregunta
        or "cuantas ordenes" in pregunta
        or "total de órdenes" in pregunta
        or "total de ordenes" in pregunta
    )

    contiene_ordenes_sin_stock = (
        "qué órdenes tienen materiales sin stock" in pregunta
        or "que ordenes tienen materiales sin stock" in pregunta
        or "órdenes con materiales sin stock" in pregunta
        or "ordenes con materiales sin stock" in pregunta
    )

    if contiene_total and contiene_ordenes_sin_stock:
        return "total_sin_stock"

    contiene_esperando_material = (
        "órdenes esperando material" in pregunta
        or "ordenes esperando material" in pregunta
        or "órdenes que esperan material" in pregunta
        or "ordenes que esperan material" in pregunta
        or "esperando materiales" in pregunta
        or "esperan material" in pregunta
    )

    contiene_mayor_prioridad = (
        "mayor prioridad" in pregunta
        or "más prioritaria" in pregunta
        or "mas prioritaria" in pregunta
        or "prioridad más alta" in pregunta
        or "prioridad mas alta" in pregunta
        or "atender primero" in pregunta
    )

    contiene_menor_prioridad = (
        "menor prioridad" in pregunta
        or "menos prioritaria" in pregunta
        or "prioridad más baja" in pregunta
        or "prioridad mas baja" in pregunta
        or "atender ultimo" in pregunta
        or "atender último" in pregunta
    )

    if contiene_esperando_material and contiene_mayor_prioridad:
        return "esperando_material_prioridad"
    if contiene_esperando_material and contiene_menor_prioridad:
        return "esperando_material_prioridad_menor"

    return None
