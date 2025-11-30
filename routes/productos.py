from flask import Blueprint, jsonify, request
from config.db import db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid
import cloudinary
import cloudinary.uploader

productos_bp = Blueprint('productos', __name__)

# configuración de cloudinary
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

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

    # Detectar si viene como JSON o form-data
    if request.is_json:
        data = request.get_json() or {}
        imagen_file = None
    else:
        data = request.form.to_dict()
        imagen_file = request.files.get("imagen")

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

        # Verificar existencia del producto
        cursor.execute("""
            SELECT imagen_url 
            FROM productos 
            WHERE id_product = %s
        """, (id_product,))
        producto = cursor.fetchone()

        if not producto:
            return jsonify({"error": "No product with that ID"}), 404

        imagen_actual_url = producto[0]

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

        # -------------------------------------------------------
        #   SI VIENE UNA IMAGEN NUEVA, SUBIR A CLOUDINARY
        # -------------------------------------------------------
        nueva_imagen_url = None
        nueva_thumbnail_url = None

        if imagen_file and imagen_file.filename != "":
            if not ALLOWED_EXTENSIONS(imagen_file.filename):
                return jsonify({
                    "error": f"Tipo de archivo no permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"
                }), 400

            try:
                upload_result = cloudinary.uploader.upload(
                    imagen_file,
                    folder="pos_productos",
                    transformation=[
                        {'width': 1200, 'height': 1200, 'crop': 'limit'},
                        {'quality': 'auto:good'}
                    ],
                    eager=[
                        {'width': 300, 'height': 300, 'crop': 'fill', 'gravity': 'auto'}
                    ],
                    eager_async=False
                )

                nueva_imagen_url = upload_result["secure_url"]

                if "eager" in upload_result and len(upload_result["eager"]) > 0:
                    nueva_thumbnail_url = upload_result["eager"][0]["secure_url"]
                else:
                    nueva_thumbnail_url = nueva_imagen_url

                campos.append("imagen_url = %s")
                valores.append(nueva_imagen_url)

                campos.append("imagen_thumbnail = %s")
                valores.append(nueva_thumbnail_url)

            except Exception as e:
                return jsonify({"error": f"Error subiendo imagen a Cloudinary: {str(e)}"}), 500

        if not campos:
            return jsonify({"error": "No fields to update"}), 400

        valores.append(id_product)

        query_update = f"""
            UPDATE productos 
            SET {', '.join(campos)} 
            WHERE id_product = %s
        """

        cursor.execute(query_update, tuple(valores))
        connection.commit()

        return jsonify({
            "message": f"Product {id_product} updated successfully",
            "updated_fields": campos,
            "new_image": nueva_imagen_url
        }), 200

    except Exception as error:
        connection.rollback()
        return jsonify({"error": f"Registered error: {str(error)}"}), 500
    finally:
        cursor.close()
        connection.close()

@productos_bp.route('/agregar', methods=['POST'])
@jwt_required()
def Agregar_Productos():
    current_user_id = get_jwt_identity()

    # Solo form-data
    if not request.content_type or "multipart/form-data" not in request.content_type:
        return jsonify({"error": "Unsupported Media Type. Use multipart/form-data"}), 415

    data = request.form.to_dict()
    imagen_file = request.files.get("imagen")

    connection = db_connection()
    cursor = connection.cursor()
    try:
        # Verificar rol
        rol_actual = _obtener_rol_activo(cursor, current_user_id)
        if not rol_actual:
            return jsonify({"error": "Invalid token or user not found"}), 401
        if not _autorizar_roles(rol_actual, {"admin", "manager"}):
            return jsonify({"error": "Unauthorized user (only admin/manager allowed)"}), 403

        # Validar campos requeridos
        campos_requeridos = ["product_name", "price", "barcode", "stock"]
        valido, mensaje = validar_campos_requeridos(data, campos_requeridos)
        if not valido:
            return jsonify({"error": mensaje}), 400

        product_name = data.get("product_name")
        price = data.get("price")
        barcode = data.get("barcode")
        stock = data.get("stock")

        # Verificar si el producto ya existe
        cursor.execute("SELECT 1 FROM productos WHERE product_name = %s", (product_name,))
        if cursor.fetchone():
            return jsonify({"error": "Product with that name already exists"}), 400

        # Variables para imagen
        imagen_url = None
        thumbnail_url = None

        # Subir imagen a Cloudinary si se envió
        if imagen_file and imagen_file.filename != "":
            if not ALLOWED_EXTENSIONS(imagen_file.filename):
                return jsonify({
                    "error": f"Tipo de archivo no permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"
                }), 400
            try:
                upload_result = cloudinary.uploader.upload(
                    imagen_file,
                    folder="pos_productos",
                    transformation=[
                        {'width': 1200, 'height': 1200, 'crop': 'limit'},
                        {'quality': 'auto:good'}
                    ],
                    eager=[
                        {'width': 300, 'height': 300, 'crop': 'fill', 'gravity': 'auto'}
                    ],
                    eager_async=False
                )
                imagen_url = upload_result.get("secure_url")
                if 'eager' in upload_result and len(upload_result['eager']) > 0:
                    thumbnail_url = upload_result['eager'][0].get("secure_url")
                else:
                    thumbnail_url = imagen_url

            except Exception as e:
                return jsonify({"error": f"Error subiendo imagen a Cloudinary: {str(e)}"}), 500

        # Insertar producto
        cursor.execute(
            "INSERT INTO productos (product_name, price, barcode, stock, imagen_url, imagen_thumbnail) VALUES (%s, %s, %s, %s, %s, %s)",
            (product_name, price, barcode, stock, imagen_url, thumbnail_url)
        )
        connection.commit()

        response = {
            "message": f"Product {product_name} created successfully",
            "product": {
                "product_name": product_name,
                "price": float(price),
                "barcode": barcode,
                "stock": int(stock),
                "imagen_url": imagen_url,
                "thumbnail_url": thumbnail_url
            }
        }

        return jsonify(response), 201

    except Exception as error:
        connection.rollback()
        return jsonify({"error": f"Registered error: {str(error)}"}), 500
    finally:
        cursor.close()
        connection.close()
