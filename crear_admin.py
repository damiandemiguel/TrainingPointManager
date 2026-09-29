from getpass import getpass
import sqlite3

from database import (
    conectar,
    crear_tabla_usuarios,
    crear_usuario
)


def crear_administrador():

    crear_tabla_usuarios()

    print()
    print("=== CREAR ADMINISTRADOR DE TRAINING POINT ===")
    print()

    usuario = input(
        "Usuario del administrador: "
    ).strip()

    if not usuario:
        print("El usuario no puede estar vacío.")
        return

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM usuarios
        WHERE usuario = ?
    """, (usuario,))

    usuario_existente = cursor.fetchone()

    conexion.close()

    if usuario_existente:
        print()
        print(
            "Ya existe un usuario con ese nombre."
        )
        return

    password = getpass(
        "Contraseña: "
    )

    confirmar_password = getpass(
        "Repetir contraseña: "
    )

    if not password:
        print()
        print(
            "La contraseña no puede estar vacía."
        )
        return

    if password != confirmar_password:
        print()
        print(
            "Las contraseñas no coinciden."
        )
        return

    try:

        crear_usuario(
            usuario,
            password,
            "administrador"
        )

    except sqlite3.IntegrityError:

        print()
        print(
            "No se pudo crear el administrador "
            "porque el usuario ya existe."
        )
        return

    print()
    print(
        "Administrador creado correctamente."
    )


if __name__ == "__main__":
    crear_administrador()