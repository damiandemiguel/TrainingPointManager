import sqlite3
from werkzeug.security import generate_password_hash


def conectar():
    conexion = sqlite3.connect("trainingpoint.db")
    return conexion


def crear_tabla_usuarios():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


def crear_usuario(usuario, password, rol):
    conexion = conectar()

    cursor = conexion.cursor()

    password_segura = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO usuarios (usuario, password, rol)
        VALUES (?, ?, ?)
    """, (usuario, password_segura, rol))

    conexion.commit()
    conexion.close()