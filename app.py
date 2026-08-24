from flask import Flask, render_template, request, redirect, url_for, session
session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

from database import conectar

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads/perfiles"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.secret_key = "clave-temporal-training-point"

def archivo_permitido(nombre):

    return (
        "." in nombre
        and nombre.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
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

        conexion.close()

        return render_template(
            "admin.html",
            total_alumnos=total_alumnos,
            alumnos_activos=alumnos_activos,
            alumnos_inactivos=alumnos_inactivos,
            fichas_salud=fichas_salud
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

    cursor.execute("SELECT id FROM alumnos WHERE usuario_id = ?", (session["usuario_id"],))
    alumno = cursor.fetchone()

    if alumno is None:
        conexion.close()
        return "No se encontró el perfil del alumno."

    alumno_id = alumno["id"]

    if request.method == "POST":

        contacto_emergencia = request.form.get("contacto_emergencia", "")
        telefono_emergencia = request.form.get("telefono_emergencia", "")
        lesiones = request.form.get("lesiones", "")
        antecedentes = request.form.get("antecedentes", "")
        observaciones = request.form.get("observaciones", "")

        cursor.execute("""
            INSERT INTO salud (
                alumno_id,
                contacto_emergencia,
                telefono_emergencia,
                lesiones,
                antecedentes,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(alumno_id) DO UPDATE SET
                contacto_emergencia = excluded.contacto_emergencia,
                telefono_emergencia = excluded.telefono_emergencia,
                lesiones = excluded.lesiones,
                antecedentes = excluded.antecedentes,
                observaciones = excluded.observaciones
        """, (
            alumno_id,
            contacto_emergencia,
            telefono_emergencia,
            lesiones,
            antecedentes,
            observaciones
        ))

        conexion.commit()

    cursor.execute("""
        SELECT contacto_emergencia,
               telefono_emergencia,
               lesiones,
               antecedentes,
               observaciones
        FROM salud
        WHERE alumno_id = ?
    """, (alumno_id,))

    salud = cursor.fetchone()

    conexion.close()

    return render_template("salud.html", salud=salud)

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
               telefono, direccion, certificado_medico, activo, foto_perfil
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
