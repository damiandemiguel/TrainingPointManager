import json
import unicodedata

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return texto

def agregar_alumno():
    print()
    print("--- AGREGAR ALUMNO ---")
    print()

    nombre = input("Nombre: ")

    while True:
        try:
            edad = int(input("Edad: "))

            if 16 <= edad <= 80:
                break
            else:
                print("La edad debe estar entre 16 y 80 años.")

        except ValueError:
            print("La edad debe ser un número.")

    if alumnos:
        id_alumno = max(alumno[0] for alumno in alumnos) + 1
    else:
        id_alumno = 1

    alumnos.append([id_alumno, nombre, edad])

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
        print("ID:", alumno[0])
        print("Nombre:", alumno[1])
        print("Edad:", alumno[2])
        print("-----------------------")

def buscar_alumno():
    print()
    print("--- BUSCAR ALUMNO ---")
    print()

    busqueda = input("Ingrese el nombre o ID del alumno: ")

    encontrados = []

    for alumno in alumnos:
        if normalizar(busqueda) in normalizar(alumno[1]) or busqueda == str(alumno[0]):
            encontrados.append(alumno)

    if len(encontrados) == 0:
        print()
        print("No se encontró ningún alumno.")

    else:
        for alumno in encontrados:
            print()
            print("Alumno encontrado:")
            print("ID:", alumno[0])
            print("Nombre:", alumno[1])
            print("Edad:", alumno[2])        

def modificar_alumno():
    print()
    print("--- MODIFICAR ALUMNO ---")
    print()

    nombre_buscar = input("Ingrese el nombre o ID del alumno: ")

    encontrados = []

    for alumno in alumnos:
        if normalizar(nombre_buscar) in normalizar(alumno[1]) or nombre_buscar == str(alumno[0]):
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
            print(f"{i}. {alumno_encontrado[1]}")
            print(f"   Edad: {alumno_encontrado[2]}")
            print(f"   ID: {alumno_encontrado[0]}")
            print()

        seleccion = int(input("Seleccione el número del alumno que desea modificar: "))
        alumno = encontrados[seleccion - 1]

    if len(encontrados) > 0:
        print()
        print("Alumno seleccionado:")
        print("ID:", alumno[0])
        print("Nombre:", alumno[1])
        print("Edad:", alumno[2])

        print()
        print("¿Qué dato desea modificar?")
        print("1. Nombre")
        print("2. Edad")
        print("3. Cancelar")

        opcion_modificar = input("Seleccione una opción: ")

        if opcion_modificar == "1":
            nuevo_nombre = input("Ingrese el nuevo nombre: ")
            alumno[1] = nuevo_nombre

            with open("alumnos.json", "w") as archivo:
                json.dump(alumnos, archivo, indent=4)

            print()
            print("Nombre modificado correctamente.")

        elif opcion_modificar == "2":
            nueva_edad = input("Ingrese la nueva edad: ")
            alumno[2] = nueva_edad

            with open("alumnos.json", "w") as archivo:
                json.dump(alumnos, archivo, indent=4)

            print()
            print("Edad modificada correctamente.")

        elif opcion_modificar == "3":
            print()
            print("Modificación cancelada.")

def eliminar_alumno():
    print()
    print("--- ELIMINAR ALUMNO ---")
    print()

    nombre_buscar = input("Ingrese el nombre o ID del alumno: ")

    encontrados = []

    for alumno in alumnos:
        if normalizar(nombre_buscar) in normalizar(alumno[1]) or nombre_buscar == str(alumno[0]):
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
            print(f"{i}. {alumno_encontrado[1]}")
            print(f"   Edad: {alumno_encontrado[2]}")
            print(f"   ID: {alumno_encontrado[0]}")
            print()

        seleccion = int(input("Seleccione el número del alumno que desea eliminar: "))
        alumno = encontrados[seleccion - 1]

    if len(encontrados) > 0:
        print()
        print("Alumno seleccionado:")
        print("ID:", alumno[0])
        print("Nombre:", alumno[1])
        print("Edad:", alumno[2])

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