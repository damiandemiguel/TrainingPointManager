from datetime import date, timedelta

from database import conectar


def obtener_cumpleanos_proximos(hoy=None, dias=7):
    if hoy is None:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        hoy = datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ).date()

    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, nombre, fecha_nacimiento
            FROM alumnos
            WHERE activo = 1
              AND fecha_nacimiento IS NOT NULL
              AND TRIM(fecha_nacimiento) != ''
        """)

        cumpleanos = []

        for alumno_id, nombre, fecha_texto in cursor.fetchall():
            try:
                nacimiento = date.fromisoformat(fecha_texto)
            except (ValueError, TypeError):
                continue

            for diferencia in range(dias + 1):
                fecha = hoy + timedelta(days=diferencia)

                if (
                    nacimiento.month == fecha.month
                    and nacimiento.day == fecha.day
                ):
                    cumpleanos.append({
                        "alumno_id": alumno_id,
                        "nombre": nombre,
                        "fecha": fecha,
                        "dias_restantes": diferencia,
                        "edad": fecha.year - nacimiento.year,
                    })
                    break

        return sorted(
            cumpleanos,
            key=lambda alumno: (
                alumno["dias_restantes"],
                alumno["nombre"]
            )
        )

    finally:
        conexion.close()

def generar_saludos_cumpleanos(hoy=None):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    zona = ZoneInfo("America/Argentina/Buenos_Aires")

    if hoy is None:
        hoy = datetime.now(zona).date()

    fecha_envio = datetime.now(zona).strftime("%Y-%m-%d %H:%M:%S")

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, nombre, fecha_nacimiento
            FROM alumnos
            WHERE activo = 1
              AND fecha_nacimiento IS NOT NULL
              AND TRIM(fecha_nacimiento) != ''
        """)

        alumnos = cursor.fetchall()
        enviados = 0

        for alumno_id, nombre, fecha_texto in alumnos:
            try:
                nacimiento = date.fromisoformat(fecha_texto)
            except (ValueError, TypeError):
                continue

            if (nacimiento.month, nacimiento.day) != (hoy.month, hoy.day):
                continue

            cursor.execute("""
                SELECT 1
                FROM saludos_cumpleanos
                WHERE alumno_id = ? AND anio = ?
            """, (alumno_id, hoy.year))

            if cursor.fetchone():
                continue

            nombres = (nombre or "").strip().split()
            primer_nombre = nombres[0] if nombres else "campeón"

            titulo = f"🎉 ¡Feliz cumpleaños, {primer_nombre}!"

            mensaje = (
                f"¡Hoy es tu día, {primer_nombre}! 🎂💙 "
                "Desde Training Point queremos desearte un muy feliz "
                "cumpleaños. Gracias por formar parte de nuestra "
                "comunidad. ¡Que tengas un excelente día y sigamos "
                "entrenando juntos! 💪"
            )

            try:
                cursor.execute("""
                    INSERT INTO notificaciones (
                        alumno_id, titulo, mensaje, tipo,
                        fecha_creacion, activa
                    )
                    VALUES (?, ?, ?, 'Individual', ?, 1)
                """, (alumno_id, titulo, mensaje, fecha_envio))

                notificacion_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO saludos_cumpleanos (
                        alumno_id, anio, notificacion_id, fecha_envio
                    )
                    VALUES (?, ?, ?, ?)
                """, (alumno_id, hoy.year, notificacion_id, fecha_envio))

                conexion.commit()
                enviados += 1

            except Exception:
                conexion.rollback()
                raise

        return enviados

    finally:
        conexion.close()
