from flask import Blueprint, jsonify, request
from config.db import db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity

productos_bp = Blueprint('productos', __name__)

# ---------------- Helper functions ----------------
def validar_campos_requeridos(data, campos):
    faltantes = [campo for campo in campos if not data.get(campo)]
    if faltantes: 
        return False, f"Please provide the following missing fields: {', '.join(faltantes)}"
    return True, None

def _obtener_rol_activo(cursor, user_id):
    cursor.execute(
        "SELECT role FROM usuarios WHERE id_user = %s AND active = TRUE",
        (user_id,)
    )
    row = cursor.fetchone()
    return (row[0] or "").lower() if row else None

def _autorizar_roles(rol_actual, roles_permitidos):
    return rol_actual in roles_permitidos


# ---------------- Endpoints ----------------

@productos_bp.route('/mostrar', methods=['GET'])
@jwt_required()
def obtener_productos():
    current_user_id = get_jwt_identity()
    connection = db_connection()
    cursor = connection.cursor()
    try:
        rol_actual = _obtener_rol_activo(cursor, current_user_id)
        if not rol_actual:
            return jsonify({"error": "Invalid token or user not found"}), 401
        if not _autorizar_roles(rol_actual, {"admin", "manager", "cashier"}):
            return jsonify({"error": "Unauthorized user (only admin/manager/cashier allowed)"}), 403

        cursor.execute("SELECT * FROM productos;")
        productos = cursor.fetchall()
        if not productos:
            return jsonify({"error": "No products found"}), 404
        return jsonify({"products": productos}), 200
    except Exception as e:
        return jsonify({"error": f"Error in obtener_productos: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()


@productos_bp.route('/<int:id_product>', methods=['GET'])
@jwt_required()
def mostrar_un_producto(id_product):
    current_user_id = get_jwt_identity()
    connection = db_connection()
    cursor = connection.cursor()
    try:
        rol_actual = _obtener_rol_activo(cursor, current_user_id)
        if not rol_actual:
            return jsonify({"error": "Invalid token or user not found"}), 401
        if not _autorizar_roles(rol_actual, {"admin", "manager", "cashier"}):
            return jsonify({"error": "Unauthorized user (only admin/manager/cashier allowed)"}), 403

        cursor.execute("SELECT * FROM productos WHERE id_product = %s", (id_product,))
        producto = cursor.fetchone()
        if not producto:
            return jsonify({"error": "No product with that ID"}), 404
        return jsonify({"product": producto}), 200
    except Exception as error:
        return jsonify({"error": f"Registered error: {str(error)}"}), 500
    finally:
        cursor.close()
        connection.close()


@productos_bp.route('/barcode/<string:barcode>', methods=['GET'])
@jwt_required()
def mostrar_con_barcode(barcode):
    current_user_id = get_jwt_identity()
    connection = db_connection()
    cursor = connection.cursor()
    try:
        rol_actual = _obtener_rol_activo(cursor, current_user_id)
        if not rol_actual:
            return jsonify({"error": "Invalid token or user not found"}), 401
        if not _autorizar_roles(rol_actual, {"admin", "manager", "cashier"}):
            return jsonify({"error": "Unauthorized user (only admin/manager/cashier allowed)"}), 403

        cursor.execute("SELECT * FROM productos WHERE barcode = %s", (barcode,))
        producto = cursor.fetchone()
        if not producto:
            return jsonify({"error": "No product with that barcode"}), 404
        return jsonify({"product": producto}), 200
    except Exception as error:
        return jsonify({"error": f"Registered error: {str(error)}"}), 500
    finally:
        cursor.close()
        connection.close()


@productos_bp.route('/<int:id_product>', methods=['PATCH'])
@jwt_required()
def editar_producto(id_product):
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    product_name = data.get("product_name")
    price = data.get("price")
    barcode = data.get("barcode")
    stock = data.get("stock")

    connection = db_connection()
    cursor = connection.cursor()
    try:
        rol_actual = _obtener_rol_activo(cursor, current_user_id)
        if not rol_actual:
            return jsonify({"error": "Invalid token or user not found"}), 401
        if not _autorizar_roles(rol_actual, {"admin", "manager"}):
            return jsonify({"error": "Unauthorized user (only admin/manager allowed)"}), 403

        cursor.execute("SELECT 1 FROM productos WHERE id_product = %s", (id_product,))
        existe = cursor.fetchone()
        if not existe:
            return jsonify({"error": "No product with that ID"}), 404

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
            return jsonify({"error": "No fields to update"}), 400

        valores.append(id_product)
        query_update = f"UPDATE productos SET {', '.join(campos)} WHERE id_product = %s"
        cursor.execute(query_update, tuple(valores))
        connection.commit()

        return jsonify({"message": f"Product {id_product} updated successfully"}), 200
    except Exception as error:
        return jsonify({"error": f"Registered error: {str(error)}"}), 500
    finally:
        cursor.close()
        connection.close()


@productos_bp.route('/agregar', methods=['POST'])
@jwt_required()
def Agregar_Productos():
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}

    connection = db_connection()
    cursor = connection.cursor()
    try:
        rol_actual = _obtener_rol_activo(cursor, current_user_id)
        if not rol_actual:
            return jsonify({"error": "Invalid token or user not found"}), 401
        if not _autorizar_roles(rol_actual, {"admin", "manager"}):
            return jsonify({"error": "Unauthorized user (only admin/manager allowed)"}), 403

        campos_requeridos = ["product_name", "price", "barcode", "stock"]
        valido, mensaje = validar_campos_requeridos(data, campos_requeridos)
        if not valido:
            return jsonify({"error": mensaje}), 400

        product_name = data.get("product_name")
        price = data.get("price")
        barcode = data.get("barcode")
        stock = data.get("stock")

        cursor.execute("SELECT 1 FROM productos WHERE product_name = %s", (product_name,))
        existing_product = cursor.fetchone()
        if existing_product:
            return jsonify({"error": "Product with that name already exists"}), 400

        cursor.execute(
            "INSERT INTO productos (product_name, price, barcode, stock) VALUES (%s, %s, %s, %s)",
            (product_name, price, barcode, stock)
        )
        connection.commit()
        return jsonify({"message": f"Product {product_name} created successfully"}), 201
    except Exception as error:
        return jsonify({"error": f"Registered error: {str(error)}"}), 500
    finally:
        cursor.close()
        connection.close()
