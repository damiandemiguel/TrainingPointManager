import os
import sqlite3
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RUTA_DB = os.path.join(
    BASE_DIR,
    "trainingpoint.db"
)

CARPETA_BACKUPS = os.path.join(
    BASE_DIR,
    "backups"
)

MAX_BACKUPS = 10


def crear_backup():

    if not os.path.exists(RUTA_DB):
        print("ERROR: No se encontró la base de datos.")
        print(RUTA_DB)
        return

    os.makedirs(
        CARPETA_BACKUPS,
        exist_ok=True
    )

    fecha_hora = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    nombre_backup = (
        f"trainingpoint_{fecha_hora}.db"
    )

    ruta_backup = os.path.join(
        CARPETA_BACKUPS,
        nombre_backup
    )

    origen = None
    destino = None

    try:

        origen = sqlite3.connect(RUTA_DB)
        destino = sqlite3.connect(ruta_backup)

        origen.backup(destino)

        resultado = destino.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if resultado != "ok":
            raise RuntimeError(
                f"El backup no superó el control de integridad: {resultado}"
            )

        print(
            f"Backup creado correctamente: {ruta_backup}"
        )

        print(
            "Integridad del backup: ok"
        )

    except Exception as error:

        print(
            f"ERROR al crear el backup: {error}"
        )

        if os.path.exists(ruta_backup):
            os.remove(ruta_backup)

        return

    finally:

        if destino is not None:
            destino.close()

        if origen is not None:
            origen.close()

    eliminar_backups_antiguos()


def eliminar_backups_antiguos():

    archivos = []

    for nombre in os.listdir(CARPETA_BACKUPS):

        if (
            nombre.startswith("trainingpoint_")
            and nombre.endswith(".db")
        ):
            ruta = os.path.join(
                CARPETA_BACKUPS,
                nombre
            )

            archivos.append(ruta)

    archivos.sort(
        key=os.path.getmtime,
        reverse=True
    )

    for archivo in archivos[MAX_BACKUPS:]:

        try:
            os.remove(archivo)

            print(
                f"Backup antiguo eliminado: {os.path.basename(archivo)}"
            )

        except OSError as error:

            print(
                f"No se pudo eliminar {archivo}: {error}"
            )


if __name__ == "__main__":
    crear_backup()