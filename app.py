from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta

from database import (
    conectar,
    crear_tabla_tipos_bono,
    crear_tabla_bonos,
    crear_tabla_movimientos_creditos,
    crear_tabla_inscripciones,
    crear_tabla_asistencias,
    crear_tabla_rutinas,
    crear_tabla_notificaciones,
    crear_tabla_configuracion,
    crear_tabla_horarios_habituales
)

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads/perfiles"
CERTIFICADOS_FOLDER = "static/uploads/certificados"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CERTIFICADOS_FOLDER"] = CERTIFICADOS_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_CERTIFICADO_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

app.secret_key = "clave-temporal-training-point"

@app.template_filter("fecha_ar")
def fecha_ar(fecha):

    if not fecha:
        return ""

    try:
        fecha_convertida = datetime.strptime(
            fecha,
            "%Y-%m-%d"
        )

        return fecha_convertida.strftime("%d/%m/%Y")

    except (ValueError, TypeError):
        return fecha

def calcular_vencimiento_bono(fecha_inicio, cantidad_clases):

    fecha = datetime.strptime(
        fecha_inicio,
        "%Y-%m-%d"
    )

    clases_contadas = 0

    while clases_contadas < cantidad_clases:

        # 0 = lunes
        # 2 = miércoles
        # 4 = viernes

        if fecha.weekday() in [0, 2, 4]:
            clases_contadas += 1

            if clases_contadas == cantidad_clases:
                return fecha.strftime("%Y-%m-%d")

        fecha += timedelta(days=1)

    return fecha.strftime("%Y-%m-%d")

crear_tabla_tipos_bono()
crear_tabla_bonos()
crear_tabla_movimientos_creditos()
crear_tabla_inscripciones()
crear_tabla_asistencias()
crear_tabla_rutinas()
crear_tabla_notificaciones()
crear_tabla_configuracion()
crear_tabla_horarios_habituales()

def archivo_permitido(nombre):

    return (
        "." in nombre
        and nombre.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def certificado_permitido(nombre):

    return (
        "." in nombre
        and nombre.rsplit(".", 1)[1].lower() in ALLOWED_CERTIFICADO_EXTENSIONS
    )


def fecha_vencida(fecha):

    if not fecha:
        return True

    try:
        fecha_dt = datetime.strptime(fecha[:10], "%Y-%m-%d").date()
        hoy = datetime.now().date()

        try:
            fecha_vencimiento = fecha_dt.replace(
                year=fecha_dt.year + 1
            )
        except ValueError:
            fecha_vencimiento = fecha_dt.replace(
                year=fecha_dt.year + 1,
                day=28
            )

        return hoy >= fecha_vencimiento

    except ValueError:
        return True


@app.route("/", methods=["GET", "POST"])
def inicio():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, usuario, password, rol
            FROM usuarios
            WHERE usuario = ?
        """, (usuario,))

        usuario_encontrado = cursor.fetchone()

        conexion.close()

        if usuario_encontrado:

            id_usuario = usuario_encontrado[0]
            nombre_usuario = usuario_encontrado[1]
            password_guardada = usuario_encontrado[2]
            rol = usuario_encontrado[3]

            if check_password_hash(password_guardada, password):

                session["usuario_id"] = id_usuario
                session["usuario"] = nombre_usuario
                session["rol"] = rol

                return redirect(url_for("panel"))

        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos."
        )

    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form["nombre"]
        email = request.form["email"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        telefono = request.form["telefono"]
        direccion = request.form["direccion"]
        usuario = request.form["usuario"]
        password = request.form["password"]
        confirmar_password = request.form["confirmar_password"]

        if password != confirmar_password:
            return render_template(
                "registro.html",
                error="Las contraseñas no coinciden.",
                datos=request.form
            )

        conexion = conectar()
        cursor = conexion.cursor()

        try:

            # Crear usuario
            password_segura = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO usuarios (usuario, password, rol)
                VALUES (?, ?, ?)
            """, (
                usuario,
                password_segura,
                "alumno"
            ))

            usuario_id = cursor.lastrowid

            # Crear perfil del alumno
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

        except Exception as error:

            conexion.rollback()
            conexion.close()

            return f"Error al crear la cuenta: {error}"

        conexion.close()

        return redirect(url_for("inicio"))

    return render_template("registro.html")

@app.route("/panel")
def panel():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] == "administrador":

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) FROM alumnos")
        total_alumnos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alumnos WHERE activo = 1")
        alumnos_activos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alumnos WHERE activo = 0")
        alumnos_inactivos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM salud")
        fichas_salud = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM alumnos
            WHERE certificado_medico IS NULL
                OR certificado_medico = ''
        """)
        alumnos_sin_certificado = cursor.fetchone()[0]

        cursor.execute("""
            SELECT fecha_certificado
            FROM alumnos
            WHERE certificado_medico IS NOT NULL
                AND certificado_medico != ''
        """)

        certificados = cursor.fetchall()

        certificados_vigentes = 0
        certificados_vencidos = 0

        for certificado in certificados:

            if fecha_vencida(certificado[0]):
                certificados_vencidos += 1
            else:
                certificados_vigentes += 1


        cursor.execute("""
            SELECT COUNT(*)
            FROM alumnos
            LEFT JOIN salud
                ON alumnos.id = salud.alumno_id
            WHERE salud.id IS NULL
        """)
        alumnos_sin_ficha = cursor.fetchone()[0]

        cursor.execute("""
            SELECT fecha_certificado
            FROM alumnos
            WHERE certificado_medico IS NOT NULL
                AND certificado_medico != ''
        """)

        certificados = cursor.fetchall()

        certificados_vigentes = 0
        certificados_vencidos = 0

        for certificado in certificados:

            fecha = certificado[0]

            if fecha_vencida(fecha):
                certificados_vencidos += 1
            else:
                certificados_vigentes += 1

        conexion.close()

        return render_template(
            "admin.html",
            total_alumnos=total_alumnos,
            alumnos_activos=alumnos_activos,
            alumnos_inactivos=alumnos_inactivos,
            fichas_salud=fichas_salud,
            alumnos_sin_certificado=alumnos_sin_certificado,
            alumnos_sin_ficha=alumnos_sin_ficha,
            certificados_vigentes=certificados_vigentes,
            certificados_vencidos=certificados_vencidos
        )

    return redirect(url_for("panel_alumno"))

@app.route("/panel-alumno")
def panel_alumno():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    return render_template("panel_alumno.html")

@app.route("/notificaciones")
def notificaciones_alumno():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno correspondiente al usuario
    cursor.execute("""
        SELECT
            id,
            nombre,
            fecha_certificado
        FROM alumnos
        WHERE usuario_id = ?
          AND activo = 1
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    # Notificaciones manuales:
    # generales + individuales destinadas a este alumno
    cursor.execute("""
        SELECT *
        FROM notificaciones
        WHERE activa = 1
          AND (
                tipo = 'General'
                OR (
                    tipo = 'Individual'
                    AND alumno_id = ?
                )
              )
        ORDER BY fecha_creacion DESC
    """, (alumno["id"],))

    notificaciones = cursor.fetchall()

    avisos_automaticos = []

    hoy = datetime.now().date()

    # Aviso automático de abono próximo a vencer
    cursor.execute("""
        SELECT
            fecha_vencimiento,
            creditos_disponibles,
            creditos_ilimitados
        FROM bonos
        WHERE alumno_id = ?
          AND estado = 'Activo'
        ORDER BY fecha_vencimiento ASC
        LIMIT 1
    """, (alumno["id"],))

    bono = cursor.fetchone()

    if bono and bono["fecha_vencimiento"]:

        fecha_vencimiento = datetime.strptime(
            bono["fecha_vencimiento"],
            "%Y-%m-%d"
        ).date()

        dias_para_vencer = (fecha_vencimiento - hoy).days

        if (
            (
                bono["creditos_disponibles"] > 0
                or bono["creditos_ilimitados"] == 1
            )
            and 1 <= dias_para_vencer <= 7
        ):

            avisos_automaticos.append({
                "tipo": "Abono",
                "titulo": "Tu abono vence próximamente",
                "mensaje": (
                    f"Tu abono vence el "
                    f"{fecha_vencimiento.strftime('%d/%m/%Y')}. "
                    f"Te quedan {dias_para_vencer} días."
                )
            })

    # Aviso automático de certificado médico vencido
    if alumno["fecha_certificado"] and fecha_vencida(
        alumno["fecha_certificado"]
    ):

        avisos_automaticos.append({
            "tipo": "Certificado",
            "titulo": "Certificado médico vencido",
            "mensaje": (
                "Tu certificado médico se encuentra vencido. "
                "Recordá presentar uno actualizado."
            )
        })

    conexion.close()

    return render_template(
        "notificaciones_alumno.html",
        notificaciones=notificaciones,
        avisos_automaticos=avisos_automaticos
    )

@app.route("/rutinas")
def rutinas_alumno():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    hoy = datetime.now().date()
    fecha_limite = hoy + timedelta(days=30)

    cursor.execute("""
        SELECT
            clases.id,
            clases.fecha,
            clases.hora_inicio,
            clases.hora_fin,
            rutinas.id AS rutina_id,
            rutinas.titulo,
            rutinas.contenido
        FROM clases
        LEFT JOIN rutinas
            ON rutinas.clase_id = clases.id
        WHERE clases.fecha BETWEEN ? AND ?
        ORDER BY clases.fecha ASC, clases.hora_inicio ASC
    """, (
        hoy.strftime("%Y-%m-%d"),
        fecha_limite.strftime("%Y-%m-%d")
    ))

    clases = cursor.fetchall()

    conexion.close()

    return render_template(
        "rutinas_alumno.html",
        clases=clases
    )

