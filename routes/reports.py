from flask import Blueprint, request, jsonify
from config.db import db_connection

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/sales-summary', methods=['GET'])
def sales_summary():
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                SUM(v.unit_price * v.quantity) AS total_amount,
                COUNT(DISTINCT v.ticket_id) AS tickets
            FROM ventas v;
        """)
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "No hay ventas registradas"}), 404

        total_amount = float(row[0] or 0)
        tickets = int(row[1] or 0)
        avg_ticket = total_amount / tickets if tickets > 0 else 0

        return jsonify({
            "total_amount": total_amount,
            "tickets": tickets,
            "avg_ticket": round(avg_ticket, 2)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error en sales-summary: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()


@reports_bp.route('/reports/sales-employee', methods=['GET'])
def sales_employee():
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                v.id_user,
                COUNT(DISTINCT v.ticket_id) AS tickets,
                SUM(v.unit_price * v.quantity) AS total_amount,
                SUM(v.quantity) AS total_units
            FROM ventas v
            GROUP BY v.id_user
            ORDER BY total_amount DESC;
        """)
        rows = cur.fetchall()

        if not rows:
            return jsonify({"error": "No hay ventas registradas"}), 404

        result = []
        for r in rows:
            result.append({
                "id_user": int(r[0]) if r[0] is not None else None,
                "tickets": int(r[1]),
                "total_amount": float(r[2] or 0),
                "total_units": int(r[3] or 0)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Error en sales-employee: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()
