from recordatorios_abonos import (
    preparar_recordatorios,
    reservar_recordatorio,
    actualizar_estado_recordatorio
)

from envio_emails import enviar_email


def envio_real_de_prueba(destinatario, asunto, mensaje):
    correo_autorizado = "trainingpoint.ef@gmail.com"

    if destinatario.lower().strip() != correo_autorizado:
        print(
            "[BLOQUEADO] Destinatario no autorizado:",
            destinatario
        )
        return False

    return enviar_email(
        destinatario,
        asunto,
        mensaje
    )


def envio_simulado(destinatario, asunto, mensaje):
    print(f"[ENVÍO SIMULADO] Destinatario: {destinatario}")
    return True


def procesar_recordatorios(
    simulacion=True,
    funcion_envio=None
):
    if not simulacion:
        if funcion_envio is None:
            raise ValueError(
                "Para procesar recordatorios se debe "
                "indicar explícitamente una función de envío."
            )

        if funcion_envio is envio_simulado:
            raise ValueError(
                "No se puede utilizar envio_simulado "
                "como función de envío real."
            )

    recordatorios = preparar_recordatorios()

    print(
        "Recordatorios encontrados:",
        len(recordatorios)
    )

    for recordatorio in recordatorios:

        bono_id = recordatorio["bono_id"]
        fecha_vencimiento = recordatorio["fecha_vencimiento"]
        destinatario = recordatorio["destinatario"]

        if simulacion:
            print(
                f"[SIMULACIÓN] Bono {bono_id}: "
                "se evaluaría su envío"
            )
            continue

        reservado = reservar_recordatorio(
            bono_id,
            fecha_vencimiento,
            destinatario
        )

        if not reservado:
            print(
                f"Bono {bono_id}: "
                "ya tiene una reserva registrada"
            )
            continue

        try:
            enviado = funcion_envio(
                destinatario,
                recordatorio["asunto"],
                recordatorio["mensaje"]
            )

        except Exception as error:
            print(
                f"Bono {bono_id}: error durante el envío: {error}"
            )
            # Un error no siempre significa que el correo
            # no haya sido aceptado. Conservamos Pendiente
            # para evitar un reintento automático.
            continue

        if enviado is True:
            actualizado = actualizar_estado_recordatorio(
                bono_id,
                fecha_vencimiento,
                "Enviado"
            )

            print(
                f"Bono {bono_id}: "
                f"envío confirmado, registro actualizado: {actualizado}"
            )
        else:
            print(
                f"Bono {bono_id}: "
                "envío no confirmado; queda Pendiente"
            )


if __name__ == "__main__":
    procesar_recordatorios(simulacion=True)