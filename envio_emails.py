from email.message import EmailMessage

import os
import smtplib
import ssl

from dotenv import load_dotenv


load_dotenv()


def probar_conexion_gmail():
    servidor = os.getenv("MAIL_HOST")
    puerto = int(os.getenv("MAIL_PORT", "587"))
    usuario = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")

    if not all([servidor, usuario, password]):
        print("Error: faltan datos de configuración.")
        return False

    try:
        with smtplib.SMTP_SSL(
            servidor,
            465,
            timeout=15,
            context=ssl.create_default_context()
        ) as smtp:

            print("1. Conexión SSL establecida")

            smtp.ehlo()
            print("2. EHLO correcto")

            smtp.login(usuario, password)
            print("3. Autenticación correcta")

            print("Conexión y autenticación con Gmail exitosas.")
            return True

    except smtplib.SMTPException as error:
        print("Error de SMTP:", error)
        return False

    except (OSError, ValueError) as error:
        print("Error de conexión o configuración:", error)
        return False

def enviar_email(destinatario, asunto, mensaje):
    load_dotenv()

    servidor = os.getenv("MAIL_HOST")
    usuario = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    remitente = os.getenv("MAIL_FROM") or usuario

    if not all([servidor, usuario, password, remitente]):
        print("Error: faltan datos de configuración.")
        return False

    correo = EmailMessage()
    correo["From"] = remitente
    correo["To"] = destinatario
    correo["Subject"] = asunto
    correo.set_content(mensaje)

    try:
        with smtplib.SMTP_SSL(
            servidor,
            465,
            timeout=15,
            context=ssl.create_default_context()
        ) as smtp:

            smtp.login(usuario, password)
            smtp.send_message(correo)

        return True

    except (smtplib.SMTPException, OSError) as error:
        print("Error al enviar correo:", error)
        return False

if __name__ == "__main__":
    probar_conexion_gmail()