@app.route("/mi-cuenta", methods=["GET", "POST"])
def mi_cuenta():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, usuario, password, rol
        FROM usuarios
        WHERE id = ?
    """, (session["usuario_id"],))

    usuario = cursor.fetchone()

    if usuario is None:
        conexion.close()
        session.clear()
        return redirect(url_for("inicio"))

    mensaje = None
    error = None

    if request.method == "POST":

        password_actual = request.form.get("password_actual", "")
        password_nueva = request.form.get("password_nueva", "")
        confirmar_password = request.form.get("confirmar_password", "")

        if not check_password_hash(
            usuario["password"],
            password_actual
        ):
            error = "La contraseña actual no es correcta."

        elif len(password_nueva) < 6:
            error = "La nueva contraseña debe tener al menos 6 caracteres."

        elif password_nueva != confirmar_password:
            error = "Las nuevas contraseñas no coinciden."

        else:
            password_segura = generate_password_hash(password_nueva)

            cursor.execute("""
                UPDATE usuarios
                SET password = ?
                WHERE id = ?
            """, (
                password_segura,
                session["usuario_id"]
            ))

            conexion.commit()

            mensaje = "Contraseña actualizada correctamente."

            # Actualizamos el dato leído para mantener
            # la información de la cuenta consistente.
            cursor.execute("""
                SELECT id, usuario, password, rol
                FROM usuarios
                WHERE id = ?
            """, (session["usuario_id"],))

            usuario = cursor.fetchone()

    conexion.close()

    return render_template(
        "mi_cuenta.html",
        usuario=usuario,
        mensaje=mensaje,
        error=error
    )

@app.route("/cerrar-sesion")
def cerrar_sesion():

    session.clear()

    return redirect(url_for("inicio"))

@app.route("/clases")
def gestionar_clases():

    clases_creadas = request.args.get("creadas", type=int)
    clases_omitidas = request.args.get("omitidas", type=int)

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    hoy = datetime.now().date()

    fecha_inicio = hoy.replace(day=1)
    fecha_limite = hoy + timedelta(days=30)

    cursor.execute("""
        SELECT
            clases.*,
            COUNT(inscripciones.id) AS cantidad_inscriptos
        FROM clases
        LEFT JOIN inscripciones
            ON clases.id = inscripciones.clase_id
            AND inscripciones.estado = 'Inscripto'
        WHERE clases.fecha BETWEEN ? AND ?
        GROUP BY clases.id
        ORDER BY clases.fecha ASC, clases.hora_inicio ASC
    """, (
        fecha_inicio.strftime("%Y-%m-%d"),
        fecha_limite.strftime("%Y-%m-%d")
    ))

    clases = cursor.fetchall()

    clases_por_fecha = {}

    for clase in clases:
        fecha_clase = clase["fecha"]

        if fecha_clase not in clases_por_fecha:
            clases_por_fecha[fecha_clase] = []

        clases_por_fecha[fecha_clase].append(clase)

    nombres_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo"
    ]

    semanas = []

    inicio_calendario = fecha_inicio - timedelta(days=fecha_inicio.weekday())
    inicio = inicio_calendario

    while inicio <= fecha_limite:

        dias = []

        for numero_dia in range(7):

            fecha_dia = inicio + timedelta(days=numero_dia)
            fecha_texto = fecha_dia.strftime("%Y-%m-%d")

            dias.append({
                "nombre": nombres_dias[numero_dia],
                "fecha": fecha_dia,
                "fecha_texto": fecha_texto,
                "clases": clases_por_fecha.get(fecha_texto, [])
            })

        semanas.append({
            "inicio": inicio,
            "fin": inicio + timedelta(days=6),
            "dias": dias
        })

        inicio = inicio + timedelta(days=7)

    conexion.close()

    return render_template(
        "clases_admin.html",
        clases=clases,
        semanas=semanas,
        hoy=hoy,
        fecha_limite=fecha_limite,
        clases_creadas=clases_creadas,
        clases_omitidas=clases_omitidas
    )

@app.route("/clases/nueva", methods=["GET", "POST"])
def nueva_clase():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    if request.method == "POST":

        modo = request.form["modo"]

        hora_inicio = request.form["hora_inicio"]
        hora_fin = request.form["hora_fin"]
        cupo_maximo = int(request.form["cupo_maximo"])

        conexion = conectar()
        cursor = conexion.cursor()

        try:

            clases_creadas = 0
            clases_omitidas = 0

            if modo == "individual":

                fecha = request.form["fecha"]

                cursor.execute("""
                    SELECT id
                    FROM clases
                    WHERE fecha = ?
                      AND hora_inicio = ?
                """, (
                    fecha,
                    hora_inicio
                ))

                clase_existente = cursor.fetchone()

                if clase_existente:

                    conexion.close()

                    return (
                        "Ya existe una clase para esa fecha y horario. "
                        "<br><br>"
                        "<a href='/clases/nueva'>Volver</a>"
                    )

                cursor.execute("""
                    INSERT INTO clases (
                        fecha,
                        hora_inicio,
                        hora_fin,
                        cupo_maximo,
                        estado
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    fecha,
                    hora_inicio,
                    hora_fin,
                    cupo_maximo,
                    "Disponible"
                ))

                clases_creadas += 1

            elif modo == "recurrente":

                from datetime import datetime, timedelta

                fecha_desde = datetime.strptime(
                    request.form["fecha_desde"],
                    "%Y-%m-%d"
                ).date()

                fecha_hasta = datetime.strptime(
                    request.form["fecha_hasta"],
                    "%Y-%m-%d"
                ).date()

                dias = request.form.getlist("dias")

                if fecha_desde > fecha_hasta:
                    conexion.close()
                    return "La fecha de inicio no puede ser posterior a la fecha de finalización."

                if not dias:
                    conexion.close()
                    return "Debés seleccionar al menos un día de la semana."

                dias = [int(dia) for dia in dias]

                fecha_actual = fecha_desde

                while fecha_actual <= fecha_hasta:

                    if fecha_actual.weekday() in dias:

                        fecha_texto = fecha_actual.strftime("%Y-%m-%d")

                        cursor.execute("""
                            SELECT id
                            FROM clases
                            WHERE fecha = ?
                              AND hora_inicio = ?
                        """, (
                            fecha_texto,
                            hora_inicio
                        ))

                        clase_existente = cursor.fetchone()

                        if clase_existente:

                            clases_omitidas += 1

                        else:

                            cursor.execute("""
                                INSERT INTO clases (
                                    fecha,
                                    hora_inicio,
                                    hora_fin,
                                    cupo_maximo,
                                    estado
                                )
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                fecha_texto,
                                hora_inicio,
                                hora_fin,
                                cupo_maximo,
                                "Disponible"
                            ))

                            clases_creadas += 1

                    fecha_actual += timedelta(days=1)

            conexion.commit()

        except Exception as error:

            conexion.rollback()
            conexion.close()

            return f"Error al crear la clase: {error}"

        conexion.close()

        return redirect(
            url_for(
                "gestionar_clases",
                creadas=clases_creadas,
                omitidas=clases_omitidas
            )
        )

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT valor
        FROM configuracion
        WHERE clave = 'cupo_predeterminado'
    """)

    fila = cursor.fetchone()

    conexion.close()

    cupo_predeterminado = 30

    if fila is not None:
        try:
            cupo_predeterminado = int(fila["valor"])
        except (ValueError, TypeError):
            cupo_predeterminado = 30

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, hora_inicio, hora_fin
        FROM horarios_habituales
        WHERE activo = 1
        ORDER BY hora_inicio ASC
    """)

    horarios_habituales = cursor.fetchall()

    conexion.close()       

    return render_template(
        "nueva_clase_admin.html",
        cupo_predeterminado=cupo_predeterminado,
        horarios_habituales=horarios_habituales
    )

@app.route("/clases/<int:clase_id>/editar", methods=["GET", "POST"])
def editar_clase(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "No se encontró la clase."

    if request.method == "POST":

        fecha = request.form["fecha"]
        hora_inicio = request.form["hora_inicio"]
        hora_fin = request.form["hora_fin"]
        cupo_maximo = int(request.form["cupo_maximo"])
        estado = request.form["estado"]

        cursor.execute("""
            UPDATE clases
            SET fecha = ?,
                hora_inicio = ?,
                hora_fin = ?,
                cupo_maximo = ?,
                estado = ?
            WHERE id = ?
        """, (
            fecha,
            hora_inicio,
            hora_fin,
            cupo_maximo,
            estado,
            clase_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("gestionar_clases"))

    conexion.close()

    return render_template(
        "editar_clase_admin.html",
        clase=clase
    )

@app.route("/clases/<int:clase_id>/eliminar", methods=["POST"])
def eliminar_clase(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM clases
        WHERE id = ?
    """, (clase_id,))

    conexion.commit()
    conexion.close()

    return redirect(url_for("gestionar_clases"))


