
import os
import ssl
import smtplib
from email.message import EmailMessage


def enviar_correo_recuperacion(destinatario, enlace):
    mensaje = EmailMessage()

    mensaje["Subject"] = "Recuperá tu contraseña - Training Point"
    mensaje["From"] = os.environ["MAIL_FROM"]
    mensaje["To"] = destinatario

    mensaje.set_content(
        "¡Hola!\n\n"
        "Recibimos una solicitud para recuperar tu contraseña "
        "de Training Point.\n\n"
        "Para crear una contraseña nueva, ingresá al siguiente enlace:\n\n"
        f"{enlace}\n\n"
        "Este enlace vence dentro de 30 minutos y solo puede "
        "utilizarse una vez.\n\n"
        "Si no solicitaste este cambio, podés ignorar el mensaje.\n\n"
        "Training Point"
    )

    with smtplib.SMTP_SSL(
        os.environ["MAIL_HOST"],
        465,
        timeout=20,
        context=ssl.create_default_context()
    ) as servidor:
        servidor.login(
            os.environ["MAIL_USERNAME"],
            os.environ["MAIL_PASSWORD"]
        )

        servidor.send_message(mensaje)
