from flask import Flask
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv
from routes.prueba import productos_bp

#Cargar las Variables de entorno
load_dotenv()


#Iniciamos la APP
def create_app():
    #Instanciamos la app
    app= Flask(__name__)
    #configuracion del JWT secreto de .env
    app.config['JWT_SECRET_KEY']= os.getenv('JWT_SECRET_KEY')
    jwt=JWTManager(app)

    #registramos el blueprint
    app.register_blueprint(productos_bp, url_prefix='/api') 

    return app

app = create_app()

if __name__=='__main__':
    #obtenemos el puerto
    port= int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)


