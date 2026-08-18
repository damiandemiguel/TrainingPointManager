from flask import Flask, render_template
import json

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/alumnos")
def mostrar_alumnos():
    with open("alumnos.json", "r") as archivo:
        alumnos = json.load(archivo)

    return render_template("alumnos.html", alumnos=alumnos)

@app.route("/agregar")
def agregar_alumno():
    return render_template("agregar.html")

if __name__ == "__main__":
    app.run(debug=True)