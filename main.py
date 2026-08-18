import json
import unicodedata
from datetime import datetime

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return texto

def calcular_edad(fecha_nacimiento):
    fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%d/%m/%Y")
    hoy = datetime.today()

    edad = hoy.year - fecha_nacimiento.year

    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    return edad

def validar_fecha_nacimiento(fecha_nacimiento):
    try:
        fecha = datetime.strptime(fecha_nacimiento, "%d/%m/%Y")
        edad = calcular_edad(fecha_nacimiento)

        if 16 <= edad <= 80:
            return True
        else:
            print("La edad debe estar entre 16 y 80 años.")
            return False

    except ValueError:
        print("La fecha no es válida. Use el formato DD/MM/AAAA.")
        return False

def validar_email(email):
    if "@" in email and "." in email.split("@")[1]:
        return True
    else:
        print("El e-mail no es válido.")
        return False        

def email_ya_existe(email):
    for alumno in alumnos:
        if alumno["email"].lower() == email.lower():
            return True

    return False

def agregar_alumno():
    print()
    print("--- AGREGAR ALUMNO ---")
    print()

    nombre = input("Nombre y apellido: ")

    while True:
        email = input("E-mail: ")

        if not validar_email(email):
            continue

        if email_ya_existe(email):
            print("Ya existe un alumno registrado con ese e-mail.")
            continue

        break
        break

    while True:
        fecha_nacimiento = input("Fecha de nacimiento (DD/MM/AAAA): ")

        if validar_fecha_nacimiento(fecha_nacimiento):
            break

    if alumnos:
        id_alumno = max(alumno["id"] for alumno in alumnos) + 1
    else:
        id_alumno = 1

    nuevo_alumno = {
        "id": id_alumno,
        "nombre": nombre,
        "email": email,
        "fecha_nacimiento": fecha_nacimiento
    }

    alumnos.append(nuevo_alumno)

    with open("alumnos.json", "w") as archivo:
        json.dump(alumnos, archivo, indent=4)

    print()
    print("Alumno agregado correctamente.")
    print("ID asignado:", id_alumno)

def mostrar_alumnos():
    print()
    print("--- LISTA DE ALUMNOS ---")
    print()

    for alumno in alumnos:
        edad = calcular_edad(alumno["fecha_nacimiento"])

        print("ID:", alumno["id"])
        print("Nombre:", alumno["nombre"])
        print("E-mail:", alumno["email"])
        print("Fecha de nacimiento:", alumno["fecha_nacimiento"])
        print("Edad:", edad, "años")
        print("-----------------------")

def buscar_alumno():
    print()
    print("--- BUSCAR ALUMNO ---")
    print()

    busqueda = input("Ingrese el nombre o ID del alumno: ")

    encontrados = []

    for alumno in alumnos:
        if normalizar(busqueda) in normalizar(alumno["nombre"]) or busqueda == str(alumno["id"]):
            encontrados.append(alumno)

    if len(encontrados) == 0:
        print()
        print("No se encontró ningún alumno.")

    else:
        for alumno in encontrados:
            print()
            print("Alumno encontrado:")
            print("ID:", alumno["id"])
            print("Nombre:", alumno["nombre"])
            print("E-mail:", alumno["email"])
            print("Fecha de nacimiento:", alumno["fecha_nacimiento"])
            print("Edad:", calcular_edad(alumno["fecha_nacimiento"]), "años")      

