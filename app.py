from flask import Flask, render_template, request, redirect, url_for, session
session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

from database import conectar

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads/perfiles"
CERTIFICADOS_FOLDER = "static/uploads/certificados"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CERTIFICADOS_FOLDER"] = CERTIFICADOS_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_CERTIFICADO_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

app.secret_key = "clave-temporal-training-point"

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
            SELECT COUNT(*)
            FROM alumnos
            LEFT JOIN salud
                ON alumnos.id = salud.alumno_id
            WHERE salud.id IS NULL
        """)
        alumnos_sin_ficha = cursor.fetchone()[0]

        conexion.close()

        return render_template(
            "admin.html",
            total_alumnos=total_alumnos,
            alumnos_activos=alumnos_activos,
            alumnos_inactivos=alumnos_inactivos,
            fichas_salud=fichas_salud,
            alumnos_sin_certificado=alumnos_sin_certificado,
            alumnos_sin_ficha=alumnos_sin_ficha
        )

    return redirect(url_for("perfil_alumno"))

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

    return render_template(
        "salud.html",
        salud=salud,
        certificado_medico=certificado_medico,
        fecha_certificado=fecha_certificado
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

    return render_template(
        "perfil_alumno_admin.html",
        alumno=alumno
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

    return render_template(
        "ficha_salud_admin.html",
        ficha=ficha
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


if __name__ == "__main__":
    app.run(debug=True)
