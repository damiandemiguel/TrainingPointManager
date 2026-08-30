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

def crear_tabla_tipos_bono():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_bono (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            creditos INTEGER NOT NULL,
            precio REAL NOT NULL,
            duracion_dias INTEGER,
            activo INTEGER DEFAULT 1
        )
    """)

    conexion.commit()
    conexion.close()


def crear_tabla_bonos():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER NOT NULL,
            tipo_bono_id INTEGER NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_vencimiento_original TEXT,
            fecha_vencimiento TEXT,
            creditos_iniciales INTEGER NOT NULL,
            creditos_disponibles INTEGER NOT NULL,
            precio REAL NOT NULL,
            forma_pago TEXT NOT NULL,
            fecha_pago TEXT,
            extension_dias INTEGER DEFAULT 0,
            motivo_extension TEXT,
            estado TEXT DEFAULT 'Activo',
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id),
            FOREIGN KEY (tipo_bono_id) REFERENCES tipos_bono(id)
        )
    """)

    conexion.commit()
    conexion.close()


def crear_tabla_movimientos_creditos():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_creditos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bono_id INTEGER NOT NULL,
            alumno_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            descripcion TEXT,
            FOREIGN KEY (bono_id) REFERENCES bonos(id),
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
        )
    """)

    conexion.commit()
    conexion.close()