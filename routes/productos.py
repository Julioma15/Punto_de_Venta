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
    

@productos_bp.route('/<int:id_product>', methods=['GET'])
def mostrar_un_producto(id_product):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        query = "SELECT * FROM productos WHERE id_product = %s"
        cursor.execute(query, (id_product,))
        producto = cursor.fetchone()
        if not producto:
            return jsonify({"error":"no existe producto con ese id"}), 404
        return jsonify({"Producto ": producto}), 200
    except Exception as error:
        return jsonify({"error":f"El error registrado es: {str(error)}"}), 500
    
    finally:
        cursor.close()
        connection.close()


@productos_bp.route('/<string:barcode>', methods=['GET'])
def mostrar_con_barcode(barcode):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        query = "SELECT * FROM productos WHERE barcode = %s"
        cursor.execute(query, (barcode, ))
        producto = cursor.fetchone()
        if not producto:
            return jsonify({"error":"no existe producto con ese codigo de barras"}),404
        return jsonify({"Producto ": producto}),200
    except Exception as error:
        return jsonify({"error":f"El error registrado es: {str(error)}"}), 500
    
    finally:
        cursor.close()
        connection.close()
    

@productos_bp.route('/<int:id_product>', methods= ['PATCH'])
def editar_producto(id_product):
    data = request.get_json() or {}
    product_name =data.get("product_name")
    price = data.get("price")
    barcode = data.get("barcode")
    stock =data.get("stock")
    connection = db_connection()
    cursor = connection.cursor()

    try:
        query = "SELECT * FROM productos WHERE id_product = %s"
        cursor.execute(query, (id_product ,))
        producto =cursor.fetchone()
        if not producto:
            return jsonify({"error": "No existe producto con ese id"}),404
        #Funcionamiento del patch
        campos = []
        valores = []

        if product_name is not None:
            campos.append("product_name = %s")
            valores.append(product_name)

        if price is not None:
            campos.append("price = %s")
            valores.append(price)

        if barcode is not None:
            campos.append("barcode = %s")
            valores.append(barcode)

        if stock is not None:
            campos.append("stock = %s")
            valores.append(stock)
        
        if not campos:
            return jsonify({"error":"no hay datos para actualizar"}), 400
        
        valores.append(id_product)
        query_update = f"UPDATE productos SET {', '.join(campos)} WHERE id_product = %s "
        cursor.execute(query_update, tuple(valores))
        connection.commit()

        return jsonify({"mensaje":f"Producto {id_product} fue actualizado"}),200
    
    except Exception as error:
        return jsonify({"error": f"El error registrado es: {str(error)}"}), 500

    finally:
        cursor.close()
        connection.close()
        
        


        


          

    
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



    