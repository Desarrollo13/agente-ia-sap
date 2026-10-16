import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
import tools


@pytest.fixture(autouse=True)
def evitar_auditoria_real(monkeypatch):
    monkeypatch.setattr(api, "registrar_evento", lambda *_args: None)
    monkeypatch.setattr(api, "contar_intentos_login", lambda *_args: 0)
    monkeypatch.setattr(api, "registrar_intento_login", lambda *_args: None)


def autenticar_como_admin():
    api.app.dependency_overrides[api.obtener_usuario_actual] = lambda: "admin"


def limpiar_autenticacion():
    api.app.dependency_overrides.clear()


def test_consultar_chat_devuelve_respuesta_y_herramientas(monkeypatch):
    historial_recibido = []

    def procesar(pregunta, historial):
        historial_recibido.extend(historial)
        return {"respuesta": f"Respuesta para: {pregunta}", "herramientas_usadas": ["consultar_stock"]}

    monkeypatch.setattr(api, "procesar_pregunta", procesar)
    monkeypatch.setattr(api, "crear_conversacion", lambda _usuario: 7)
    monkeypatch.setattr(api, "obtener_historial_conversacion", lambda *_args: [])
    monkeypatch.setattr(api, "guardar_interaccion_chat", lambda *_args: True)
    autenticar_como_admin()
    respuesta = TestClient(api.app).post("/api/chat", json={"pregunta": "Stock de MAT-003"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"respuesta": "Respuesta para: Stock de MAT-003", "herramientas_usadas": ["consultar_stock"], "conversacion_id": 7}
    assert historial_recibido == []
    limpiar_autenticacion()


def test_consultar_chat_envia_el_historial_persistido_al_agente(monkeypatch):
    historial_recibido = []

    def procesar(_pregunta, historial):
        historial_recibido.extend(historial)
        return {"respuesta": "Correcto.", "herramientas_usadas": []}

    monkeypatch.setattr(api, "procesar_pregunta", procesar)
    monkeypatch.setattr(api, "obtener_historial_conversacion", lambda *_args: [{"role": "user", "content": "Consulta la orden 45001234"}])
    monkeypatch.setattr(api, "guardar_interaccion_chat", lambda *_args: True)
    autenticar_como_admin()
    respuesta = TestClient(api.app).post("/api/chat", json={"pregunta": "Y cual es su prioridad?", "conversacion_id": 3})

    assert respuesta.status_code == 200
    assert historial_recibido == [{"role": "user", "content": "Consulta la orden 45001234"}]
    limpiar_autenticacion()


def test_consultar_chat_rechaza_pregunta_vacia():
    autenticar_como_admin()
    assert TestClient(api.app).post("/api/chat", json={"pregunta": ""}).status_code == 422
    limpiar_autenticacion()


def test_endpoints_operativos_requieren_autenticacion():
    cliente = TestClient(api.app)
    assert cliente.post("/api/chat", json={"pregunta": "Stock"}).status_code == 401
    assert cliente.get("/api/conversaciones").status_code == 401
    assert cliente.get("/api/conversaciones/1").status_code == 401
    assert cliente.get("/api/cuentas").status_code == 401
    assert cliente.get("/api/resumen").status_code == 401
    assert cliente.get("/api/estado").status_code == 401


def test_api_permite_el_origen_del_frontend():
    respuesta = TestClient(api.app).options("/api/chat", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_consultar_resumen_devuelve_indicadores(monkeypatch):
    monkeypatch.setattr(api, "analizar_ordenes", lambda: {"total_ordenes": 4, "en_espera_material": 2})
    monkeypatch.setattr(api, "buscar_materiales_sin_stock", lambda: [{"material": "MAT-003"}])
    monkeypatch.setattr(api, "analizar_prioridad_ordenes_esperando_material", lambda _tipo: {"numero_orden": "45001234"})
    autenticar_como_admin()
    respuesta = TestClient(api.app).get("/api/resumen")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"total_ordenes": 4, "en_espera_material": 2, "materiales_sin_stock": 1, "orden_mayor_prioridad": "45001234"}
    limpiar_autenticacion()


def test_consultar_estado_verifica_base_y_modelo(monkeypatch):
    class RespuestaModelos:
        models = [type("Modelo", (), {"model": "qwen2.5:3b"})()]

    monkeypatch.setattr(api, "analizar_ordenes", lambda: {})
    monkeypatch.setattr(api, "listar_modelos", lambda: RespuestaModelos())
    autenticar_como_admin()
    respuesta = TestClient(api.app).get("/api/estado")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"disponible": True, "base_datos": True, "ollama": True}
    limpiar_autenticacion()


