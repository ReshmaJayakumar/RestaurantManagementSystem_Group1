import pyodbc
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=LAPTOP-797FIBCN\\SQLEXPRESS;'
                          'DATABASE=project;'
                          'Trusted_Connection=yes;')
    return conn

#--------- Add or Update menu item   ----------

# Route to add or update a menu item
@app.route('/menu/add_update', methods=['POST', 'PUT'])
def add_or_update_menu_item():
    try:
        data = request.json
        # Check for required fields in the request data
        if not data or not all(key in data for key in ('name', 'description', 'price', 'category', 'is_available', 'quantity_available', 'manager_id')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':  # Add new menu item
            # Insert into menu_items table
            cursor.execute('''
                INSERT INTO menu_items (name, description, price, category, is_available)
                VALUES (?, ?, ?, ?, ?)
            ''', data['name'], data['description'], data['price'], data['category'], data['is_available'])
            conn.commit()

            # Get the id of the newly added menu item
            cursor.execute('SELECT SCOPE_IDENTITY()')
            item_id = cursor.fetchone()[0]

            # Insert into inventory table
            cursor.execute('''
                INSERT INTO inventory (menu_item_id, quantity_available, last_updated, manager_id)
                VALUES (?, ?, GETDATE(), ?)
            ''', item_id, data['quantity_available'], data['manager_id'])
            conn.commit()

            message = 'Menu item added successfully'

        elif request.method == 'PUT':  # Update existing menu item
            if 'id' not in data:
                return jsonify({'error': 'Missing id'}), 400  # Ensure 'id' is provided for updating

            # Update menu_items table
            cursor.execute('''
                UPDATE menu_items
                SET name = ?, description = ?, price = ?, category = ?, is_available = ?
                WHERE id = ?  -- Using 'id' to update the item
            ''', data['name'], data['description'], data['price'], data['category'], data['is_available'], data['id'])
            conn.commit()

            # Update inventory table if quantity_available is provided
            if 'quantity_available' in data:
                cursor.execute('''
                    UPDATE inventory
                    SET quantity_available = ?, last_updated = GETDATE()
                    WHERE menu_item_id = ?
                ''', data['quantity_available'], data['id'])  # Use 'id' in the inventory table
                conn.commit()

            message = 'Menu item updated successfully'

        cursor.close()
        # conn.close()
        return jsonify({'message': message}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



#------ Remove menu items -----

@app.route('/menu/remove', methods=['DELETE'])
def remove_menu_item():
    try:
        data = request.json
        if not data or 'menu_item_id' not in data:
            return jsonify({'error': 'Missing menu_item_id'}), 400

        menu_item_id = data['menu_item_id']
        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove from inventory table
        cursor.execute('DELETE FROM inventory WHERE menu_item_id = ?', menu_item_id)
        conn.commit()

        # Remove from menu_items table
        cursor.execute('DELETE FROM menu_items WHERE id = ?', menu_item_id)
        conn.commit()

        cursor.close()
        return jsonify({'message': 'Menu item removed successfully'}), 200

    except pyodbc.IntegrityError:
        return jsonify({'error': 'Cannot delete due to foreign key constraints.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Consolidate all other routes here (add, update, etc.)...
# Ensure you have only one app.run() at the bottom

# if __name__ == '__main__':
#     app.run(debug=True)



#-------------  View menu items by categories -------

# Route to view menu items organized by categories
@app.route('/menu/view', methods=['GET'])
def view_menu():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT category, id, name, description, price, is_available FROM menu_items ORDER BY category')
        menu_items = cursor.fetchall()
        menu = {}
        for item in menu_items:
            category = item[0]
            if category not in menu:
                menu[category] = []
            menu[category].append({
                'id': item[1],
                'name': item[2],
                'description': item[3],
                'price': item[4],
                'is_available': item[5]
            })
        cursor.close()
        # conn.close()
        return jsonify(menu), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)



# ###--------  feedback  -----------


# Route to view all feedback with urgency flag in the review status
@app.route('/feedback/view', methods=['GET'])
def view_feedback():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT FeedbackID, EmployeeID, FeedbackType, Description, CreatedAt, ReviewStatus FROM Feedback')
        feedback = cursor.fetchall()
        feedback_list = [{
            'FeedbackID': row[0],
            'EmployeeID': row[1],
            'FeedbackType': row[2],
            'Description': row[3],
            'CreatedAt': row[4],
            'ReviewStatus': row[5]
        } for row in feedback]
        cursor.close()
        # conn.close()
        return jsonify(feedback_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route to respond to feedback and categorize it, with urgent feedback flagging
@app.route('/feedback/respond', methods=['POST'])
def respond_to_feedback():
    try:
        data = request.json
        if not data or not all(key in data for key in ('FeedbackID', 'Response', 'Category')):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if the feedback should be flagged as urgent based on Response or Category
        urgency_flag = False
        if 'Urgent' in data.get('Response', '') or 'Urgent' in data.get('Category', ''):
            urgency_flag = True
            data['Response'] = f"{data['Response']} - Urgent"

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update feedback response, category, and review status (flagging urgent feedback if needed)
        cursor.execute('''
            UPDATE Feedback
            SET ReviewStatus = ?, FeedbackType = ?
            WHERE FeedbackID = ?
        ''', data['Response'], data['Category'], data['FeedbackID'])
        conn.commit()
        cursor.close()
        # conn.close()

        return jsonify({'message': 'Feedback updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route to add customer feedback (without UrgencyFlag in table, logic handled in response)
@app.route('/feedback/add', methods=['POST'])
def add_feedback():
    try:
        data = request.json
        if not data or not all(key in data for key in ('EmployeeID', 'FeedbackType', 'Description')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert feedback into the Feedback table
        cursor.execute('''
            INSERT INTO Feedback (EmployeeID, FeedbackType, Description, CreatedAt, ReviewStatus)
            VALUES (?, ?, ?, GETDATE(), 'Pending')
        ''', data['EmployeeID'], data['FeedbackType'], data['Description'])

        # Check if feedback is urgent and update accordingly
        if 'Urgent' in data.get('FeedbackType', ''):
            cursor.execute('''
                UPDATE Feedback
                SET ReviewStatus = 'Urgent'
                WHERE FeedbackID = (SELECT MAX(FeedbackID) FROM Feedback)
            ''')
            conn.commit()

        conn.commit()
        cursor.close()
        # conn.close()

        return jsonify({'message': 'Feedback added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# if __name__ == '__main__':
#     app.run(debug=True)


#----------- Inventory management  -----------

@app.route('/inventory/view', methods=['GET'])
def view_inventory():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Join inventory with menu_items to get more detailed information
        cursor.execute('''
            SELECT i.id, i.menu_item_id, i.quantity_available, i.last_updated, i.manager_id,
                   m.name AS menu_item_name, m.category AS menu_item_category
            FROM inventory i
            JOIN menu_items m ON i.menu_item_id = m.id
        ''')
        inventory_items = cursor.fetchall()
        inventory_list = [{
            'id': row[0],
            'menu_item_id': row[1],
            'quantity_available': row[2],
            'last_updated': row[3],
            'manager_id': row[4],
            'menu_item_name': row[5],
            'menu_item_category': row[6]
        } for row in inventory_items]
        
        cursor.close()
        # conn.close()
        
        return jsonify(inventory_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)

#-------  Alert for low inventory -----

@app.route('/inventory/alerts', methods=['GET'])
def inventory_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query for low inventory (e.g., threshold of 10 units)
        cursor.execute('''
            SELECT i.id, i.menu_item_id, i.quantity_available, m.name AS menu_item_name
            FROM inventory i
            JOIN menu_items m ON i.menu_item_id = m.id
            WHERE i.quantity_available < 10
        ''')
        low_inventory = cursor.fetchall()
        low_inventory_list = [{
            'id': row[0],
            'menu_item_id': row[1],
            'quantity_available': row[2],
            'menu_item_name': row[3]
        } for row in low_inventory]
        
        cursor.close()
        # conn.close()
        
        return jsonify(low_inventory_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
  

# if __name__ == '__main__':
#     app.run(debug=True)


# #----------  employeemanagement ----


# Route to add a new employee
@app.route('/employee/add', methods=['POST'])
def add_employee():
    try:
        data = request.json
        if not data or not all(key in data for key in ('Name', 'PhoneNumber', 'RoleID', 'StartDate', 'PasswordHash')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Employee (Name, PhoneNumber, RoleID, StartDate, Status, PasswordHash)
            VALUES (?, ?, ?, ?, 'Active', ?)
        ''', data['Name'], data['PhoneNumber'], data['RoleID'], data['StartDate'], data['PasswordHash'])
        conn.commit()
        cursor.close()
        # conn.close()

        return jsonify({'message': 'Employee added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to update employee details
@app.route('/employee/update/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Missing data to update'}), 400

        update_fields = []
        update_values = []
        for key in ('Name', 'PhoneNumber', 'RoleID', 'Status', 'PasswordHash'):
            if key in data:
                update_fields.append(f"{key} = ?")
                update_values.append(data[key])

        if 'Salary' in data:  # Salary is not in the table; update RoleID if applicable
            update_fields.append("RoleID = ?")
            update_values.append(data['Salary'])

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        update_values.append(employee_id)
        query = f"UPDATE Employee SET {', '.join(update_fields)} WHERE EmployeeId = ?"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, *update_values)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Employee updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to remove an employee
@app.route('/employee/remove/<int:employee_id>', methods=['DELETE'])
def remove_employee(employee_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Employee WHERE EmployeeId = ?', employee_id)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Employee removed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to view all employees
@app.route('/employee/view', methods=['GET'])
def view_employees():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Employee')
        employees = cursor.fetchall()
        employee_list = [{
            'EmployeeId': row[0],
            'Name': row[1],
            'PhoneNumber': row[2],
            'RoleID': row[3],
            'StartDate': row[4],
            'Status': row[5]
        } for row in employees]
        cursor.close()
        conn.close()

        return jsonify(employee_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