def modificar_alumno():
    print()
    print("--- MODIFICAR ALUMNO ---")
    print()

    nombre_buscar = input("Ingrese el nombre o ID del alumno: ")

    encontrados = []

    for alumno in alumnos:
        if normalizar(nombre_buscar) in normalizar(alumno["nombre"]) or nombre_buscar == str(alumno["id"]):
            encontrados.append(alumno)

    if len(encontrados) == 0:
        print()
        print("No se encontró ningún alumno.")
        return

    elif len(encontrados) == 1:
        alumno = encontrados[0]

    else:
        print()
        print("Se encontraron varios alumnos:")
        print()

        for i, alumno_encontrado in enumerate(encontrados, start=1):
            print(f"{i}. {alumno_encontrado['nombre']}")
            print(f"   E-mail: {alumno_encontrado['email']}")
            print(f"   ID: {alumno_encontrado['id']}")
            print()

        seleccion = int(input("Seleccione el número del alumno que desea modificar: "))
        alumno = encontrados[seleccion - 1]

    print()
    print("Alumno seleccionado:")
    print("ID:", alumno["id"])
    print("Nombre:", alumno["nombre"])
    print("E-mail:", alumno["email"])
    print("Fecha de nacimiento:", alumno["fecha_nacimiento"])
    print("Edad:", calcular_edad(alumno["fecha_nacimiento"]), "años")

    print()
    print("¿Qué dato desea modificar?")
    print("1. Nombre y apellido")
    print("2. E-mail")
    print("3. Fecha de nacimiento")
    print("4. Cancelar")

    opcion_modificar = input("Seleccione una opción: ")

    if opcion_modificar == "1":
        nuevo_nombre = input("Ingrese el nuevo nombre y apellido: ")

        alumno["nombre"] = nuevo_nombre

        with open("alumnos.json", "w") as archivo:
            json.dump(alumnos, archivo, indent=4)

        print()
        print("Nombre modificado correctamente.")

    elif opcion_modificar == "2":
        while True:
            nuevo_email = input("Ingrese el nuevo e-mail: ")

            if not validar_email(nuevo_email):
                continue

            if nuevo_email.lower() != alumno["email"].lower() and email_ya_existe(nuevo_email):
                print("Ya existe otro alumno registrado con ese e-mail.")
                continue

            break

        alumno["email"] = nuevo_email

        with open("alumnos.json", "w") as archivo:
            json.dump(alumnos, archivo, indent=4)

        print()
        print("E-mail modificado correctamente.")

    elif opcion_modificar == "3":
        while True:
            nueva_fecha = input("Ingrese la nueva fecha de nacimiento (DD/MM/AAAA): ")

            if validar_fecha_nacimiento(nueva_fecha):
                break

        alumno["fecha_nacimiento"] = nueva_fecha

        with open("alumnos.json", "w") as archivo:
            json.dump(alumnos, archivo, indent=4)

        print()
        print("Fecha de nacimiento modificada correctamente.")

    elif opcion_modificar == "4":
        print()
        print("Modificación cancelada.")

    else:
        print()
        print("Opción no válida.")

def eliminar_alumno():
    print()
    print("--- ELIMINAR ALUMNO ---")
    print()

    nombre_buscar = input("Ingrese el nombre o ID del alumno: ")

    encontrados = []

    for alumno in alumnos:
        if normalizar(nombre_buscar) in normalizar(alumno["nombre"]) or nombre_buscar == str(alumno["id"]):
            encontrados.append(alumno)

    if len(encontrados) == 0:
        print()
        print("No se encontró ningún alumno.")

    elif len(encontrados) == 1:
        alumno = encontrados[0]

    else:
        print()
        print("Se encontraron varios alumnos:")
        print()

        for i, alumno_encontrado in enumerate(encontrados, start=1):
            print(f"{i}. {alumno_encontrado['nombre']}")
            print(f"   E-mail: {alumno_encontrado['email']}")
            print(f"   Fecha de nacimiento: {alumno_encontrado['fecha_nacimiento']}")
            print(f"   Edad: {calcular_edad(alumno_encontrado['fecha_nacimiento'])} años")
            print(f"   ID: {alumno_encontrado['id']}")
            print()

        seleccion = int(input("Seleccione el número del alumno que desea eliminar: "))
        alumno = encontrados[seleccion - 1]

    if len(encontrados) > 0:
        print()
        print("Alumno seleccionado:")
        print("ID:", alumno["id"])
        print("Nombre:", alumno["nombre"])
        print("E-mail:", alumno["email"])
        print("Fecha de nacimiento:", alumno["fecha_nacimiento"])
        print("Edad:", calcular_edad(alumno["fecha_nacimiento"]), "años")

        print()
        print("¿Está seguro de eliminar este alumno?")
        print("1. Sí")
        print("2. No")

        confirmacion = input("Seleccione una opción: ")

        if confirmacion == "1":
            alumnos.remove(alumno)

            with open("alumnos.json", "w") as archivo:
                json.dump(alumnos, archivo, indent=4)

            print()
            print("Alumno eliminado correctamente.")

        elif confirmacion == "2":
            print()
            print("Eliminación cancelada.")

def mostrar_menu():
    print()
    print("===================================")
    print("      TRAINING POINT MANAGER")
    print("===================================")
    print()

    print("1. Agregar alumno")
    print("2. Mostrar alumnos")
    print("3. Buscar alumno")
    print("4. Modificar alumno")
    print("5. Eliminar alumno")
    print("6. Salir")
    print()

try:
    with open("alumnos.json", "r") as archivo:
        alumnos = json.load(archivo)
except FileNotFoundError:
    alumnos = []

while True:
    mostrar_menu()
    opcion = input("Seleccione una opción: ")

    if opcion == "1":
        agregar_alumno()

    elif opcion == "2":
        mostrar_alumnos()

    elif opcion == "3":
        buscar_alumno()

    elif opcion == "4":
        modificar_alumno()

    elif opcion == "5":
        eliminar_alumno()

    elif opcion == "6":
        print()
        print("Saliendo de Training Point Manager.")
        break

    else:
        print()
        print("Opción no válida.")