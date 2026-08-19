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


def crear_tabla_alumnos():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            nombre TEXT NOT NULL,
            email TEXT,
            fecha_nacimiento TEXT,
            telefono TEXT,
            direccion TEXT,
            certificado_medico TEXT,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conexion.commit()
    conexion.close()

def crear_alumno(usuario_id, nombre, email, fecha_nacimiento, telefono, direccion):
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO alumnos (
            usuario_id,
            nombre,
            email,
            fecha_nacimiento,
            telefono,
            direccion
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        usuario_id,
        nombre,
        email,
        fecha_nacimiento,
        telefono,
        direccion
    ))

    conexion.commit()
    conexion.close()