def test_login_crea_una_sesion(monkeypatch):
    monkeypatch.setattr(api, "intentar_inicio_sesion", lambda *_args: "administrador")
    sesiones = []
    monkeypatch.setattr(api, "crear_sesion", lambda usuario, token: sesiones.append((usuario, token)))

    respuesta = TestClient(api.app).post("/api/login", json={"usuario": "admin", "contrasena": "secreta"})

    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"] == "admin"
    assert respuesta.json()["rol"] == "administrador"
    assert respuesta.json()["token"]
    assert sesiones[0][0] == "admin"
    assert sesiones[0][1] != respuesta.json()["token"]


def test_login_rechaza_credenciales_incorrectas(monkeypatch):
    monkeypatch.setattr(api, "intentar_inicio_sesion", lambda *_args: False)
    respuesta = TestClient(api.app).post("/api/login", json={"usuario": "admin", "contrasena": "error"})
    assert respuesta.status_code == 401


def test_login_bloquea_despues_de_cinco_intentos(monkeypatch):
    monkeypatch.setattr(api, "intentar_inicio_sesion", lambda *_args: None)

    respuesta = TestClient(api.app).post("/api/login", json={"usuario": "admin", "contrasena": "error"})

    assert respuesta.status_code == 429


def test_logout_revoca_la_sesion_aunque_falle_la_auditoria(monkeypatch):
    token_eliminado = []
    autenticar_como_admin()
    monkeypatch.setattr(api, "eliminar_sesion", lambda token: token_eliminado.append(token))
    monkeypatch.setattr(api, "registrar_evento", lambda *_args: (_ for _ in ()).throw(api.ErrorConsultaBaseDatos()))

    respuesta = TestClient(api.app).post("/api/logout", headers={"Authorization": "Bearer token-prueba"})

    assert respuesta.status_code == 204
    assert token_eliminado
    limpiar_autenticacion()


def test_auditoria_requiere_administrador(monkeypatch):
    api.app.dependency_overrides[api.requiere_administrador] = lambda: "admin"
    monkeypatch.setattr(api, "listar_auditoria", lambda: [{
        "usuario": "admin",
        "evento": "inicio_sesion",
        "detalle": None,
        "creado_en": "2026-10-14T12:00:00",
    }])

    respuesta = TestClient(api.app).get("/api/auditoria")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["evento"] == "inicio_sesion"
    limpiar_autenticacion()


def test_auditoria_rechaza_a_un_operador(monkeypatch):
    api.app.dependency_overrides[api.obtener_usuario_actual] = lambda: "operador"
    monkeypatch.setattr(api, "obtener_rol_cuenta", lambda _usuario: "operador")

    respuesta = TestClient(api.app).get("/api/auditoria")

    assert respuesta.status_code == 403
    limpiar_autenticacion()


def test_auditoria_informa_error_de_base_de_datos(monkeypatch):
    api.app.dependency_overrides[api.requiere_administrador] = lambda: "admin"

    def falla():
        raise api.ErrorConsultaBaseDatos()

    monkeypatch.setattr(api, "listar_auditoria", falla)

    assert TestClient(api.app).get("/api/auditoria").status_code == 503
    limpiar_autenticacion()


def test_cuentas_requiere_administrador(monkeypatch):
    api.app.dependency_overrides[api.obtener_usuario_actual] = lambda: "operador"
    monkeypatch.setattr(api, "obtener_rol_cuenta", lambda _usuario: "operador")

    assert TestClient(api.app).get("/api/cuentas").status_code == 403
    limpiar_autenticacion()


def test_administrador_puede_listar_y_crear_cuentas(monkeypatch):
    api.app.dependency_overrides[api.requiere_administrador] = lambda: "admin"
    monkeypatch.setattr(api, "listar_cuentas", lambda: [{
        "usuario": "operador",
        "rol": "operador",
        "creado_en": "2026-10-15T12:00:00",
    }])
    creadas = []
    monkeypatch.setattr(api, "crear_cuenta_administrada", lambda *args: creadas.append(args) or True)

    cliente = TestClient(api.app)
    listado = cliente.get("/api/cuentas")
    creada = cliente.post("/api/cuentas", json={"usuario": "nuevo", "contrasena": "contrasena-segura", "rol": "operador"})

    assert listado.status_code == 200
    assert listado.json()[0]["usuario"] == "operador"
    assert creada.status_code == 201
    assert creadas[0][0] == "nuevo"
    assert creadas[0][2:] == ("operador", "admin")
    limpiar_autenticacion()


