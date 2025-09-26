#PAME

# POST /auth/login
# Inicia sesión y devuelve token.
# GET /me
# Devuelve perfil del usuario autenticado.

from flask import Blueprint, jsonify, request
from config.db import db_connection
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt

users_bp = Blueprint('users', __name__)

#inicializamos el Bycript para hashear las contraseñas
bcrypt = Bcrypt()

#-------------- ENDPOINTS USUARIOS -----------------#
#VALIDAMOS QUE SE PONGAN TODOS LOS CAMPOS REQUERIDOS
def validar_campos_requeridos(data, campos):
    faltantes = [campo for campo in campos if not data.get(campo)]
    if faltantes:
        return False, f"Porfavor rellena los siguientes campos: {', '.join(faltantes)}"
    return True, None

#Lo volvemos para que solo el administrador pueda agregar usuarios?

#ENDPOINT REGRISTRAR USUARIOS
@users_bp.route('/singIn', methods=['POST'])
def obtener_productos():
    data = request.get_json()
    #validamos que esten todos los campos
    campos_requeridos = ["username", "password", "role"]
    valido, mensaje = validar_campos_requeridos(data, campos_requeridos)
    if not valido:
        return jsonify({"error": mensaje}), 400
    
    username = data.get("username")
    password = data.get("password")
    #Los roles admitidos son admin, cashier, manager 
    role = data.get("role")

    #obtenemos la conexion a la base de datos
    connection = db_connection()
    cursor = connection.cursor()

    try: 
        # verificar si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"error" : "Ya hay un usuario registrado con ese nombre de usuario"}), 400
        # Hash a la contraseña con Flask-Bcrypt
        # .decode('utf-8') se utiliza para convertir el hash de bytes a cadena antes de almacenarlo en la base de datos
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        #insertar el nuevo usuario
        cursor.execute('''INSERT INTO usuarios (username, password, role)
                       VALUES (%s, %s, %s)''', 
                       (username, hashed_password, role))
        cursor.connection.commit()
        return jsonify({"mensaje" : f"El usuario {username}, [{role}] ha sido creado"})
    
    except Exception as error:
        return jsonify({"error" : f"Error el registrar el usuario: {str(error)}"}), 500
    
    finally:
        # asegurarse de cerrar la conexion y el cursor a la base de datos despues de la operacion
        cursor.close()
        connection.close()