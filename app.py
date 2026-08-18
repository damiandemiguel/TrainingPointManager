from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
import json

from database import conectar

app = Flask(__name__)

app.secret_key = "clave-temporal-training-point"


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


@app.route("/panel")
def panel():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    if session["rol"] == "administrador":
        return "Panel del administrador"

    return "Panel del alumno"


@app.route("/alumnos")
def mostrar_alumnos():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    with open("alumnos.json", "r") as archivo:
        alumnos = json.load(archivo)

    return render_template("alumnos.html", alumnos=alumnos)


@app.route("/agregar")
def agregar_alumno():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("agregar.html")


if __name__ == "__main__":
    app.run(debug=True)