@app.route("/clases/<int:clase_id>/inscriptos")
def ver_inscriptos(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "No se encontró la clase."

    cursor.execute("""
        SELECT
            inscripciones.id,
            inscripciones.fecha_inscripcion,
            inscripciones.estado,
            alumnos.id AS alumno_id,
            alumnos.nombre,
            alumnos.email
        FROM inscripciones
        INNER JOIN alumnos
            ON inscripciones.alumno_id = alumnos.id
        WHERE inscripciones.clase_id = ?
          AND inscripciones.estado = 'Inscripto'
        ORDER BY alumnos.nombre ASC
    """, (clase_id,))

    inscriptos = cursor.fetchall()

    conexion.close()

    return render_template(
        "inscriptos_clase_admin.html",
        clase=clase,
        inscriptos=inscriptos
    )

@app.route("/clases/<int:clase_id>/inscriptos/<int:inscripcion_id>/cancelar", methods=["POST"])
def cancelar_inscripcion_admin(clase_id, inscripcion_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM inscripciones
        WHERE id = ?
          AND clase_id = ?
          AND estado = 'Inscripto'
    """, (inscripcion_id, clase_id))

    inscripcion = cursor.fetchone()

    if inscripcion is None:
        conexion.close()
        return "No se encontró la inscripción."

    cursor.execute("""
        UPDATE inscripciones
        SET estado = 'Cancelado'
        WHERE id = ?
    """, (inscripcion_id,))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for(
            "ver_inscriptos",
            clase_id=clase_id
        )
    )

@app.route("/clases/<int:clase_id>/asistencia", methods=["GET", "POST"])
def registrar_asistencia_admin(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    mensaje = request.args.get("mensaje")

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar la clase
    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "No se encontró la clase."

    inicio_clase = datetime.fromisoformat(
        f"{clase['fecha']} {clase['hora_inicio']}"
    )

    clase_iniciada = datetime.now() >= inicio_clase

    if request.method == "POST":

        if not clase_iniciada:
            conexion.close()

            return redirect(
                url_for(
                    "registrar_asistencia_admin",
                    clase_id=clase_id,
                    mensaje="Todavía no se puede registrar asistencia porque la clase no comenzó."
                )
            )

        alumnos_presentes = request.form.getlist("alumnos_presentes")

        registradas = 0
        ya_registradas = 0
        sin_bono = 0

        for alumno_id in alumnos_presentes:

            alumno_id = int(alumno_id)

            # Buscar un abono activo y vigente
            cursor.execute("""
                SELECT
                    id,
                    creditos_disponibles,
                    fecha_vencimiento,
                    creditos_ilimitados
                FROM bonos
                WHERE alumno_id = ?
                  AND estado = 'Activo'
                  AND fecha_vencimiento >= ?
                  AND (
                        creditos_disponibles > 0
                        OR creditos_ilimitados = 1
                      )
                ORDER BY fecha_vencimiento ASC
                LIMIT 1
            """, (
                alumno_id,
                datetime.now().strftime("%Y-%m-%d")
            ))

            bono = cursor.fetchone()

            # Verificar si la asistencia ya fue registrada
            cursor.execute("""
                SELECT id
                FROM asistencias
                WHERE clase_id = ?
                  AND alumno_id = ?
            """, (clase_id, alumno_id))

            asistencia_existente = cursor.fetchone()

            if asistencia_existente:
                ya_registradas += 1
                continue

            if bono is None:
                sin_bono += 1
                continue

            creditos_ilimitados = (
                bono["creditos_ilimitados"] == 1
            )

            credito_descontado = (
                0 if creditos_ilimitados else 1
            )

            # Registrar asistencia
            cursor.execute("""
                INSERT INTO asistencias (
                    clase_id,
                    alumno_id,
                    bono_id,
                    fecha_hora,
                    metodo,
                    credito_descontado
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                clase_id,
                alumno_id,
                bono["id"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Manual",
                credito_descontado
            ))

            # Los abonos normales consumen un crédito.
            # Pase Libre no consume créditos.
            if not creditos_ilimitados:

                cursor.execute("""
                    UPDATE bonos
                    SET creditos_disponibles = creditos_disponibles - 1
                    WHERE id = ?
                """, (bono["id"],))

                cursor.execute("""
                    INSERT INTO movimientos_creditos (
                        bono_id,
                        alumno_id,
                        fecha,
                        tipo,
                        cantidad,
                        descripcion
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    bono["id"],
                    alumno_id,
                    datetime.now().strftime("%Y-%m-%d"),
                    "consumo",
                    -1,
                    "Consumo de crédito por asistencia a clase"
                ))

            registradas += 1

        conexion.commit()
        conexion.close()

        mensaje_resultado = (
            f"Asistencias registradas: {registradas}. "
            f"Ya registradas: {ya_registradas}. "
            f"Sin abono activo y vigente: {sin_bono}."
        )

        return redirect(
            url_for(
                "registrar_asistencia_admin",
                clase_id=clase_id,
                mensaje=mensaje_resultado
            )
        )

    # Buscar alumnos inscriptos
    cursor.execute("""
        SELECT
            alumnos.id AS alumno_id,
            alumnos.nombre,
            alumnos.email,
            asistencias.id AS asistencia_id,
            asistencias.fecha_hora,
            asistencias.metodo
        FROM inscripciones
        INNER JOIN alumnos
            ON inscripciones.alumno_id = alumnos.id
        LEFT JOIN asistencias
            ON asistencias.clase_id = inscripciones.clase_id
           AND asistencias.alumno_id = alumnos.id
        WHERE inscripciones.clase_id = ?
          AND inscripciones.estado = 'Inscripto'
        ORDER BY alumnos.nombre ASC
    """, (clase_id,))

    inscriptos = cursor.fetchall()

    conexion.close()

    return render_template(
        "registrar_asistencia_admin.html",
        clase=clase,
        inscriptos=inscriptos,
        mensaje=mensaje,
        clase_iniciada=clase_iniciada
    )

@app.route("/admin/asistencias")
def asistencias_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            asistencias.id,
            asistencias.bono_id,
            asistencias.fecha_hora,
            asistencias.metodo,
            asistencias.credito_descontado,
            alumnos.nombre AS alumno_nombre,
            clases.fecha AS clase_fecha,
            clases.hora_inicio,
            clases.hora_fin
        FROM asistencias
        INNER JOIN alumnos
            ON asistencias.alumno_id = alumnos.id
        INNER JOIN clases
            ON asistencias.clase_id = clases.id
        ORDER BY asistencias.fecha_hora DESC
    """)

    asistencias = cursor.fetchall()

    conexion.close()

    return render_template(
        "asistencias_admin.html",
        asistencias=asistencias
    )

@app.route("/alumnos/<int:alumno_id>/asistencias")
def asistencias_alumno_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno
    cursor.execute("""
        SELECT id, nombre
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "Alumno no encontrado."

    # Buscar únicamente sus asistencias
    cursor.execute("""
        SELECT
            asistencias.id,
            asistencias.bono_id,
            asistencias.fecha_hora,
            asistencias.metodo,
            asistencias.credito_descontado,
            clases.fecha AS clase_fecha,
            clases.hora_inicio,
            clases.hora_fin
        FROM asistencias
        INNER JOIN clases
            ON asistencias.clase_id = clases.id
        WHERE asistencias.alumno_id = ?
        ORDER BY asistencias.fecha_hora DESC
    """, (alumno_id,))

    asistencias = cursor.fetchall()

    conexion.close()

    return render_template(
        "asistencias_alumno_admin.html",
        alumno=alumno,
        asistencias=asistencias
    )

@app.route(
    "/admin/asistencias/<int:asistencia_id>/anular",
    methods=["POST"]
)
def anular_asistencia_admin(asistencia_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar la asistencia
    cursor.execute("""
        SELECT
            id,
            alumno_id,
            bono_id,
            credito_descontado
        FROM asistencias
        WHERE id = ?
    """, (asistencia_id,))

    asistencia = cursor.fetchone()

    if asistencia is None:
        conexion.close()
        return redirect(url_for("asistencias_admin"))

    # Devolver crédito solo si la asistencia consumió uno
    if asistencia["credito_descontado"] > 0:

        cursor.execute("""
            UPDATE bonos
            SET creditos_disponibles = creditos_disponibles + ?
            WHERE id = ?
        """, (
            asistencia["credito_descontado"],
            asistencia["bono_id"]
        ))

        # Registrar la devolución en movimientos
        cursor.execute("""
            INSERT INTO movimientos_creditos (
                bono_id,
                alumno_id,
                fecha,
                tipo,
                cantidad,
                descripcion
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            asistencia["bono_id"],
            asistencia["alumno_id"],
            datetime.now().strftime("%Y-%m-%d"),
            "devolucion",
            asistencia["credito_descontado"],
            "Devolución de crédito por anulación de asistencia"
        ))

    # Eliminar la asistencia
    cursor.execute("""
        DELETE FROM asistencias
        WHERE id = ?
    """, (asistencia_id,))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for("asistencias_admin")
    )

@app.route("/admin/configuracion", methods=["GET", "POST"])
def configuracion_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    mensaje = None
    error = None

    if request.method == "POST":

        nombre = request.form.get(
            "nombre_training_point", ""
        ).strip()

        telefono = request.form.get(
            "telefono", ""
        ).strip()

        direccion = request.form.get(
            "direccion", ""
        ).strip()

        instagram = request.form.get(
            "instagram", ""
        ).strip()

        cupo = request.form.get(
            "cupo_predeterminado", ""
        ).strip()

        minutos = request.form.get(
            "minutos_cancelacion", ""
        ).strip()

        try:
            cupo_numero = int(cupo)
            minutos_numero = int(minutos)

            if not nombre:
                error = "El nombre es obligatorio."

            elif cupo_numero < 1:
                error = "El cupo predeterminado debe ser mayor a 0."

            elif minutos_numero < 0:
                error = "Los minutos de cancelación no pueden ser negativos."

            else:

                valores = {
                    "nombre_training_point": nombre,
                    "telefono": telefono,
                    "direccion": direccion,
                    "instagram": instagram,
                    "cupo_predeterminado": str(cupo_numero),
                    "minutos_cancelacion": str(minutos_numero)
                }

                for clave, valor in valores.items():

                    cursor.execute("""
                        UPDATE configuracion
                        SET valor = ?
                        WHERE clave = ?
                    """, (
                        valor,
                        clave
                    ))

                conexion.commit()

                mensaje = "Configuración actualizada correctamente."

        except ValueError:
            error = "Cupo y minutos de cancelación deben ser números válidos."

    cursor.execute("""
        SELECT clave, valor
        FROM configuracion
    """)

    filas = cursor.fetchall()

    configuracion = {
        fila["clave"]: fila["valor"]
        for fila in filas
    }

    cursor.execute("""
        SELECT *
        FROM horarios_habituales
        ORDER BY hora_inicio ASC
    """)

    horarios = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM tipos_bono
        ORDER BY id ASC
    """)

    tipos_bono = cursor.fetchall()

    conexion.close()

    return render_template(
        "configuracion_admin.html",
        configuracion=configuracion,
        horarios=horarios,
        tipos_bono=tipos_bono,
        mensaje=mensaje,
        error=error
    )

@app.route("/admin/configuracion/horarios/nuevo", methods=["POST"])
def nuevo_horario_habitual():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    hora_inicio = request.form.get("hora_inicio", "").strip()
    hora_fin = request.form.get("hora_fin", "").strip()

    if not hora_inicio or not hora_fin:
        return redirect(url_for("configuracion_admin"))

    if hora_inicio >= hora_fin:
        return redirect(url_for("configuracion_admin"))

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM horarios_habituales
        WHERE hora_inicio = ?
          AND hora_fin = ?
    """, (
        hora_inicio,
        hora_fin
    ))

    horario_existente = cursor.fetchone()

    if horario_existente is None:

        cursor.execute("""
            INSERT INTO horarios_habituales (
                hora_inicio,
                hora_fin,
                activo
            )
            VALUES (?, ?, 1)
        """, (
            hora_inicio,
            hora_fin
        ))

        conexion.commit()

    conexion.close()

    return redirect(
        url_for("configuracion_admin") + "#horarios-habituales"
    )

@app.route(
    "/admin/configuracion/horarios/<int:horario_id>/estado",
    methods=["POST"]
)
def cambiar_estado_horario_habitual(horario_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT activo
        FROM horarios_habituales
        WHERE id = ?
    """, (horario_id,))

    horario = cursor.fetchone()

    if horario is not None:

        nuevo_estado = 0 if horario[0] == 1 else 1

        cursor.execute("""
            UPDATE horarios_habituales
            SET activo = ?
            WHERE id = ?
        """, (
            nuevo_estado,
            horario_id
        ))

        conexion.commit()

    conexion.close()

    return redirect(
        url_for("configuracion_admin") + "#horarios-habituales"
    )

@app.route(
    "/admin/configuracion/horarios/<int:horario_id>/eliminar",
    methods=["POST"]
)
def eliminar_horario_habitual(horario_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM horarios_habituales
        WHERE id = ?
    """, (horario_id,))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for("configuracion_admin") + "#horarios-habituales"
    )

