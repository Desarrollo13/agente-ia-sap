from seguridad import (
    cifrar_contrasena,
    generar_token,
    resumir_token,
    validar_contrasena,
    validar_usuario,
    verificar_contrasena,
)


def test_verificar_contrasena_acepta_solo_la_contrasena_original():
    contrasena_cifrada = cifrar_contrasena("contrasena-segura")

    assert verificar_contrasena("contrasena-segura", contrasena_cifrada)
    assert not verificar_contrasena("otra-contrasena", contrasena_cifrada)


def test_resumir_token_no_devuelve_el_token_original():
    token = generar_token()

    assert resumir_token(token) != token
    assert len(resumir_token(token)) == 64


def test_validar_datos_de_cuenta():
    assert validar_usuario("operador.planta-1") is None
    assert validar_usuario("operador invalido")
    assert validar_contrasena("contrasena-larga") is None
    assert validar_contrasena("corta")
