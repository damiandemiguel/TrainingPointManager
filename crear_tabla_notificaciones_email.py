
from database import conectar

conexion = conectar()

try:
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones_email (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bono_id INTEGER NOT NULL,
            tipo_notificacion TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            fecha_envio TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (bono_id) REFERENCES bonos(id),
            UNIQUE (
                bono_id,
                tipo_notificacion,
                fecha_vencimiento
            )
        )
    """)

    conexion.commit()
    print("Tabla de notificaciones creada correctamente.")

finally:
    conexion.close()