@app.route(
    "/admin/configuracion/abonos/<int:tipo_bono_id>/editar",
    methods=["POST"]
)
def editar_tipo_bono(tipo_bono_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    nombre = request.form.get("nombre", "").strip()
    creditos = request.form.get("creditos", "").strip()
    precio = request.form.get("precio", "").strip()
    duracion_dias = request.form.get("duracion_dias", "").strip()
    creditos_ilimitados = (
        1
        if request.form.get("creditos_ilimitados") == "1"
        else 0
    )

    try:
        precio = float(precio)
        duracion_dias = int(duracion_dias)

        if not nombre or precio < 0 or duracion_dias < 0:
            raise ValueError

        if creditos_ilimitados:
            creditos = 0
        else:
            creditos = int(creditos)

            if creditos < 1:
                raise ValueError

    except ValueError:
        return redirect(
            url_for("configuracion_admin") + "#tipos-abono"
        )

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UUPDATE tipos_bono
        SET
            nombre = ?,
            creditos = ?,
            precio = ?,
            duracion_dias = ?,
            creditos_ilimitados = ?
        WHERE id = ?
    """, (
        nombre,
        creditos,
        precio,
        duracion_dias,
        creditos_ilimitados,
        tipo_bono_id
    ))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for("configuracion_admin") + "#tipos-abono"
    )

@app.route(
    "/admin/configuracion/abonos/<int:tipo_bono_id>/estado",
    methods=["POST"]
)
def cambiar_estado_tipo_bono(tipo_bono_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT activo
        FROM tipos_bono
        WHERE id = ?
    """, (tipo_bono_id,))

    tipo_bono = cursor.fetchone()

    if tipo_bono is not None:

        nuevo_estado = 0 if tipo_bono[0] == 1 else 1

        cursor.execute("""
            UPDATE tipos_bono
            SET activo = ?
            WHERE id = ?
        """, (
            nuevo_estado,
            tipo_bono_id
        ))

        conexion.commit()

    conexion.close()

    return redirect(
        url_for("configuracion_admin") + "#tipos-abono"
    )

@app.route(
    "/admin/configuracion/abonos/nuevo",
    methods=["POST"]
)
def nuevo_tipo_bono():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    nombre = request.form.get("nombre", "").strip()
    creditos = request.form.get("creditos", "").strip()
    precio = request.form.get("precio", "").strip()
    duracion_dias = request.form.get("duracion_dias", "").strip()

    creditos_ilimitados = (
        1
        if request.form.get("creditos_ilimitados") == "1"
        else 0
    )

    try:
        precio = float(precio)
        duracion_dias = int(duracion_dias)

        if not nombre or precio < 0 or duracion_dias < 0:
            raise ValueError

        if creditos_ilimitados:
            creditos = 0
        else:
            creditos = int(creditos)

            if creditos < 1:
                raise ValueError

    except ValueError:
        return redirect(
            url_for("configuracion_admin") + "#tipos-abono"
        )

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO tipos_bono (
            nombre,
            creditos,
            precio,
            duracion_dias,
            activo,
            creditos_ilimitados
        )
        VALUES (?, ?, ?, ?, 1, ?)
    """, (
        nombre,
        creditos,
        precio,
        duracion_dias,
        creditos_ilimitados
    ))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for("configuracion_admin") + "#tipos-abono"
    )

@app.route("/clases/<int:clase_id>/inscribir", methods=["GET", "POST"])
def inscribir_alumno_admin(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "No se encontró la clase."

    cursor.execute("""
        SELECT
            alumnos.id,
            alumnos.nombre,
            alumnos.email
        FROM alumnos
        WHERE alumnos.activo = 1
          AND alumnos.id NOT IN (
              SELECT alumno_id
              FROM inscripciones
              WHERE clase_id = ?
                AND estado = 'Inscripto'
          )
        ORDER BY alumnos.nombre ASC
    """, (clase_id,))

    alumnos_disponibles = cursor.fetchall()

    if request.method == "POST":

        alumno_id = request.form.get("alumno_id")

        if not alumno_id:
            conexion.close()
            return "Debés seleccionar un alumno."

        cursor.execute("""
            SELECT id
            FROM alumnos
            WHERE id = ?
              AND activo = 1
        """, (alumno_id,))

        alumno = cursor.fetchone()

        if alumno is None:
            conexion.close()
            return "El alumno no existe o está inactivo."

        cursor.execute("""
            SELECT COUNT(*)
            FROM inscripciones
            WHERE clase_id = ?
              AND estado = 'Inscripto'
        """, (clase_id,))

        cantidad_inscriptos = cursor.fetchone()[0]

        if cantidad_inscriptos >= clase["cupo_maximo"]:
            conexion.close()
            return "No hay cupos disponibles para esta clase."

        cursor.execute("""
            SELECT id
            FROM inscripciones
            WHERE clase_id = ?
              AND alumno_id = ?
              AND estado = 'Inscripto'
        """, (clase_id, alumno_id))

        inscripcion_existente = cursor.fetchone()

        if inscripcion_existente is not None:
            conexion.close()
            return "El alumno ya está inscripto en esta clase."

        # Verificar que el alumno no esté inscripto
        # en otra clase del mismo día
        cursor.execute("""
            SELECT inscripciones.id
            FROM inscripciones
            INNER JOIN clases
                ON clases.id = inscripciones.clase_id
            WHERE inscripciones.alumno_id = ?
              AND inscripciones.estado = 'Inscripto'
              AND clases.fecha = ?
              AND clases.id != ?
        """, (
            alumno_id,
            clase["fecha"],
            clase_id
        ))

        otra_clase_mismo_dia = cursor.fetchone()

        if otra_clase_mismo_dia is not None:
            conexion.close()
            return "El alumno ya está inscripto en otra clase de ese día."

        fecha_inscripcion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO inscripciones (
                clase_id,
                alumno_id,
                fecha_inscripcion,
                estado
            )
            VALUES (?, ?, ?, ?)
        """, (
            clase_id,
            alumno_id,
            fecha_inscripcion,
            "Inscripto"
        ))

        conexion.commit()
        conexion.close()

        return redirect(
            url_for(
                "ver_inscriptos",
                clase_id=clase_id
            )
        )

    conexion.close()

    return render_template(
        "inscribir_alumno_admin.html",
        clase=clase,
        alumnos=alumnos_disponibles
    )


