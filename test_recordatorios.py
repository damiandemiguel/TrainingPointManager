import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from procesar_recordatorios import envio_real_de_prueba
from procesar_recordatorios import (
    procesar_recordatorios,
    envio_simulado
)

import database
from recordatorios_abonos import (
    reservar_recordatorio,
    preparar_recordatorios,
    actualizar_estado_recordatorio,
    reintentar_recordatorio
)


with tempfile.TemporaryDirectory() as carpeta:
    ruta_temporal = Path(carpeta) / "prueba.db"

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
        VALUES (1, 'Alumno Prueba', 'prueba@example.com', 1)
    """)

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

    def envio_exitoso_ficticio(destinatario, asunto, mensaje):
        print(
            f"[PRUEBA] Envío ficticio a: {destinatario}"
        )
        return True

    with patch.object(database, "RUTA_DB", ruta_temporal):

        print("=== PRUEBA DE RESERVAS ===")

        primera_reserva = reservar_recordatorio(
            1,
            fecha_vencimiento,
            "prueba@example.com"
        )

        segunda_reserva = reservar_recordatorio(
            1,
            fecha_vencimiento,
            "prueba@example.com"
        )

        print("Primera reserva:", primera_reserva)
        print("Segunda reserva:", segunda_reserva)

        conexion = database.conectar()

        registros = conexion.execute("""
            SELECT bono_id, estado
            FROM notificaciones_email
        """).fetchall()

        conexion.close()

        print("Registros guardados:", registros)

        print("\n=== PRUEBA DE ACTUALIZACIÓN ===")

        actualizado = actualizar_estado_recordatorio(
            1,
            fecha_vencimiento,
            "Enviado"
        )

        print("Estado actualizado:", actualizado)

        conexion = database.conectar()

        estado_actual = conexion.execute("""
            SELECT estado
            FROM notificaciones_email
            WHERE bono_id = 1
        """).fetchone()

        conexion.close()

        print("Estado en la base de datos:", estado_actual)

        print("\n=== PRUEBA DE RECORDATORIOS ===")

        recordatorios = preparar_recordatorios()

        print("Recordatorios preparados:", len(recordatorios))

        print("\n=== PRUEBA DE ERROR ===")

        # Creamos otro bono ficticio en la base temporal.
        conexion = database.conectar()

        conexion.execute("""
            INSERT INTO bonos (
                id, alumno_id, tipo_bono_id,
                fecha_inicio, fecha_vencimiento,
                creditos_iniciales, creditos_disponibles,
                precio, forma_pago, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
    2, 1, 1,
    date.today().isoformat(),
    fecha_vencimiento,
    8, 8, 40000,
    "Efectivo", "Activo"
))

        conexion.commit()
        conexion.close()

        reserva_error = reservar_recordatorio(
            2,
            fecha_vencimiento,
            "prueba@example.com"
        )

        actualizacion_error = actualizar_estado_recordatorio(
            2,
            fecha_vencimiento,
            "Error"
        )

        conexion = database.conectar()

        estado_error = conexion.execute("""
            SELECT estado
            FROM notificaciones_email
            WHERE bono_id = 2
        """).fetchone()

        conexion.close()

        print("Reserva creada:", reserva_error)
        print("Actualización a Error:", actualizacion_error)
        print("Estado guardado:", estado_error)

        print("\n=== PRUEBA DE REINTENTOS ===")

        # Bono 2: actualmente está en estado Error.
        primer_reintento = reintentar_recordatorio(
            2,
            fecha_vencimiento
        )

        # Intentamos reservar nuevamente el mismo reintento.
        segundo_reintento = reintentar_recordatorio(
            2,
            fecha_vencimiento
        )

        # Bono 1: ya está Enviado, por lo que no debe reintentarse.
        reintento_enviado = reintentar_recordatorio(
            1,
            fecha_vencimiento
        )

        conexion = database.conectar()

        estados = conexion.execute("""
            SELECT bono_id, estado
            FROM notificaciones_email
            ORDER BY bono_id
        """).fetchall()

        conexion.close()

        print("Primer reintento del bono 2:", primer_reintento)
        print("Segundo reintento del bono 2:", segundo_reintento)
        print("Reintento del bono 1 enviado:", reintento_enviado)
        print("Estados finales:", estados)

        assert primer_reintento is True
        assert segundo_reintento is False
        assert reintento_enviado is False
        assert estados == [(1, "Enviado"), (2, "Pendiente")]

        print("\n=== PRUEBA DEL PROCESADOR ===")

        procesar_recordatorios(simulacion=True)

        print("\n=== PRUEBA DE BONO NUEVO ===")

        conexion = database.conectar()

        conexion.execute("""
            INSERT INTO bonos (
                id, alumno_id, tipo_bono_id,
                fecha_inicio, fecha_vencimiento,
                creditos_iniciales, creditos_disponibles,
                precio, forma_pago, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            3, 1, 1,
            date.today().isoformat(),
            fecha_vencimiento,
            8, 8, 40000,
            "Efectivo", "Activo"
        ))

        conexion.commit()
        conexion.close()

        recordatorios_nuevos = preparar_recordatorios()

        print("Recordatorios nuevos:", len(recordatorios_nuevos))

        if recordatorios_nuevos:
            print(
                "Bono detectado:",
                recordatorios_nuevos[0]["bono_id"]
            )

        assert len(recordatorios_nuevos) == 1
        assert recordatorios_nuevos[0]["bono_id"] == 3

        procesar_recordatorios(simulacion=True)

        print("\n=== PRUEBA DE ENVÍO SIMULADO ===")

        procesar_recordatorios(
            simulacion=False,
            funcion_envio=envio_exitoso_ficticio
        )

        conexion = database.conectar()

        estado_bono_3 = conexion.execute("""
            SELECT estado
            FROM notificaciones_email
            WHERE bono_id = 3
        """).fetchone()

        conexion.close()

        print("Estado final del bono 3:", estado_bono_3)

        assert estado_bono_3 == ("Enviado",)

        print("\n=== PRUEBA CONTRA SEGUNDO ENVÍO ===")

        procesar_recordatorios(
                simulacion=False,
            funcion_envio=envio_exitoso_ficticio
        )

        print("\n=== PRUEBA DE ENVÍO FALLIDO ===")

        conexion = database.conectar()

        conexion.execute("""
            INSERT INTO bonos (
                id, alumno_id, tipo_bono_id,
                fecha_inicio, fecha_vencimiento,
                creditos_iniciales, creditos_disponibles,
                precio, forma_pago, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            4, 1, 1,
            date.today().isoformat(),
            fecha_vencimiento,
            8, 8, 40000,
            "Efectivo", "Activo"
        ))

        conexion.commit()
        conexion.close()


        def envio_fallido(destinatario, asunto, mensaje):
            print("[SIMULACIÓN] El envío no fue confirmado")
            return False


        procesar_recordatorios(
            simulacion=False,
            funcion_envio=envio_fallido
        )

        conexion = database.conectar()

        estado_bono_4 = conexion.execute("""
            SELECT estado
            FROM notificaciones_email
            WHERE bono_id = 4
        """).fetchone()

        conexion.close()

        print("Estado final del bono 4:", estado_bono_4)

        assert estado_bono_4 == ("Pendiente",)

        print("\n=== SEGUNDO INTENTO TRAS FALLO ===")

        procesar_recordatorios(
            simulacion=False,
            funcion_envio=envio_fallido
        )

        print("\n=== PRUEBA DE BLOQUEO DE DESTINATARIO ===")

        resultado_bloqueo = envio_real_de_prueba(
            "prueba@example.com",
            "Prueba de seguridad",
            "Este mensaje no debe enviarse."
        )

        print("Resultado del intento:", resultado_bloqueo)

        assert resultado_bloqueo is False

        if recordatorios:
            print("Asunto:", recordatorios[0]["asunto"])
            print("Mensaje:\n", recordatorios[0]["mensaje"])