from flask import Blueprint, jsonify, request
from config.db import db_connection



productos_bp = Blueprint('productos', __name__)


def validar_campos_requeridos(data, campos):
    faltantes = [campo for campo in campos if not data.get(campo)]
    if faltantes: 
        return False, f"Rellena los siguientes datos faltantes: {',' .join(faltantes)}"
    return True, None

@productos_bp.route('/mostrar', methods=['GET'])
def obtener_productos():
    connection = db_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM productos;"
    cursor.execute(query)
    productos = cursor.fetchall()
    cursor.close()
    connection.close()
    if not productos:
        return jsonify({"error":"no hay productos registrados"}), 404
    else:
        return jsonify({"Productos": productos})
    
@productos_bp.route ('/agregar', methods=['POST'])
def Agregar_Productos():
    data = request.get_json()
    campos_requeridos = ["product_name", "price", "barcode", "stock"]
    valido, mensaje = validar_campos_requeridos(data, campos_requeridos)
    if not valido:
        return jsonify({"error:":mensaje}), 400
    product_name = data.get("product_name")
    price = data.get("price")
    barcode = data.get("barcode")
    stock =data.get("stock")

    connection = db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM productos WHERE product_name = %s", (product_name,))
        existing_product = cursor.fetchone()
        if existing_product:
            return jsonify({"error":"ya hay un producto con ese nombre"}), 400
        cursor.execute('''INSERT INTO productos (product_name, price, barcode,stock)
                       VALUES (%s,%s,%s,%s)''', (product_name, price, barcode, stock))
        cursor.connection.commit()
        return jsonify({"mensaje": f"El producto{product_name}, fue creado"})
    except Exception as error:
        return jsonify({"error":f"El error registrado es: {str(error)}"}), 500
    
    finally:
        cursor.close()
        connection.close()



    