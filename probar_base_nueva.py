import os
import sqlite3
import database


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RUTA_DB_REAL = database.RUTA_DB

RUTA_DB_PRUEBA = os.path.join(
    BASE_DIR,
    "prueba_base_nueva.db"
)


def probar_base_nueva():

    if os.path.exists(RUTA_DB_PRUEBA):
        os.remove(RUTA_DB_PRUEBA)

    database.RUTA_DB = RUTA_DB_PRUEBA

    try:

        database.crear_tabla_usuarios()
        database.crear_tabla_alumnos()
        database.crear_tabla_salud()
        database.crear_tabla_clases()
        database.crear_tabla_tipos_bono()
        database.crear_tabla_bonos()
        database.crear_tabla_movimientos_creditos()
        database.crear_tabla_inscripciones()
        database.crear_tabla_asistencias()
        database.crear_tabla_rutinas()
        database.crear_tabla_notificaciones()
        database.crear_tabla_configuracion()
        database.crear_tabla_horarios_habituales()

        conexion = sqlite3.connect(RUTA_DB_PRUEBA)

        try:

            integridad = conexion.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

            tablas = conexion.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()

        finally:

            conexion.close()

        print()
        print("BASE NUEVA CREADA CORRECTAMENTE")
        print()
        print("Integridad:", integridad)
        print()
        print("Tablas creadas:")

        for tabla in tablas:
            print("-", tabla[0])

    finally:

        database.RUTA_DB = RUTA_DB_REAL


if __name__ == "__main__":
    probar_base_nueva()