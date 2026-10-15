import hashlib
import hmac
import secrets


def validar_usuario(usuario):
    if not 1 <= len(usuario) <= 50:
        return "El usuario debe tener entre 1 y 50 caracteres."
    if not all(caracter.isalnum() or caracter in "_.-" for caracter in usuario):
        return "El usuario solo puede contener letras, numeros, puntos, guiones y guiones bajos."
    return None


def validar_contrasena(contrasena):
    if len(contrasena) < 10:
        return "La contrasena debe tener al menos 10 caracteres."
    return None


def cifrar_contrasena(contrasena):
    sal = secrets.token_hex(16)
    clave = hashlib.scrypt(
        contrasena.encode(), salt=sal.encode(), n=2**14, r=8, p=1
    ).hex()
    return f"{sal}${clave}"


def verificar_contrasena(contrasena, contrasena_cifrada):
    try:
        sal, clave_esperada = contrasena_cifrada.split("$", maxsplit=1)
        clave = hashlib.scrypt(
            contrasena.encode(), salt=sal.encode(), n=2**14, r=8, p=1
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(clave, clave_esperada)


def generar_token():
    return secrets.token_urlsafe(32)


def resumir_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