@app.route("/editar-perfil", methods=["GET", "POST"])
def editar_perfil():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    if request.method == "POST":

        nombre = request.form["nombre"]
        email = request.form["email"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        telefono = request.form["telefono"]
        direccion = request.form["direccion"]

        cursor.execute("""
            UPDATE alumnos
            SET nombre = ?,
                email = ?,
                fecha_nacimiento = ?,
                telefono = ?,
                direccion = ?
            WHERE usuario_id = ?
        """, (
            nombre,
            email,
            fecha_nacimiento,
            telefono,
            direccion,
            session["usuario_id"]
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("perfil_alumno"))

    cursor.execute("""
        SELECT nombre, email, fecha_nacimiento, telefono, direccion
        FROM alumnos
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    conexion.close()

    if alumno is None:
        return "No se encontró el perfil del alumno."

    return render_template(
        "editar_perfil.html",
        alumno=alumno
    )

@app.route("/salud", methods=["GET", "POST"])
def ficha_salud():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT id FROM alumnos WHERE usuario_id = ?",
        (session["usuario_id"],)
    )

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el perfil del alumno."

    alumno_id = alumno["id"]

    if request.method == "POST":

        certificado = request.files.get("certificado_medico")

        if certificado and certificado.filename:

            if not certificado_permitido(certificado.filename):
                conexion.close()
                return "Tipo de archivo no permitido."

        campos = [
            "contacto_emergencia",
            "telefono_emergencia",
            "enfermedad_diagnosticada",
            "detalle_enfermedad",
            "antecedentes_cardiacos",
            "detalle_cardiaco",
            "problemas_respiratorios",
            "detalle_respiratorio",
            "presion_arterial",
            "detalle_presion",
            "diabetes",
            "detalle_diabetes",
            "alergias",
            "detalle_alergias",
            "medicacion",
            "detalle_medicacion",
            "lesion_actual",
            "detalle_lesion_actual",
            "lesion_anterior",
            "detalle_lesion_anterior",
            "dolores_frecuentes",
            "detalle_dolores",
            "limitaciones_movimiento",
            "detalle_limitaciones",
            "observaciones",
            "declaracion_aceptada"
        ]

        datos = {}

        for campo in campos:

            if campo in [
                "enfermedad_diagnosticada",
                "antecedentes_cardiacos",
                "problemas_respiratorios",
                "presion_arterial",
                "diabetes",
                "alergias",
                "medicacion",
                "lesion_actual",
                "lesion_anterior",
                "dolores_frecuentes",
                "limitaciones_movimiento",
                "declaracion_aceptada"
            ]:
                datos[campo] = int(request.form.get(campo, "0"))
            else:
                datos[campo] = request.form.get(campo, "").strip()

        cursor.execute("""
            INSERT INTO salud (
                alumno_id,
                contacto_emergencia,
                telefono_emergencia,
                enfermedad_diagnosticada,
                detalle_enfermedad,
                antecedentes_cardiacos,
                detalle_cardiaco,
                problemas_respiratorios,
                detalle_respiratorio,
                presion_arterial,
                detalle_presion,
                diabetes,
                detalle_diabetes,
                alergias,
                detalle_alergias,
                medicacion,
                detalle_medicacion,
                lesion_actual,
                detalle_lesion_actual,
                lesion_anterior,
                detalle_lesion_anterior,
                dolores_frecuentes,
                detalle_dolores,
                limitaciones_movimiento,
                detalle_limitaciones,
                observaciones,
                declaracion_aceptada,
                fecha_actualizacion
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime')
            )
            ON CONFLICT(alumno_id) DO UPDATE SET
                contacto_emergencia = excluded.contacto_emergencia,
                telefono_emergencia = excluded.telefono_emergencia,
                enfermedad_diagnosticada = excluded.enfermedad_diagnosticada,
                detalle_enfermedad = excluded.detalle_enfermedad,
                antecedentes_cardiacos = excluded.antecedentes_cardiacos,
                detalle_cardiaco = excluded.detalle_cardiaco,
                problemas_respiratorios = excluded.problemas_respiratorios,
                detalle_respiratorio = excluded.detalle_respiratorio,
                presion_arterial = excluded.presion_arterial,
                detalle_presion = excluded.detalle_presion,
                diabetes = excluded.diabetes,
                detalle_diabetes = excluded.detalle_diabetes,
                alergias = excluded.alergias,
                detalle_alergias = excluded.detalle_alergias,
                medicacion = excluded.medicacion,
                detalle_medicacion = excluded.detalle_medicacion,
                lesion_actual = excluded.lesion_actual,
                detalle_lesion_actual = excluded.detalle_lesion_actual,
                lesion_anterior = excluded.lesion_anterior,
                detalle_lesion_anterior = excluded.detalle_lesion_anterior,
                dolores_frecuentes = excluded.dolores_frecuentes,
                detalle_dolores = excluded.detalle_dolores,
                limitaciones_movimiento = excluded.limitaciones_movimiento,
                detalle_limitaciones = excluded.detalle_limitaciones,
                observaciones = excluded.observaciones,
                declaracion_aceptada = excluded.declaracion_aceptada,
                fecha_actualizacion = excluded.fecha_actualizacion
        """, (
            alumno_id,
            datos["contacto_emergencia"],
            datos["telefono_emergencia"],
            datos["enfermedad_diagnosticada"],
            datos["detalle_enfermedad"],
            datos["antecedentes_cardiacos"],
            datos["detalle_cardiaco"],
            datos["problemas_respiratorios"],
            datos["detalle_respiratorio"],
            datos["presion_arterial"],
            datos["detalle_presion"],
            datos["diabetes"],
            datos["detalle_diabetes"],
            datos["alergias"],
            datos["detalle_alergias"],
            datos["medicacion"],
            datos["detalle_medicacion"],
            datos["lesion_actual"],
            datos["detalle_lesion_actual"],
            datos["lesion_anterior"],
            datos["detalle_lesion_anterior"],
            datos["dolores_frecuentes"],
            datos["detalle_dolores"],
            datos["limitaciones_movimiento"],
            datos["detalle_limitaciones"],
            datos["observaciones"],
            datos["declaracion_aceptada"]
        ))

        conexion.commit()

        if certificado and certificado.filename:

            nombre_original = secure_filename(certificado.filename)
            extension = nombre_original.rsplit(".", 1)[1].lower()
            nombre_archivo = f"certificado_medico_alumno_{alumno_id}.{extension}"

            cursor.execute("""
                SELECT certificado_medico
                FROM alumnos
                WHERE id = ?
            """, (alumno_id,))

            certificado_anterior = cursor.fetchone()

            if certificado_anterior and certificado_anterior["certificado_medico"]:
                ruta_anterior = os.path.join(
                    app.config["CERTIFICADOS_FOLDER"],
                    certificado_anterior["certificado_medico"]
                )

                if os.path.exists(ruta_anterior):
                    os.remove(ruta_anterior)

            ruta_certificado = os.path.join(
                app.config["CERTIFICADOS_FOLDER"],
                nombre_archivo
            )

            certificado.save(ruta_certificado)

            cursor.execute("""
                UPDATE alumnos
                SET certificado_medico = ?,
                    fecha_certificado = datetime('now','localtime')
                WHERE id = ?
            """, (nombre_archivo, alumno_id))

            conexion.commit()

    cursor.execute("""
        SELECT *
        FROM salud
        WHERE alumno_id = ?
    """, (alumno_id,))

    salud = cursor.fetchone()

    cursor.execute("""
        SELECT certificado_medico, fecha_certificado
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    certificado_datos = cursor.fetchone()

    certificado_medico = certificado_datos["certificado_medico"] if certificado_datos else None
    fecha_certificado = certificado_datos["fecha_certificado"] if certificado_datos else None

    conexion.close()

    ficha_vencida = fecha_vencida(
        salud["fecha_actualizacion"] if salud else None
    )

    certificado_vencido = fecha_vencida(
        fecha_certificado
    )

    return render_template(
        "salud.html",
        salud=salud,
        certificado_medico=certificado_medico,
        fecha_certificado=fecha_certificado,
        ficha_vencida=ficha_vencida,
        certificado_vencido=certificado_vencido
    )

@app.route("/perfil", methods=["GET", "POST"])
def perfil_alumno():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if request.method == "POST":

        archivo = request.files.get("foto")

        if archivo and archivo_permitido(archivo.filename):

            nombre_archivo = secure_filename(archivo.filename)

            archivo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nombre_archivo
                )
            )

            conexion = conectar()
            cursor = conexion.cursor()

            cursor.execute("""
                UPDATE alumnos
                SET foto_perfil = ?
                WHERE usuario_id = ?
            """, (
                nombre_archivo,
                session["usuario_id"]
            ))

            conexion.commit()
            conexion.close()

    conexion = conectar()
    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT nombre, email, fecha_nacimiento, telefono, direccion,
               certificado_medico, activo, foto_perfil
        FROM alumnos
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    conexion.close()

    if alumno is None:
        return "No se encontró el perfil del alumno."

    return render_template("perfil_alumno.html", alumno=alumno)

@app.route("/mis-clases")
def mis_clases():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    hoy = datetime.now().date()

    fecha_limite = hoy + timedelta(days=30)

    hora_actual = datetime.now().strftime("%H:%M:%S")

    cursor.execute("""
        SELECT
            clases.*,
            (
                SELECT COUNT(*)
                FROM inscripciones
                WHERE inscripciones.clase_id = clases.id
                  AND inscripciones.estado = 'Inscripto'
            ) AS cantidad_inscriptos,

            (
                SELECT COUNT(*)
                FROM inscripciones
                INNER JOIN alumnos
                    ON inscripciones.alumno_id = alumnos.id
                WHERE inscripciones.clase_id = clases.id
                  AND alumnos.usuario_id = ?
                  AND inscripciones.estado = 'Inscripto'
            ) AS alumno_inscripto

        FROM clases

        WHERE clases.estado = 'Disponible'
          AND clases.fecha BETWEEN ? AND ?
          AND (
                clases.fecha > ?
                OR (
                    clases.fecha = ?
                    AND clases.hora_fin > ?
                )
              )

        ORDER BY clases.fecha ASC, clases.hora_inicio ASC
    """, (
        session["usuario_id"],
        hoy.strftime("%Y-%m-%d"),
        fecha_limite.strftime("%Y-%m-%d"),
        hoy.strftime("%Y-%m-%d"),
        hoy.strftime("%Y-%m-%d"),
        hora_actual
    ))

    clases = cursor.fetchall()

    clases_por_fecha = {}

    for clase in clases:

        fecha_clase = clase["fecha"]

        if fecha_clase not in clases_por_fecha:
            clases_por_fecha[fecha_clase] = []

        clases_por_fecha[fecha_clase].append(clase)


    nombres_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo"
    ]

    semanas = []

    inicio_calendario = hoy - timedelta(days=hoy.weekday())

    inicio = inicio_calendario

    while inicio <= fecha_limite:

        dias = []

        for numero_dia in range(7):

            fecha_dia = inicio + timedelta(days=numero_dia)
            fecha_texto = fecha_dia.strftime("%Y-%m-%d")

            dias.append({
                "nombre": nombres_dias[numero_dia],
                "fecha": fecha_dia,
                "fecha_texto": fecha_texto,
                "clases": clases_por_fecha.get(fecha_texto, [])
            })

        semanas.append({
            "inicio": inicio,
            "fin": inicio + timedelta(days=6),
            "dias": dias
        })

        inicio = inicio + timedelta(days=7)

    conexion.close()

    mensaje = request.args.get("mensaje")

    return render_template(
        "mis_clases.html",
        clases=clases,
        semanas=semanas,
        mensaje=mensaje,
        hoy=hoy,
        fecha_limite=fecha_limite
    )

