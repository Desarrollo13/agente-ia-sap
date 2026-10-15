from getpass import getpass
import sys

from database import obtener_conexion
from mysql.connector import IntegrityError
from seguridad import cifrar_contrasena, validar_contrasena, validar_usuario


if len(sys.argv) != 2:
    raise SystemExit("Uso: python crear_cuenta.py <usuario>")

usuario = sys.argv[1]
error_usuario = validar_usuario(usuario)
if error_usuario:
    raise SystemExit(error_usuario)

contrasena = getpass("Contrasena: ")
confirmacion = getpass("Repetir contrasena: ")
if contrasena != confirmacion:
    raise SystemExit("Las contrasenas no coinciden.")
error_contrasena = validar_contrasena(contrasena)
if error_contrasena:
    raise SystemExit(error_contrasena)

contrasena_cifrada = cifrar_contrasena(contrasena)
conexion = obtener_conexion()
cursor = conexion.cursor()
try:
    cursor.execute("INSERT INTO cuentas (usuario, contrasena_cifrada) VALUES (%s, %s)", (usuario, contrasena_cifrada))
    conexion.commit()
except IntegrityError:
    raise SystemExit(f"La cuenta {usuario} ya existe.")
finally:
    cursor.close()
    conexion.close()

print(f"Cuenta creada para {usuario}.")
