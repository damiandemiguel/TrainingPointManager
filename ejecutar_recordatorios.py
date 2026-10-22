import os
from datetime import datetime
from zoneinfo import ZoneInfo

from procesar_recordatorios import (
    procesar_recordatorios,
    envio_real_de_prueba
)


def ejecutar():
    ahora = datetime.now(
        ZoneInfo("America/Argentina/Buenos_Aires")
    )

    modo = os.getenv(
        "MODO_RECORDATORIOS", "simulacion"
    ).strip().lower()

    print("=" * 50)
    print("TRAINING POINT - REVISIÓN DE RECORDATORIOS")
    print("Fecha y hora:", ahora.strftime("%d/%m/%Y %H:%M:%S"))
    print("Modo:", modo)

    if modo == "simulacion":
        procesar_recordatorios(simulacion=True)

    elif modo == "prueba_email":
        procesar_recordatorios(
            simulacion=False,
            funcion_envio=envio_real_de_prueba
        )

    else:
        raise ValueError(
            f"Modo de recordatorios no permitido: {modo}"
        )

    print("Revisión finalizada.")
    print("=" * 50)


if __name__ == "__main__":
    ejecutar()