@app.route("/mis-clases/<int:clase_id>/inscribirme", methods=["POST"])
def inscribirme_clase(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar la clase
    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
          AND estado = 'Disponible'
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "No se encontró la clase o no está disponible."

    # Buscar al alumno correspondiente al usuario que inició sesión
    cursor.execute("""
        SELECT id, activo
        FROM alumnos
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    if alumno["activo"] != 1:
        conexion.close()
        return "El alumno está inactivo."

    # Verificar cupos
    cursor.execute("""
        SELECT COUNT(*)
        FROM inscripciones
        WHERE clase_id = ?
          AND estado = 'Inscripto'
    """, (clase_id,))

    cantidad_inscriptos = cursor.fetchone()[0]

    if cantidad_inscriptos >= clase["cupo_maximo"]:
        conexion.close()
        return "No hay cupos disponibles para esta clase."

    # Verificar si ya existe una inscripción
    cursor.execute("""
        SELECT id, estado
        FROM inscripciones
        WHERE clase_id = ?
           AND alumno_id = ?
    """, (clase_id, alumno["id"]))

    inscripcion_existente = cursor.fetchone()

    if inscripcion_existente is not None:

        if inscripcion_existente["estado"] == "Inscripto":

            conexion.close()

            return redirect(
                url_for(
                    "mis_clases",
                    mensaje="Ya estás inscripto en esta clase."
                )
            )

        elif inscripcion_existente["estado"] == "Cancelado":

            fecha_inscripcion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                UPDATE inscripciones
                SET estado = 'Inscripto',
                    fecha_inscripcion = ?
                WHERE id = ?
            """, (
                fecha_inscripcion,
                inscripcion_existente["id"]
            ))

            conexion.commit()
            conexion.close()

            return redirect(url_for("mis_clases"))

    # Registrar inscripción
    fecha_inscripcion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO inscripciones (
            clase_id,
            alumno_id,
            fecha_inscripcion,
            estado
        )
        VALUES (?, ?, ?, ?)
    """, (
        clase_id,
        alumno["id"],
        fecha_inscripcion,
        "Inscripto"
    ))

    conexion.commit()
    conexion.close()

    return redirect(url_for("mis_clases"))

@app.route("/mis-clases/<int:clase_id>/cancelar", methods=["POST"])
def cancelar_inscripcion_alumno(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno correspondiente al usuario
    cursor.execute("""
        SELECT id
        FROM alumnos
        WHERE usuario_id = ?
          AND activo = 1
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    # Buscar la inscripción activa
    cursor.execute("""
        SELECT id
        FROM inscripciones
        WHERE clase_id = ?
          AND alumno_id = ?
          AND estado = 'Inscripto'
    """, (clase_id, alumno["id"]))

    inscripcion = cursor.fetchone()

    if inscripcion is None:
        conexion.close()

        return redirect(
            url_for(
                "mis_clases",
                mensaje="No estás inscripto en esta clase."
            )
        )

# Verificar que todavía esté dentro del plazo de cancelación
    cursor.execute("""
        SELECT fecha, hora_inicio
        FROM clases
        WHERE id = ?
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return redirect(
            url_for(
                "mis_clases",
                mensaje="La clase no existe."
            )
        )

    inicio_clase = datetime.fromisoformat(
        f"{clase['fecha']} {clase['hora_inicio']}"
    )

    cursor.execute("""
        SELECT valor
        FROM configuracion
        WHERE clave = 'minutos_cancelacion'
    """)

    fila_configuracion = cursor.fetchone()

    minutos_cancelacion = 10

    if fila_configuracion is not None:
        try:
            minutos_cancelacion = int(fila_configuracion["valor"])
        except (ValueError, TypeError):
            minutos_cancelacion = 10

    limite_cancelacion = inicio_clase - timedelta(
        minutes=minutos_cancelacion
    )

    if datetime.now() > limite_cancelacion:
        conexion.close()

        return redirect(
            url_for(
                "mis_clases",
                mensaje=(
                    "Ya no podés cancelar la inscripción. "
                    f"El límite es {minutos_cancelacion} minutos "
                    "antes de la clase."
                )
            )
        )

    # Cancelar inscripción
    cursor.execute("""
        UPDATE inscripciones
        SET estado = 'Cancelado'
        WHERE id = ?
    """, (inscripcion["id"],))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for(
            "mis_clases",
            mensaje="Tu inscripción fue cancelada correctamente."
        )
    )

@app.route("/mis-clases/<int:clase_id>/inscriptos")
def ver_inscriptos_alumno(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar la clase
    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
          AND estado = 'Disponible'
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "No se encontró la clase o no está disponible."

    # Buscar alumnos inscriptos
    cursor.execute("""
        SELECT alumnos.nombre
        FROM inscripciones
        INNER JOIN alumnos
            ON inscripciones.alumno_id = alumnos.id
        WHERE inscripciones.clase_id = ?
          AND inscripciones.estado = 'Inscripto'
        ORDER BY alumnos.nombre ASC
    """, (clase_id,))

    inscriptos = cursor.fetchall()

    conexion.close()

    return render_template(
        "inscriptos_clase_alumno.html",
        clase=clase,
        inscriptos=inscriptos
    )

@app.route("/mis-inscripciones")
def mis_inscripciones():

    mensaje = request.args.get("mensaje")

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            inscripciones.id AS inscripcion_id,
            inscripciones.fecha_inscripcion,
            inscripciones.estado,

            clases.id AS clase_id,
            clases.fecha,
            clases.hora_inicio,
            clases.hora_fin,
            clases.cupo_maximo

        FROM inscripciones

        INNER JOIN alumnos
            ON inscripciones.alumno_id = alumnos.id

        INNER JOIN clases
            ON inscripciones.clase_id = clases.id

        WHERE alumnos.usuario_id = ?
           AND inscripciones.estado = 'Inscripto'

        ORDER BY clases.fecha ASC, clases.hora_inicio ASC
    """, (session["usuario_id"],))

    inscripciones = cursor.fetchall()

    conexion.close()

    return render_template(
        "mis_inscripciones.html",
        inscripciones=inscripciones,
        mensaje=mensaje
    )

@app.route("/mi-bono")
def mi_bono():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno correspondiente al usuario
    cursor.execute("""
        SELECT id
        FROM alumnos
        WHERE usuario_id = ?
          AND activo = 1
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    # Buscar el bono activo del alumno
    cursor.execute("""
        SELECT
            bonos.id,
            bonos.alumno_id,
            bonos.tipo_bono_id,
            bonos.creditos_iniciales,
            bonos.creditos_disponibles,
            bonos.creditos_ilimitados,
            bonos.fecha_inicio,
            bonos.fecha_vencimiento,
            bonos.estado,
            tipos_bono.nombre AS nombre_bono
        FROM bonos
        INNER JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE bonos.alumno_id = ?
          AND bonos.estado = 'Activo'
        ORDER BY bonos.fecha_vencimiento ASC
        LIMIT 1
    """, (alumno["id"],))

    bono = cursor.fetchone()

        # Calcular créditos utilizados e historial del bono
    movimientos = []

    if bono:

        cursor.execute("""
            SELECT
                fecha,
                tipo,
                cantidad,
                descripcion
            FROM movimientos_creditos
            WHERE bono_id = ?
            ORDER BY fecha ASC, id ASC
        """, (bono["id"],))

        movimientos = cursor.fetchall()

    creditos_utilizados = 0

    for movimiento in movimientos:

        if movimiento["tipo"] == "consumo":
            creditos_utilizados += abs(movimiento["cantidad"])

    conexion.close()

    return render_template(
        "mi_bono.html",
        bono=bono,
        movimientos=movimientos,
        creditos_utilizados=creditos_utilizados
    )

@app.route("/pagos")
def pagos():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno correspondiente al usuario
    cursor.execute("""
        SELECT id
        FROM alumnos
        WHERE usuario_id = ?
          AND activo = 1
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    # Buscar los pagos asociados a los bonos del alumno
    cursor.execute("""
        SELECT
            bonos.id,
            bonos.precio,
            bonos.forma_pago,
            bonos.fecha_pago,
            bonos.fecha_inicio,
            bonos.fecha_vencimiento,
            tipos_bono.nombre AS nombre_bono
        FROM bonos
        INNER JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE bonos.alumno_id = ?
        ORDER BY bonos.fecha_pago DESC
    """, (alumno["id"],))

    pagos = cursor.fetchall()

    conexion.close()

    return render_template(
        "pagos.html",
        pagos=pagos
    )

@app.route("/admin/pagos")
def pagos_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            bonos.id,
            bonos.fecha_pago,
            bonos.precio,
            bonos.forma_pago,
            bonos.estado,
            alumnos.nombre AS alumno_nombre,
            tipos_bono.nombre AS nombre_bono
        FROM bonos
        INNER JOIN alumnos
            ON bonos.alumno_id = alumnos.id
        INNER JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE bonos.fecha_pago IS NOT NULL
        ORDER BY bonos.fecha_pago DESC, bonos.id DESC
    """)

    pagos = cursor.fetchall()

    conexion.close()

    return render_template(
        "pagos_admin.html",
        pagos=pagos
    )

@app.route("/alumnos/<int:alumno_id>/pagos")
def pagos_alumno_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno
    cursor.execute("""
        SELECT id, nombre
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "Alumno no encontrado."

    # Buscar únicamente sus pagos
    cursor.execute("""
        SELECT
            bonos.id,
            bonos.fecha_pago,
            bonos.precio,
            bonos.forma_pago,
            bonos.estado,
            tipos_bono.nombre AS nombre_bono
        FROM bonos
        INNER JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE bonos.alumno_id = ?
          AND bonos.fecha_pago IS NOT NULL
        ORDER BY bonos.fecha_pago DESC, bonos.id DESC
    """, (alumno_id,))

    pagos = cursor.fetchall()

    conexion.close()

    return render_template(
        "pagos_alumno_admin.html",
        alumno=alumno,
        pagos=pagos
    )

@app.route("/mis-asistencias")
def mis_asistencias():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id
        FROM alumnos
        WHERE usuario_id = ?
          AND activo = 1
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    cursor.execute("""
        SELECT
            asistencias.id,
            asistencias.fecha_hora,
            asistencias.metodo,
            asistencias.credito_descontado,
            clases.fecha,
            clases.hora_inicio,
            clases.hora_fin
        FROM asistencias
        INNER JOIN clases
            ON asistencias.clase_id = clases.id
        WHERE asistencias.alumno_id = ?
        ORDER BY asistencias.fecha_hora DESC
    """, (alumno["id"],))

    asistencias = cursor.fetchall()

    conexion.close()

    return render_template(
        "mis_asistencias.html",
        asistencias=asistencias
    )

@app.route("/mis-inscripciones/<int:inscripcion_id>/cancelar", methods=["POST"])
def cancelar_inscripcion_desde_mis_inscripciones(inscripcion_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar al alumno correspondiente al usuario
    cursor.execute("""
        SELECT id
        FROM alumnos
        WHERE usuario_id = ?
          AND activo = 1
    """, (session["usuario_id"],))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el alumno."

    # Buscar la inscripción y comprobar que pertenece al alumno
    cursor.execute("""
        SELECT
            inscripciones.id,
            clases.fecha,
            clases.hora_inicio
        FROM inscripciones
        INNER JOIN clases
            ON inscripciones.clase_id = clases.id
        WHERE inscripciones.id = ?
          AND inscripciones.alumno_id = ?
          AND inscripciones.estado = 'Inscripto'
    """, (
        inscripcion_id,
        alumno["id"]
    ))

    inscripcion = cursor.fetchone()

    if inscripcion is None:
        conexion.close()

        return redirect(
            url_for(
                "mis_inscripciones"
            )
        )

    # Verificar que todavía esté dentro del plazo de cancelación
    inicio_clase = datetime.fromisoformat(
        f"{inscripcion['fecha']} {inscripcion['hora_inicio']}"
    )

    cursor.execute("""
        SELECT valor
        FROM configuracion
        WHERE clave = 'minutos_cancelacion'
    """)

    fila_configuracion = cursor.fetchone()

    minutos_cancelacion = 10

    if fila_configuracion is not None:
        try:
            minutos_cancelacion = int(fila_configuracion["valor"])
        except (ValueError, TypeError):
            minutos_cancelacion = 10

    limite_cancelacion = inicio_clase - timedelta(
        minutes=minutos_cancelacion
    )

    if datetime.now() > limite_cancelacion:
        conexion.close()

        return redirect(
            url_for(
                "mis_inscripciones",
                mensaje=(
                    "Ya no podés cancelar la inscripción. "
                    f"El límite es {minutos_cancelacion} minutos "
                    "antes de la clase."
                )
            )
        )

    # Cancelar inscripción
    cursor.execute("""
        UPDATE inscripciones
        SET estado = 'Cancelado'
        WHERE id = ?
    """, (inscripcion_id,))

    conexion.commit()
    conexion.close()

    return redirect(
        url_for(
            "mis_inscripciones"
        )
    )

@app.route("/alumnos/<int:alumno_id>")
def perfil_alumno_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, email, fecha_nacimiento,
               telefono, direccion, certificado_medico, fecha_certificado, activo, foto_perfil
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    alumno = cursor.fetchone()

    conexion.close()

    if alumno is None:
        return "Alumno no encontrado."

    certificado_vencido = fecha_vencida(alumno["fecha_certificado"])

    return render_template(
        "perfil_alumno_admin.html",
        alumno=alumno,
        certificado_vencido=certificado_vencido
    )

@app.route("/alumnos/<int:alumno_id>/bonos/nuevo", methods=["GET", "POST"])
def nuevo_bono_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "Alumno no encontrado."

    cursor.execute("""
        SELECT *
        FROM tipos_bono
        WHERE activo = 1
        ORDER BY id
    """)

    tipos_bono = cursor.fetchall()

    if request.method == "POST":

        tipo_bono_id = request.form.get("tipo_bono_id")
        fecha_inicio = request.form.get("fecha_inicio")
        forma_pago = request.form.get("forma_pago")

        if not tipo_bono_id or not fecha_inicio or not forma_pago:
            conexion.close()
            return "Faltan datos obligatorios."

        cursor.execute("""
            SELECT *
            FROM tipos_bono
            WHERE id = ?
              AND activo = 1
        """, (tipo_bono_id,))

        tipo_bono = cursor.fetchone()

        if tipo_bono is None:
            conexion.close()
            return "Tipo de abono no válido."

        creditos_iniciales = tipo_bono["creditos"]
        precio = tipo_bono["precio"]
        duracion_dias = tipo_bono["duracion_dias"]
        creditos_ilimitados = tipo_bono["creditos_ilimitados"]

        cursor.execute("""
            UPDATE bonos
            SET estado = 'Finalizado'
            WHERE alumno_id = ?
              AND estado = 'Activo'
        """, (alumno_id,))

        if creditos_ilimitados:

            fecha_inicio_dt = datetime.strptime(
                fecha_inicio,
                "%Y-%m-%d"
            )

            fecha_vencimiento_original = (
                fecha_inicio_dt + timedelta(days=duracion_dias)
            ).strftime("%Y-%m-%d")

        elif creditos_iniciales == 1:

            fecha_vencimiento_original = fecha_inicio

        else:

            fecha_vencimiento_original = calcular_vencimiento_bono(
                fecha_inicio,
                creditos_iniciales
            )
        cursor.execute("""
            INSERT INTO bonos (
                alumno_id,
                tipo_bono_id,
                fecha_inicio,
                fecha_vencimiento_original,
                fecha_vencimiento,
                creditos_iniciales,
                creditos_disponibles,
                precio,
                forma_pago,
                fecha_pago,
                extension_dias,
                estado,
                creditos_ilimitados
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alumno_id,
            tipo_bono_id,
            fecha_inicio,
            fecha_vencimiento_original,
            fecha_vencimiento_original,
            creditos_iniciales,
            creditos_iniciales,
            precio,
            forma_pago,
            fecha_inicio,
            0,
            "Activo",
            creditos_ilimitados
        ))

        bono_id = cursor.lastrowid

        if not creditos_ilimitados:

            cursor.execute("""
                INSERT INTO movimientos_creditos (
                    bono_id,
                    alumno_id,
                    fecha,
                    tipo,
                    cantidad,
                    descripcion
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bono_id,
                alumno_id,
                fecha_inicio,
                "carga",
                creditos_iniciales,
                "Carga inicial de créditos por compra de bono"
            ))

        conexion.commit()
        conexion.close()

        return redirect(
            url_for(
                "bonos_alumno_admin",
                alumno_id=alumno_id
            )
        )

    conexion.close()

    return render_template(
        "nuevo_bono_admin.html",
        alumno=alumno,
        tipos_bono=tipos_bono
    )

@app.route("/alumnos/<int:alumno_id>/bonos")
def bonos_alumno_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "Alumno no encontrado."

    cursor.execute("""
        SELECT
            bonos.*,
            tipos_bono.nombre AS nombre_bono
        FROM bonos
        INNER JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE bonos.alumno_id = ?
        ORDER BY bonos.fecha_inicio DESC
    """, (alumno_id,))

    bonos = cursor.fetchall()

    conexion.close()

    return render_template(
        "bonos_alumno_admin.html",
        alumno=alumno,
        bonos=bonos
    )

@app.route("/bonos/<int:bono_id>/editar-vencimiento", methods=["GET", "POST"])
def editar_vencimiento_bono_admin(bono_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            bonos.*,
            alumnos.nombre AS nombre_alumno,
            tipos_bono.nombre AS nombre_bono
        FROM bonos
        INNER JOIN alumnos
            ON bonos.alumno_id = alumnos.id
        INNER JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE bonos.id = ?
    """, (bono_id,))

    bono = cursor.fetchone()

    if bono is None:
        conexion.close()
        return "Bono no encontrado."

    if request.method == "POST":

        nueva_fecha = request.form.get(
            "fecha_vencimiento",
            ""
        ).strip()

        motivo = request.form.get(
            "motivo_extension",
            ""
        ).strip()

        if not nueva_fecha:
            conexion.close()
            return "Debe indicar una fecha de vencimiento."

        try:
            fecha_nueva = datetime.strptime(
                nueva_fecha,
                "%Y-%m-%d"
            )

            fecha_original = datetime.strptime(
                bono["fecha_vencimiento_original"],
                "%Y-%m-%d"
            )

        except ValueError:
            conexion.close()
            return "La fecha indicada no es válida."

        extension_dias = (
            fecha_nueva - fecha_original
        ).days

        cursor.execute("""
            UPDATE bonos
            SET
                fecha_vencimiento = ?,
                extension_dias = ?,
                motivo_extension = ?
            WHERE id = ?
        """, (
            nueva_fecha,
            extension_dias,
            motivo,
            bono_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(
            url_for(
                "bonos_alumno_admin",
                alumno_id=bono["alumno_id"]
            )
        )

    conexion.close()

    return render_template(
        "editar_vencimiento_bono_admin.html",
        bono=bono
    )

@app.route("/admin/certificados")
def certificados_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            certificado_medico,
            fecha_certificado
        FROM alumnos
        WHERE activo = 1
        ORDER BY nombre ASC
    """)

    alumnos = cursor.fetchall()
    conexion.close()

    certificados = []

    vigentes = 0
    vencidos = 0
    sin_certificado = 0

    for alumno in alumnos:

        if not alumno["certificado_medico"]:
            estado = "Sin certificado"
            sin_certificado += 1

        elif fecha_vencida(alumno["fecha_certificado"]):
            estado = "Vencido"
            vencidos += 1

        else:
            estado = "Vigente"
            vigentes += 1

        certificados.append({
            "id": alumno["id"],
            "nombre": alumno["nombre"],
            "certificado_medico": alumno["certificado_medico"],
            "fecha_certificado": alumno["fecha_certificado"],
            "estado": estado
        })

    return render_template(
        "certificados_admin.html",
        certificados=certificados,
        vigentes=vigentes,
        vencidos=vencidos,
        sin_certificado=sin_certificado
    )

@app.route("/alumnos/<int:alumno_id>/salud")
def ficha_salud_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            alumnos.id,
            alumnos.nombre,
            alumnos.certificado_medico,
            alumnos.fecha_certificado,
            salud.*
        FROM alumnos
        LEFT JOIN salud
            ON alumnos.id = salud.alumno_id
        WHERE alumnos.id = ?
    """, (alumno_id,))

    ficha = cursor.fetchone()

    conexion.close()

    if ficha is None:
        return "Alumno no encontrado."

    certificado_vencido = fecha_vencida(ficha["fecha_certificado"])

    return render_template(
        "ficha_salud_admin.html",
        ficha=ficha,
        certificado_vencido=certificado_vencido
    )


@app.route("/alumnos/<int:alumno_id>/editar", methods=["GET", "POST"])
def editar_alumno_admin(alumno_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        activo = request.form.get("activo", "0")

        cursor.execute("""
            UPDATE alumnos
            SET nombre = ?,
                email = ?,
                fecha_nacimiento = ?,
                telefono = ?,
                direccion = ?,
                activo = ?
            WHERE id = ?
        """, (
            nombre,
            email,
            fecha_nacimiento,
            telefono,
            direccion,
            int(activo),
            alumno_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("perfil_alumno_admin", alumno_id=alumno_id))

    cursor.execute("""
        SELECT id, nombre, email, fecha_nacimiento,
               telefono, direccion, activo
        FROM alumnos
        WHERE id = ?
    """, (alumno_id,))

    alumno = cursor.fetchone()
    conexion.close()

    if alumno is None:
        return "Alumno no encontrado."

    return render_template(
        "editar_alumno_admin.html",
        alumno=alumno
    )

@app.route("/estado-alumnos")
def estado_alumnos():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            alumnos.id,
            alumnos.nombre,
            bonos.id AS bono_id,
            tipos_bono.nombre AS nombre_bono,
            bonos.fecha_pago,
            bonos.fecha_vencimiento,
            bonos.precio,
            bonos.creditos_iniciales,
            bonos.creditos_disponibles,
            bonos.creditos_ilimitados,
            bonos.estado
        FROM alumnos
        LEFT JOIN bonos
            ON alumnos.id = bonos.alumno_id
            AND bonos.estado = 'Activo'
        LEFT JOIN tipos_bono
            ON bonos.tipo_bono_id = tipos_bono.id
        WHERE alumnos.activo = 1
        ORDER BY
            bonos.fecha_vencimiento IS NULL,
            bonos.fecha_vencimiento ASC
    """)

    alumnos = cursor.fetchall()

    hoy = datetime.now().date()

    alumnos = [
        {
            **dict(alumno),
            "dias_para_vencer": (
                datetime.strptime(alumno["fecha_vencimiento"], "%Y-%m-%d").date() - hoy
            ).days
            if alumno["fecha_vencimiento"]
            else None
        }
        for alumno in alumnos
    ]

    bonos_vigentes = 0
    bonos_por_vencer = 0
    bonos_vencidos = 0
    alumnos_sin_bono = 0
    bonos_sin_creditos = 0

    for alumno in alumnos:

        dias = alumno["dias_para_vencer"]
        creditos = alumno["creditos_disponibles"]
        creditos_ilimitados = alumno["creditos_ilimitados"]

        if dias is None:
            alumnos_sin_bono += 1

        elif creditos == 0 and not creditos_ilimitados:
            bonos_sin_creditos += 1

        elif dias <= 0:
            bonos_vencidos += 1

        elif dias <= 7:
            bonos_por_vencer += 1

        else:
            bonos_vigentes += 1

    conexion.close()

    return render_template(
        "estado_alumnos.html",
        alumnos=alumnos,
        bonos_vigentes=bonos_vigentes,
        bonos_por_vencer=bonos_por_vencer,
        bonos_vencidos=bonos_vencidos,
        bonos_sin_creditos=bonos_sin_creditos,
        alumnos_sin_bono=alumnos_sin_bono
    )

@app.route("/alumnos")
def mostrar_alumnos():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    busqueda = request.args.get("busqueda", "").strip()

    conexion = conectar()
    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()

    if busqueda:

        cursor.execute("""
            SELECT id, nombre, email, fecha_nacimiento, telefono, activo
            FROM alumnos
            WHERE CAST(id AS TEXT) LIKE ?
               OR nombre LIKE ?
               OR email LIKE ?
            ORDER BY nombre
        """, (
            f"%{busqueda}%",
            f"%{busqueda}%",
            f"%{busqueda}%"
        ))

    else:

        cursor.execute("""
            SELECT id, nombre, email, fecha_nacimiento, telefono, activo
            FROM alumnos
            ORDER BY nombre
        """)

    alumnos = cursor.fetchall()

    conexion.close()

    return render_template(
        "alumnos.html",
        alumnos=alumnos,
        busqueda=busqueda
    )


@app.route("/agregar")
def agregar_alumno():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("agregar.html")

@app.route("/lector-qr")
def lector_qr():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "alumno":
        return "Acceso no autorizado."

    return render_template("lector_qr.html")

@app.route("/api/checkin", methods=["POST"])
def checkin():

    if "usuario_id" not in session:
        return {
            "ok": False,
            "mensaje": "La sesión no está iniciada."
        }, 401

    if session["rol"] != "alumno":
        return {
            "ok": False,
            "mensaje": "Solo los alumnos pueden registrar asistencia."
        }, 403

    datos = request.get_json()

    if not datos:
        return {
            "ok": False,
            "mensaje": "No se recibieron datos."
        }, 400

    codigo = datos.get("codigo")

    if codigo != "TRAININGPOINT-CHECKIN":
        return {
            "ok": False,
            "mensaje": "Código QR no válido."
        }, 400

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    try:

        # Buscar al alumno correspondiente al usuario conectado
        cursor.execute("""
            SELECT id, nombre
            FROM alumnos
            WHERE usuario_id = ?
              AND activo = 1
        """, (session["usuario_id"],))

        alumno = cursor.fetchone()

        if alumno is None:
            conexion.close()

            return {
                "ok": False,
                "mensaje": "No se encontró el alumno."
            }, 404

        ahora = datetime.now()

        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.strftime("%H:%M:%S")

        # Buscar la clase que está ocurriendo en este momento
        cursor.execute("""
            SELECT *
            FROM clases
            WHERE fecha = ?
              AND hora_inicio <= ?
              AND hora_fin > ?
            ORDER BY hora_inicio ASC
            LIMIT 1
        """, (
            fecha_hoy,
            hora_actual,
            hora_actual
        ))

        clase = cursor.fetchone()

        if clase is None:
            conexion.close()

            return {
                "ok": False,
                "mensaje": "No hay una clase en curso en este momento."
            }, 400

        # Verificar que el alumno esté inscripto en la clase
        cursor.execute("""
            SELECT id
            FROM inscripciones
            WHERE clase_id = ?
              AND alumno_id = ?
              AND estado = 'Inscripto'
        """, (
            clase["id"],
            alumno["id"]
        ))

        inscripcion = cursor.fetchone()

        if inscripcion is None:
            conexion.close()

            return {
                "ok": False,
                "mensaje": "No estás inscripto en esta clase."
            }, 400

        # Verificar que no tenga ya registrada la asistencia
        cursor.execute("""
            SELECT id
            FROM asistencias
            WHERE clase_id = ?
              AND alumno_id = ?
        """, (
            clase["id"],
            alumno["id"]
        ))

        asistencia_existente = cursor.fetchone()

        if asistencia_existente:
            conexion.close()

            return {
                "ok": False,
                "mensaje": "Tu asistencia ya fue registrada."
            }, 400

        # Buscar abono activo y vigente
        cursor.execute("""
            SELECT
                id,
                creditos_disponibles,
                creditos_ilimitados
            FROM bonos
            WHERE alumno_id = ?
              AND estado = 'Activo'
              AND fecha_vencimiento >= ?
              AND (
                    creditos_disponibles > 0
                    OR creditos_ilimitados = 1
                  )
            ORDER BY fecha_vencimiento ASC
            LIMIT 1
        """, (
            alumno["id"],
            fecha_hoy
        ))

        bono = cursor.fetchone()

        if bono is None:
            conexion.close()

            return {
                "ok": False,
                "mensaje": "No tenés un abono activo y vigente."
            }, 400

        creditos_ilimitados = (
            bono["creditos_ilimitados"] == 1
        )

        credito_descontado = (
            0 if creditos_ilimitados else 1
        )

        # Registrar asistencia
        cursor.execute("""
            INSERT INTO asistencias (
                clase_id,
                alumno_id,
                bono_id,
                fecha_hora,
                metodo,
                credito_descontado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            clase["id"],
            alumno["id"],
            bono["id"],
            ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "QR",
            credito_descontado
        ))

        if not creditos_ilimitados:

            # Descontar un crédito
            cursor.execute("""
                UPDATE bonos
                SET creditos_disponibles = creditos_disponibles - 1
                WHERE id = ?
            """, (bono["id"],))

            # Registrar movimiento
            cursor.execute("""
                INSERT INTO movimientos_creditos (
                    bono_id,
                    alumno_id,
                    fecha,
                    tipo,
                    cantidad,
                    descripcion
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bono["id"],
                alumno["id"],
                fecha_hoy,
                "consumo",
                -1,
                "Consumo de crédito por asistencia mediante QR"
            ))

        conexion.commit()
        conexion.close()

        return {
            "ok": True,
            "mensaje": "¡Asistencia registrada correctamente!",
            "alumno": alumno["nombre"],
            "clase": clase["hora_inicio"],
            "credito_descontado": credito_descontado
        }

    except Exception as error:

        conexion.rollback()
        conexion.close()

        return {
            "ok": False,
            "mensaje": f"Error al registrar la asistencia: {error}"
        }, 500

@app.route("/admin/rutinas")
def rutinas_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    hoy = datetime.now().date()

    fecha_limite = hoy + timedelta(days=30)

    cursor.execute("""
        SELECT
            clases.id,
            clases.fecha,
            clases.hora_inicio,
            clases.hora_fin,
            rutinas.id AS rutina_id,
            rutinas.titulo,
            rutinas.fecha_actualizacion
        FROM clases
        LEFT JOIN rutinas
            ON rutinas.clase_id = clases.id
        WHERE clases.fecha BETWEEN ? AND ?
        ORDER BY clases.fecha ASC, clases.hora_inicio ASC
    """, (
        hoy.strftime("%Y-%m-%d"),
        fecha_limite.strftime("%Y-%m-%d")
    ))

    clases = cursor.fetchall()

    conexion.close()

    return render_template(
        "rutinas_admin.html",
        clases=clases,
        hoy=hoy
    )

@app.route("/admin/rutinas/<int:clase_id>", methods=["GET", "POST"])
def editar_rutina_admin(clase_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM clases
        WHERE id = ?
    """, (clase_id,))

    clase = cursor.fetchone()

    if clase is None:
        conexion.close()
        return "Clase no encontrada.", 404

    cursor.execute("""
        SELECT *
        FROM rutinas
        WHERE clase_id = ?
    """, (clase_id,))

    rutina = cursor.fetchone()

    mensaje = None

    if request.method == "POST":

        titulo = request.form.get("titulo", "").strip()
        contenido = request.form.get("contenido", "").strip()

        if not contenido:

            mensaje = "El contenido de la rutina es obligatorio."

        else:

            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if rutina:

                cursor.execute("""
                    UPDATE rutinas
                    SET
                        titulo = ?,
                        contenido = ?,
                        fecha_actualizacion = ?
                    WHERE clase_id = ?
                """, (
                    titulo,
                    contenido,
                    ahora,
                    clase_id
                ))

            else:

                cursor.execute("""
                    INSERT INTO rutinas (
                        clase_id,
                        titulo,
                        contenido,
                        fecha_creacion
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    clase_id,
                    titulo,
                    contenido,
                    ahora
                ))

            conexion.commit()
            conexion.close()

            return redirect(url_for("rutinas_admin"))

    conexion.close()

    return render_template(
        "editar_rutina_admin.html",
        clase=clase,
        rutina=rutina,
        mensaje=mensaje
    )

@app.route("/admin/notificaciones")
def notificaciones_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            notificaciones.*,
            alumnos.nombre AS nombre_alumno
        FROM notificaciones
        LEFT JOIN alumnos
            ON notificaciones.alumno_id = alumnos.id
        ORDER BY notificaciones.fecha_creacion DESC
    """)

    notificaciones = cursor.fetchall()

    conexion.close()

    return render_template(
        "notificaciones_admin.html",
        notificaciones=notificaciones
    )

@app.route("/admin/notificaciones/nueva", methods=["GET", "POST"])
def nueva_notificacion_admin():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre
        FROM alumnos
        WHERE activo = 1
        ORDER BY nombre ASC
    """)

    alumnos = cursor.fetchall()

    mensaje_error = None

    if request.method == "POST":

        tipo = request.form.get("tipo", "").strip()
        titulo = request.form.get("titulo", "").strip()
        mensaje = request.form.get("mensaje", "").strip()
        alumno_id = request.form.get("alumno_id", "").strip()

        if tipo not in ("General", "Individual"):
            mensaje_error = "Seleccioná un tipo de notificación."

        elif not titulo or not mensaje:
            mensaje_error = "El título y el mensaje son obligatorios."

        elif tipo == "Individual" and not alumno_id:
            mensaje_error = "Seleccioná un alumno."

        else:

            if tipo == "General":
                alumno_id = None
            else:
                alumno_id = int(alumno_id)

            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO notificaciones (
                    alumno_id,
                    titulo,
                    mensaje,
                    tipo,
                    fecha_creacion,
                    activa
                )
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                alumno_id,
                titulo,
                mensaje,
                tipo,
                ahora
            ))

            conexion.commit()
            conexion.close()

            return redirect(url_for("notificaciones_admin"))

    conexion.close()

    return render_template(
        "nueva_notificacion_admin.html",
        alumnos=alumnos,
        mensaje_error=mensaje_error
    )

@app.route("/admin/notificaciones/<int:notificacion_id>/desactivar", methods=["POST"])
def desactivar_notificacion_admin(notificacion_id):

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] != "administrador":
        return "Acceso no autorizado."

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE notificaciones
        SET activa = 0
        WHERE id = ?
    """, (notificacion_id,))

    conexion.commit()
    conexion.close()

    return redirect(url_for("notificaciones_admin"))

if __name__ == "__main__":
    app.run(debug=True)
