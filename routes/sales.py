from flask import Blueprint, request, jsonify
from config.db import db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity

#Creating the blueprint 
sales_bp = Blueprint('sales', __name__)

#Defining a endpoint to create a sale (POST method)
@sales_bp.route('/sales', methods = ['POST'])
@jwt_required
def create_sale():
    
    current_user = get_jwt_identity()

    data = request.get_json()

    products = data.get('products')
    quantity = data.get('quantity')
    
    connection = db_connection()
    cursor = connection.cursor()
    
    user_confirmation = 'select id_user from usuarios where id_user = %s'
    cursor.execute(user_confirmation, (current_user, ))
    ususario = cursor.fetchone()
    
    if not ususario[0] == int(current_user): 
        cursor.close()
        return jsonify({"Message":"Invalid credentials"})

    ticket_id = cursor.execute('select ticket_id from ventas where ticket_id = (select max(ticket_id) from ventas)')

    cursor.execute('select price from productos where id_product = %s;', (product_id, ))
    unit_price = cursor.fetchone()
    total = unit_price[0]*quantity
     
    try: 
        query_3 = 'INSERT INTO ventas (ticket_id, product_id, unit_price, quantity, total) values (%s, %s, %s, %s, %s)'
        cursor.execute(query_3, (ticket_id, product_id, unit_price, quantity, total))
        cursor.connection.commit()
        return jsonify({"Message":"sale completed"})
    except Exception as error: 
        return jsonify({"Error":f"There was an error during the sale creation: {str(error)}"})
    finally: 
        cursor.close()

#Defining a endpoint to list the sales of an employee (GET method)
@sales_bp.route('/sales', methods = ['GET'])
#@jwt_required
def get_all_sales(): 

    #current_user = get_jwt_identity()
    
    data = request.get_json()
    id_user = data.get('id_user')

    connection = db_connection()
    cursor = connection.cursor()

    '''
    user_confirmation = 'select*from employees where id_user = %s;'
    employee = cursor.execute(user_confirmation, (id_user, ))
    if not employee == int(id_user): 
        cursor.close()
        return jsonify({"Error":"Invalid credentials"})
    '''
    
    query_2 = 'select *from ventas where ticket_id IN (select ticket_id from tickets where id_user = %s);'
    cursor.execute(query_2, (id_user, )) 
    user_sales = cursor.fetchall()

    cursor.close()

    if not user_sales: 
        return jsonify ({"Error":"The employee does not have sales yet"})
    else: 
        return jsonify ({"User's sales":user_sales}), 200
    

# GET /sales/<ticket_id>/receipt
from flask_jwt_extended import jwt_required, get_jwt_identity

@sales_bp.route('/sales/<int:ticket_id>/receipt', methods=['GET'])
@jwt_required()
def get_receipt(ticket_id):
    """
    Devuelve la info del ticket usando SOLO ventas + nombre de producto.
    Calcula line_total = unit_price * quantity (no hay columna total).
    Acceso:
      - admin/manager: cualquier ticket
      - cashier: solo tickets creados por él/ella (tickets.created_by)
    """
    current_user_id = get_jwt_identity()
    connection = db_connection()
    if not connection:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
    cursor = connection.cursor()
    try:
        # 1) Validar rol del usuario actual
        cursor.execute("SELECT role FROM usuarios WHERE id_user = %s AND active = TRUE", (current_user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Token inválido o usuario no encontrado"}), 401

        role_actual = (row[0] or "").lower()
        if role_actual not in ("admin", "manager", "cashier"):
            return jsonify({"error": "Usuario no autorizado"}), 403

        # 2) Si es cashier, verificar propiedad del ticket
        if role_actual == "cashier":
            cursor.execute("SELECT created_by FROM tickets WHERE id_ticket = %s", (ticket_id,))
            trow = cursor.fetchone()
            if not trow:
                return jsonify({"error": "Ticket no encontrado"}), 404
            created_by = int(trow[0]) if trow[0] is not None else None
            if created_by != int(current_user_id):
                return jsonify({"error": "No tienes permiso para ver este recibo"}), 403

        # 3) Traer líneas de venta del ticket
        cursor.execute("""
            SELECT
                v.product_id,
                COALESCE(p.product_name, '') AS product_name,
                v.unit_price,
                v.quantity
            FROM ventas v
            LEFT JOIN productos p ON p.id_product = v.product_id
            WHERE v.ticket_id = %s
            ORDER BY v.id_sale;
        """, (ticket_id,))
        rows = cursor.fetchall()

        if not rows:
            # Si no hay líneas, validamos que el ticket exista para diferenciar 404
            cursor.execute("SELECT 1 FROM tickets WHERE id_ticket = %s", (ticket_id,))
            exists = cursor.fetchone()
            if not exists:
                return jsonify({"error": "Ticket no encontrado"}), 404
            return jsonify({"error": "No hay ventas para ese ticket_id"}), 404

        items = []
        subtotal = 0.0
        for product_id, product_name, unit_price, quantity in rows:
            up = float(unit_price or 0)
            qty = int(quantity or 0)
            line_total = up * qty
            items.append({
                "product_id": int(product_id),
                "product_name": product_name,
                "unit_price": up,
                "quantity": qty,
                "line_total": round(line_total, 2)
            })
            subtotal += line_total

        taxes = 0.0  # ajusta si manejas impuestos
        total = subtotal + taxes

        return jsonify({
            "ticket_id": int(ticket_id),
            "items": items,
            "summary": {
                "subtotal": round(subtotal, 2),
                "taxes": round(taxes, 2),
                "total": round(total, 2)
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error al consultar el recibo: {str(e)}"}), 500
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
