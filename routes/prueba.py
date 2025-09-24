from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
import os
from dotenv import load_dotenv
from flask_mysqldb import MySQL
from config.db import connection

load_dotenv()
mysql = MySQL()

#creamos el blueprint
tareas_bp = Blueprint('tareas', __name__)
productos_bp = Blueprint('productos', __name__)

def validar_campos_requeridos(data, campos):
    faltantes = [campo for campo in campos if not data.get(campo)]
    if faltantes:
        return False, f"ʕ•́ᴥ•̀ʔっ Faltan los siguientes campos: {', '.join(faltantes)}"
    return True, None

# ------ ENDPOINTS -------


# Endpoint para obtener todos los productos
@productos_bp.route('/productos', methods=['GET'])
#@jwt_required()
def obtener_productos():
    cursor = connection()
    query = "SELECT * FROM Productos;"
    cursor.execute(query)
    productos = cursor.fetchall()
    cursor.close()
    if not productos:
        return jsonify({"error": "No hay productos registrados"}), 404
    else:
        return jsonify({"productos": productos}), 200