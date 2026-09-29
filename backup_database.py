import os
import sqlite3
from datetime import datetime

from database import RUTA_DB


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_BACKUPS = os.path.join(
    BASE_DIR,
    "backups"
)


def crear_backup():

    os.makedirs(
        CARPETA_BACKUPS,
        exist_ok=True
    )

    fecha_hora = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    nombre_backup = (
        f"trainingpoint_backup_{fecha_hora}.db"
    )

    ruta_backup = os.path.join(
        CARPETA_BACKUPS,
        nombre_backup
    )

    origen = sqlite3.connect(RUTA_DB)
    destino = sqlite3.connect(ruta_backup)

    try:

        with destino:
            origen.backup(destino)

    finally:

        destino.close()
        origen.close()

    verificar_backup(ruta_backup)


def verificar_backup(ruta_backup):

    conexion = sqlite3.connect(ruta_backup)

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
    print("Backup creado correctamente:")
    print(ruta_backup)

    print()
    print("Integridad:", integridad)

    print()
    print("Tablas encontradas:")

    for tabla in tablas:
        print("-", tabla[0])


if __name__ == "__main__":
    crear_backup()