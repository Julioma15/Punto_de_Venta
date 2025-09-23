from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv #Sirve patra extraer las vasriables del .env al sistema operativo

#Cargar de .env las variables de entorno
load_dotenv()

#Creando una instancia de MySQL
mysql = MySQL()

#Funcion para conectarse a la base de datos. Se le pasa la app, porque es la variable que inicializa los procesos 
def init_db(app): 
    #Configurar la BD con la instancia de flask
    app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
    app.config['MYSQL_USER'] = os.getenv('DB_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('DB_NAME')
    app.config['MYSQL_PORT'] = int (os.getenv('DB_PORT'))

    #Inicializar la conexion 
    mysql.init_app(app)

#Definimos el cursor. Esto permitira la conexion
def get_db_connection ():
    #Devuelve un cursor para interactuar con la DB
    try: 
        connection = mysql.connection
        return connection.cursor()
    except Exception as e: 
        raise RuntimeError(f"Error al conectarse a la base de datos: {e}")