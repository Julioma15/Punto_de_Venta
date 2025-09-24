import os
from psycopg2 import psycopg2
from dotenv import load_dotenv #Sirve patra extraer las vasriables del .env al sistema operativo

#Cargar de .env las variables de entorno
load_dotenv()

#Funcion para conectarse a la base de datos. Se le pasa la app, porque es la variable que inicializa los procesos 
try:
    # Conexión a la base de datos
    connection = psycopg2.connect(
        DB_NAME= os.getenv('DB_NAME'),
        DB_USER= os.getenv('DB_USER'),
        DB_PASSWORD= os.getenv('DB_PASSWORD'),
        BD_HOST= os.getenv('DB_HOST'),
        dB_PORT= os.getenv('DB_PORT')
    )
    print("Conexión exitosa a la base de datos")

    # Crear un cursor para ejecutar consultas
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"Versión de PostgreSQL: {db_version}")

except Exception as e:
    print(f"Error al conectar: {e}")

finally:
    # Cerrar la conexión
    if connection:
        cursor.close()
        connection.close()
        print("Conexión cerrada")
