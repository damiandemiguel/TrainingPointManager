import sqlite3

from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from database import conectar


def buscar_abonos_por_vencer():
    fecha_objetivo = (
        datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ).date() + timedelta(days=3)
    ).isoformat()

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                b.id,
                a.nombre,
                a.email,
                b.fecha_vencimiento
            FROM bonos b
            INNER JOIN alumnos a
                ON a.id = b.alumno_id
            WHERE b.estado = 'Activo'
              AND a.activo = 1
              AND a.email IS NOT NULL
              AND TRIM(a.email) != ''
              AND b.fecha_vencimiento = ?
        """, (fecha_objetivo,))

        return cursor.fetchall()

    finally:
        conexion.close()


if __name__ == "__main__":
    abonos = buscar_abonos_por_vencer()

    print(
        "Abonos que vencen dentro de 3 días:",
        len(abonos)
    )

    for abono in abonos:
        print(
            f"Abono ID: {abono[0]} | "
            f"Vencimiento: {abono[3]} | "
            f"Destinatario identificado: Sí"
        )


def crear_mensaje_vencimiento(nombre, fecha_vencimiento):
    asunto = "Training Point - Tu abono está por vencer"

    contenido = f"""¡Hola, {nombre}! 👋

Te recordamos que tu abono de Training Point
vence el {fecha_vencimiento}.

Si querés continuar entrenando, podés comunicarte
con nosotros para renovar tu abono.

¡Nos vemos en la próxima clase! 💪

Training Point
"""

    return asunto, contenido

def recordatorio_ya_enviado(bono_id, fecha_vencimiento):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT 1
            FROM notificaciones_email
            WHERE bono_id = ?
              AND tipo_notificacion = 'vencimiento_abono'
              AND fecha_vencimiento = ?
              AND estado = 'Enviado'
            LIMIT 1
        """, (bono_id, fecha_vencimiento))

        return cursor.fetchone() is not None

    finally:
        conexion.close()

        from datetime import datetime
        from zoneinfo import ZoneInfo


def registrar_notificacion(
    bono_id,
    fecha_vencimiento,
    destinatario,
    estado
):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO notificaciones_email (
                bono_id,
                tipo_notificacion,
                fecha_vencimiento,
                destinatario,
                fecha_envio,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            bono_id,
            "vencimiento_abono",
            fecha_vencimiento,
            destinatario,
            datetime.now(
                ZoneInfo("America/Argentina/Buenos_Aires")
            ).isoformat(timespec="seconds"),
            estado
        ))

        conexion.commit()

        return cursor.lastrowid

    finally:
        conexion.close()

def reservar_recordatorio(
    bono_id,
    fecha_vencimiento,
    destinatario
):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO notificaciones_email (
                bono_id,
                tipo_notificacion,
                fecha_vencimiento,
                destinatario,
                fecha_envio,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            bono_id,
            "vencimiento_abono",
            fecha_vencimiento,
            destinatario,
            datetime.now(
                ZoneInfo("America/Argentina/Buenos_Aires")
            ).isoformat(timespec="seconds"),
            "Pendiente"
        ))

        conexion.commit()

        return cursor.rowcount == 1

    finally:
        conexion.close()

def actualizar_estado_recordatorio(
    bono_id,
    fecha_vencimiento,
    estado
):
    if estado not in ("Enviado", "Error"):
        raise ValueError("Estado no permitido")

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE notificaciones_email
            SET estado = ?
            WHERE bono_id = ?
              AND tipo_notificacion = 'vencimiento_abono'
              AND fecha_vencimiento = ?
              AND estado = 'Pendiente'
        """, (
            estado,
            bono_id,
            fecha_vencimiento
        ))

        conexion.commit()

        return cursor.rowcount == 1

    finally:
        conexion.close()

def reintentar_recordatorio(bono_id, fecha_vencimiento):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE notificaciones_email
            SET estado = 'Pendiente'
            WHERE bono_id = ?
              AND tipo_notificacion = 'vencimiento_abono'
              AND fecha_vencimiento = ?
              AND estado = 'Error'
        """, (
            bono_id,
            fecha_vencimiento
        ))

        conexion.commit()

        return cursor.rowcount == 1

    finally:
        conexion.close()

def notificacion_ya_registrada(bono_id, fecha_vencimiento):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT 1
            FROM notificaciones_email
            WHERE bono_id = ?
              AND tipo_notificacion = 'vencimiento_abono'
              AND fecha_vencimiento = ?
            LIMIT 1
        """, (
            bono_id,
            fecha_vencimiento
        ))

        return cursor.fetchone() is not None

    finally:
        conexion.close()

def preparar_recordatorios():
    abonos = buscar_abonos_por_vencer()

    recordatorios = []

    for bono_id, nombre, email, fecha_vencimiento in abonos:

        if notificacion_ya_registrada(
            bono_id,
            fecha_vencimiento
        ):
            continue

        fecha_formateada = date.fromisoformat(
            fecha_vencimiento
        ).strftime("%d/%m/%Y")

        asunto, mensaje = crear_mensaje_vencimiento(
            nombre,
            fecha_formateada
        )

        recordatorios.append({
            "bono_id": bono_id,
            "destinatario": email,
            "fecha_vencimiento": fecha_vencimiento,
            "asunto": asunto,
            "mensaje": mensaje
        })

    return recordatorios