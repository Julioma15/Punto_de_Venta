from flask import Blueprint, request, jsonify
from config.db import db_connection
from flask_jwt_extended import jwt_required, get_jwt_identity

#Creating the blueprint 
sales_bp = Blueprint('sales', __name__)

#Defining a endpoint to create a sale (POST method)
@sales_bp.route('/sales', methods = ['POST'])
#@jwt_required
def create_sale():
    
    #current_user = get_jwt_identity()

    data = request.get_json()

    id_ticket = data.get('id_ticket')
    id_product = data.get('id_product')
    quantity = data.get('quantity')
    
    connection = db_connection()
    cursor = connection.cursor()
    
    query = 'select*from tickets where id_ticket = %s'
    cursor.execute(query, (id_ticket, ))
    ticket_product_conformation = cursor.fetchone()
    query_2 = 'select*from productos where id_product = %s'
    cursor.execute(query_2, (id_product, ))
    product_confirmation = cursor.fetchone()
    if not ticket_product_conformation or not product_confirmation: 
        cursor.close()
        return jsonify({"Error":"That id_ticket or id_product not exist"})

    cursor.execute('select price from productos where id_product = %s;', (id_product, ))
    unit_price = cursor.fetchone()
    total = unit_price[0]*quantity
    
    #user_confirmation = 'select id_user from employees where id_user = %s'
    #cursor.execute(user_confirmation, (current_user, ))
    #employee = cursor.fetchone()
    '''
    if not employee[0] == int(current_user): 
        cursor.close()
        return jsonify({"Message":"Invalid credentials"})
    '''
    
    try: 
        query_3 = 'INSERT INTO ventas (id_ticket, id_product, unit_price, quantity, total) values (%s, %s, %s, %s, %s)'
        cursor.execute(query_3, (id_ticket, id_product, unit_price, quantity, total))
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
    
    query_2 = 'select *from ventas where ticket_id IN (select id_ticket from tickets where id_user = %s);'
    cursor.execute(query_2, (id_user, )) 
    user_sales = cursor.fetchall()

    cursor.close()

    if not user_sales: 
        return jsonify ({"Error":"The employee does not have sales yet"})
    else: 
        return jsonify ({"User's sales":user_sales}), 200
    

