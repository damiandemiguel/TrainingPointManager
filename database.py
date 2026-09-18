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

def crear_tabla_clases():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            cupo_maximo INTEGER DEFAULT 30,
            estado TEXT DEFAULT 'Disponible'
        )
    """)

    conexion.commit()
    conexion.close()


def crear_tabla_inscripciones():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clase_id INTEGER NOT NULL,
            alumno_id INTEGER NOT NULL,
            fecha_inscripcion TEXT NOT NULL,
            estado TEXT DEFAULT 'Inscripto',
            FOREIGN KEY (clase_id) REFERENCES clases(id),
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id),
            UNIQUE (clase_id, alumno_id)
        )
    """)

    conexion.commit()
    conexion.close()


def crear_tabla_asistencias():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clase_id INTEGER NOT NULL,
            alumno_id INTEGER NOT NULL,
            bono_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            metodo TEXT NOT NULL,
            credito_descontado INTEGER DEFAULT 1,
            FOREIGN KEY (clase_id) REFERENCES clases(id),
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id),
            FOREIGN KEY (bono_id) REFERENCES bonos(id),
            UNIQUE (clase_id, alumno_id)
        )
    """)

    conexion.commit()
    conexion.close()

def crear_tabla_rutinas():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rutinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clase_id INTEGER NOT NULL UNIQUE,
            titulo TEXT,
            contenido TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            fecha_actualizacion TEXT,
            FOREIGN KEY (clase_id) REFERENCES clases(id)
        )
    """)

    conexion.commit()
    conexion.close()

def crear_tabla_notificaciones():
    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER,
            titulo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            tipo TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            activa INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id)
        )
    """)

    conexion.commit()
    conexion.close()

def crear_tabla_configuracion():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    valores_iniciales = [
        ("nombre_training_point", "Training Point"),
        ("telefono", ""),
        ("direccion", ""),
        ("instagram", "@trainingpoint._"),
        ("cupo_predeterminado", "30"),
        ("minutos_cancelacion", "10")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO configuracion (clave, valor)
        VALUES (?, ?)
    """, valores_iniciales)

    conexion.commit()
    conexion.close()


def crear_tabla_horarios_habituales():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS horarios_habituales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        SELECT COUNT(*)
        FROM horarios_habituales
    """)

    cantidad = cursor.fetchone()[0]

    if cantidad == 0:
        cursor.executemany("""
            INSERT INTO horarios_habituales (
                hora_inicio,
                hora_fin,
                activo
            )
            VALUES (?, ?, 1)
        """, [
            ("18:30", "19:30"),
            ("19:30", "20:30")
        ])

    conexion.commit()
    conexion.close()