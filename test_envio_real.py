import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import database

from procesar_recordatorios import (
    procesar_recordatorios,
    envio_real_de_prueba
)


def ejecutar_prueba():
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_temporal = Path(carpeta) / "prueba_envio.db"

        fecha_vencimiento = (
            date.today() + timedelta(days=3)
        ).isoformat()

        conexion = sqlite3.connect(ruta_temporal)

        conexion.executescript("""
            CREATE TABLE alumnos (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                email TEXT,
                activo INTEGER DEFAULT 1
            );

            CREATE TABLE bonos (
                id INTEGER PRIMARY KEY,
                alumno_id INTEGER NOT NULL,
                tipo_bono_id INTEGER NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_vencimiento TEXT,
                creditos_iniciales INTEGER NOT NULL,
                creditos_disponibles INTEGER NOT NULL,
                precio REAL NOT NULL,
                forma_pago TEXT NOT NULL,
                estado TEXT DEFAULT 'Activo'
            );

            CREATE TABLE notificaciones_email (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bono_id INTEGER NOT NULL,
                tipo_notificacion TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                destinatario TEXT NOT NULL,
                fecha_envio TEXT NOT NULL,
                estado TEXT NOT NULL,
                UNIQUE (
                    bono_id,
                    tipo_notificacion,
                    fecha_vencimiento
                )
            );
        """)

        conexion.execute("""
            INSERT INTO alumnos (id, nombre, email, activo)
            VALUES (?, ?, ?, ?)
        """, (
            1,
            "Alumno Prueba",
            "trainingpoint.ef@gmail.com",
            1
        ))

        conexion.execute("""
            INSERT INTO bonos (
                id, alumno_id, tipo_bono_id,
                fecha_inicio, fecha_vencimiento,
                creditos_iniciales, creditos_disponibles,
                precio, forma_pago, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1, 1, 1,
            date.today().isoformat(),
            fecha_vencimiento,
            8, 8, 40000,
            "Efectivo", "Activo"
        ))

        conexion.commit()
        conexion.close()

        with patch.object(database, "RUTA_DB", ruta_temporal):
            print("=== PRUEBA REAL CONTROLADA ===")

            procesar_recordatorios(
                simulacion=False,
                funcion_envio=envio_real_de_prueba
            )

            conexion = database.conectar()

            estado = conexion.execute("""
                SELECT estado
                FROM notificaciones_email
                WHERE bono_id = 1
            """).fetchone()

            conexion.close()

            print("Estado final:", estado)

            print("\n=== SEGUNDA EJECUCIÓN ===")

            procesar_recordatorios(
                simulacion=False,
                funcion_envio=envio_real_de_prueba
            )


if __name__ == "__main__":
    ejecutar_prueba()