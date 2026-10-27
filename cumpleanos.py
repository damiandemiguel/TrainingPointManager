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
