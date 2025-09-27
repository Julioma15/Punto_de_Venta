from flask import Blueprint, request, jsonify
from config.db import db_connection
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/sales-summary', methods=['GET'])
@jwt_required()
def sales_summary():
    current_user_id = get_jwt_identity()
    connection = db_connection()
    cursor = connection.cursor()
    try:
        # Validar rol
        cursor.execute("SELECT role FROM usuarios WHERE id_user = %s AND active = TRUE", (current_user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Token inválido o usuario no encontrado"}), 401
        role_actual = (row[0] or "").lower()
        if role_actual not in ("admin", "manager"):
            return jsonify({"error": "Usuario no autorizado (solo admin/manager)"}), 403

        # Query de reporte
        cursor.execute("""
            SELECT 
                COALESCE(SUM(v.unit_price * v.quantity), 0) AS total_amount,
                COUNT(DISTINCT v.ticket_id) AS tickets
            FROM ventas v;
        """)
        row = cursor.fetchone()

        total_amount = float(row[0] or 0)
        tickets = int(row[1] or 0)
        avg_ticket = round(total_amount / tickets, 2) if tickets > 0 else 0.0

        return jsonify({
            "total_amount": total_amount,
            "tickets": tickets,
            "avg_ticket": avg_ticket
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error en sales-summary: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()



@reports_bp.route('/reports/sales-employee', methods=['GET'])
@jwt_required()
def sales_employee():
    current_user_id = get_jwt_identity()
    connection = db_connection()
    cursor = connection.cursor()
    try:
        # Validar rol
        cursor.execute("SELECT role FROM usuarios WHERE id_user = %s AND active = TRUE", (current_user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Token inválido o usuario no encontrado"}), 401
        role_actual = (row[0] or "").lower()
        if role_actual not in ("admin", "manager"):
            return jsonify({"error": "Usuario no autorizado (solo admin/manager)"}), 403

        # Query de reporte (ajusta según tu DDL)
        cursor.execute("""
            SELECT 
                t.created_by AS id_user,
                COUNT(DISTINCT v.ticket_id) AS tickets,
                COALESCE(SUM(v.unit_price * v.quantity), 0) AS total_amount,
                COALESCE(SUM(v.quantity), 0) AS total_units
            FROM ventas v
            JOIN tickets t ON t.id_ticket = v.ticket_id
            GROUP BY t.created_by
            ORDER BY total_amount DESC;
        """)
        rows = cursor.fetchall()

        result = [{
            "id_user": int(r[0]) if r[0] is not None else None,
            "tickets": int(r[1] or 0),
            "total_amount": float(r[2] or 0),
            "total_units": int(r[3] or 0)
        } for r in rows]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Error en sales-employee: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()