def test_crear_cuenta_rechaza_usuario_duplicado_y_contrasena_corta(monkeypatch):
    api.app.dependency_overrides[api.requiere_administrador] = lambda: "admin"
    monkeypatch.setattr(api, "crear_cuenta_administrada", lambda *_args: False)
    cliente = TestClient(api.app)

    duplicada = cliente.post("/api/cuentas", json={"usuario": "nuevo", "contrasena": "contrasena-segura"})
    corta = cliente.post("/api/cuentas", json={"usuario": "nuevo", "contrasena": "corta"})

    assert duplicada.status_code == 409
    assert corta.status_code == 422
    limpiar_autenticacion()


def test_administrador_puede_actualizar_otro_rol_pero_no_el_propio(monkeypatch):
    api.app.dependency_overrides[api.requiere_administrador] = lambda: "admin"
    cambios = []
    monkeypatch.setattr(api, "actualizar_rol_cuenta", lambda *args: cambios.append(args) or True)
    cliente = TestClient(api.app)

    actualizada = cliente.patch("/api/cuentas/operador", json={"rol": "administrador"})
    propia = cliente.patch("/api/cuentas/admin", json={"rol": "operador"})

    assert actualizada.status_code == 200
    assert cambios == [("operador", "administrador", "admin")]
    assert propia.status_code == 400
    limpiar_autenticacion()


def test_no_permite_dejar_sin_administradores(monkeypatch):
    api.app.dependency_overrides[api.requiere_administrador] = lambda: "admin"
    monkeypatch.setattr(api, "actualizar_rol_cuenta", lambda *_args: None)

    respuesta = TestClient(api.app).patch("/api/cuentas/otro-admin", json={"rol": "operador"})

    assert respuesta.status_code == 409
    limpiar_autenticacion()


def test_listar_conversaciones_devuelve_titulo_y_fecha(monkeypatch):
    monkeypatch.setattr(api, "listar_conversaciones", lambda _usuario: [{
        "id": 3,
        "titulo": "Consulta de stock",
        "actualizado_en": "2026-10-15T10:00:00",
    }])
    autenticar_como_admin()

    respuesta = TestClient(api.app).get("/api/conversaciones")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["titulo"] == "Consulta de stock"
    assert respuesta.json()[0]["actualizado_en"] == "2026-10-15T10:00:00"
    limpiar_autenticacion()


def test_abrir_conversacion_propia_devuelve_mensajes_en_orden(monkeypatch):
    monkeypatch.setattr(api, "obtener_mensajes_conversacion", lambda *_args: [
        {"rol": "user", "contenido": "Consulta inicial", "creado_en": "2026-10-15T10:00:00"},
        {"rol": "assistant", "contenido": "Respuesta", "creado_en": "2026-10-15T10:00:01"},
    ])
    autenticar_como_admin()

    respuesta = TestClient(api.app).get("/api/conversaciones/3")

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == 3
    assert [mensaje["rol"] for mensaje in respuesta.json()["mensajes"]] == ["user", "assistant"]
    limpiar_autenticacion()


def test_abrir_conversacion_ajena_devuelve_404(monkeypatch):
    monkeypatch.setattr(api, "obtener_mensajes_conversacion", lambda *_args: None)
    autenticar_como_admin()

    respuesta = TestClient(api.app).get("/api/conversaciones/9")

    assert respuesta.status_code == 404
    limpiar_autenticacion()


def test_abrir_conversacion_informa_error_de_base_de_datos(monkeypatch):
    def falla(*_args):
        raise api.ErrorConsultaBaseDatos()

    monkeypatch.setattr(api, "obtener_mensajes_conversacion", falla)
    autenticar_como_admin()

    assert TestClient(api.app).get("/api/conversaciones/3").status_code == 503
    limpiar_autenticacion()


def test_historial_visual_limita_a_cien_mensajes_y_respeta_el_orden(monkeypatch):
    consultas = []

    def consultar(_consulta, parametros=(), una_fila=False):
        consultas.append((parametros, una_fila))
        if una_fila:
            return {"id": 3}
        return [
            {"rol": "assistant", "contenido": "Mas reciente", "creado_en": "2026-10-15T10:00:01"},
            {"rol": "user", "contenido": "Primero", "creado_en": "2026-10-15T10:00:00"},
        ]

    monkeypatch.setattr(tools, "_ejecutar_consulta", consultar)

    mensajes = tools.obtener_mensajes_conversacion(3, "admin")

    assert consultas[1][0] == (3, 100)
    assert [mensaje["contenido"] for mensaje in mensajes] == ["Primero", "Mas reciente"]
