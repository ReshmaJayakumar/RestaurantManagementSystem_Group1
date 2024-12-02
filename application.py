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



# Route to add a menu item
@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    try:
        data = request.json
        if not data or not all(key in data for key in ('name', 'description', 'price', 'category', 'is_available', 'quantity_available', 'manager_id')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

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

        cursor.close()
        conn.close()
        return jsonify({'message': 'Menu item added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to update a menu item
@app.route('/menu/update', methods=['PUT'])
def update_menu_item():
    try:
        data = request.json
        if not data or 'menu_item_id' not in data:
            return jsonify({'error': 'Missing menu_item_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update menu_items table
        cursor.execute('''
            UPDATE menu_items
            SET name = ?, description = ?, price = ?, category = ?, is_available = ?
            WHERE id = ?
        ''', data.get('name'), data.get('description'), data.get('price'), data.get('category'),
            data.get('is_available'), data['menu_item_id'])
        conn.commit()

        # Update inventory table if quantity_available is provided
        if 'quantity_available' in data:
            cursor.execute('''
                UPDATE inventory
                SET quantity_available = ?, last_updated = GETDATE()
                WHERE menu_item_id = ?
            ''', data['quantity_available'], data['menu_item_id'])
            conn.commit()

        cursor.close()
        conn.close()
        return jsonify({'message': 'Menu item updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to remove a menu item
@app.route('/menu/remove', methods=['DELETE'])
def remove_menu_item():
    try:
        data = request.json
        if not data or 'menu_item_id' not in data:
            return jsonify({'error': 'Missing menu_item_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove from inventory table
        cursor.execute('DELETE FROM inventory WHERE menu_item_id = ?', data['menu_item_id'])
        conn.commit()

        # Remove from menu_items table
        cursor.execute('DELETE FROM menu_items WHERE id = ?', data['menu_item_id'])
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({'message': 'Menu item removed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        conn.close()
        return jsonify(menu), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

    

###--------  feedback  -----------



# Route to add customer feedback
@app.route('/feedback/add', methods=['POST'])
def add_feedback():
    try:
        # Get the JSON data from the request
        data = request.json
        if not data or not all(key in data for key in ('EmployeeID', 'FeedbackType', 'Description')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert feedback into the Feedback table
        cursor.execute('''
            INSERT INTO Feedback (EmployeeID, FeedbackType, Description, CreatedAt, ReviewStatus)
            VALUES (?, ?, ?, GETDATE(), 'Pending')
        ''', data['EmployeeID'], data['FeedbackType'], data['Description'])
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Feedback added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to view all feedback
@app.route('/feedback/view', methods=['GET'])
def view_feedback():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Feedback')
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
        conn.close()
        return jsonify(feedback_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to respond to feedback and categorize it
@app.route('/feedback/respond', methods=['POST'])
def respond_to_feedback():
    try:
        data = request.json
        if not data or not all(key in data for key in ('FeedbackID', 'Response', 'Category')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Feedback
            SET ReviewStatus = ?, FeedbackType = ?
            WHERE FeedbackID = ?
        ''', data['Response'], data['Category'], data['FeedbackID'])
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Feedback updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to flag urgent feedback
@app.route('/feedback/flag', methods=['POST'])
def flag_feedback():
    try:
        data = request.json
        if not data or 'FeedbackID' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Feedback
            SET FeedbackType = 'Urgent'
            WHERE FeedbackID = ?
        ''', data['FeedbackID'])
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Feedback flagged as urgent'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


#----------  employeemanagement ----


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
        conn.close()

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

# Route to track employee availability (bonus)
@app.route('/employee/availability/add', methods=['POST'])
def add_availability():
    try:
        data = request.json
        if not data or not all(key in data for key in ('EmployeeID', 'Date', 'DayOfWeek', 'AvailableStartTime', 'AvailableEndTime')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO EmployeeAvailability (EmployeeID, Date, DayOfWeek, AvailableStartTime, AvailableEndTime, Status)
            VALUES (?, ?, ?, ?, ?, 'Active')
        ''', data['EmployeeID'], data['Date'], data['DayOfWeek'], data['AvailableStartTime'], data['AvailableEndTime'])
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Availability added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


#----------- payment management -----


# Route to configure payment methods
@app.route('/payment/methods/configure', methods=['POST'])
def configure_payment_methods():
    try:
        data = request.json
        if not data or 'PaymentMethods' not in data:
            return jsonify({'error': 'Missing payment methods'}), 400

        # Assuming payment methods are stored in a PaymentMethods table
        conn = get_db_connection()
        cursor = conn.cursor()

        for method in data['PaymentMethods']:
            cursor.execute('''
                INSERT INTO PaymentMethods (PaymentMethod) VALUES (?)
            ''', method)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Payment methods configured successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to process payments
@app.route('/payment/process', methods=['POST'])
def process_payment():
    try:
        data = request.json
        required_fields = ['OrderID', 'EmployeeID', 'PaymentMethod', 'Amount', 'DiscountApplied']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO Payments (OrderID, EmployeeID, PaymentMethod, DiscountApplied, Amount, PaymentDate, PaymentStatus)
            VALUES (?, ?, ?, ?, ?, GETDATE(), 'Completed')
        ''', data['OrderID'], data['EmployeeID'], data['PaymentMethod'], data['DiscountApplied'], data['Amount'])

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Payment processed successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to issue refunds
@app.route('/payment/refund', methods=['POST'])
def issue_refund():
    try:
        data = request.json
        required_fields = ['OrderID', 'PaymentID', 'EmployeeID', 'RefundAmount', 'RefundMethod']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO Refunds (OrderID, PaymentID, EmployeeID, RefundAmount, RefundMethod, RefundDate)
            VALUES (?, ?, ?, ?, ?, GETDATE())
        ''', data['OrderID'], data['PaymentID'], data['EmployeeID'], data['RefundAmount'], data['RefundMethod'])

        cursor.execute('''
            UPDATE Payments SET PaymentStatus = 'Refunded' WHERE PaymentID = ?
        ''', data['PaymentID'])

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Refund issued successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to view transaction reports
@app.route('/payment/reports', methods=['GET'])
def view_transaction_reports():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Payments')
        payments = cursor.fetchall()
        payment_list = [{
            'PaymentID': row[0],
            'OrderID': row[1],
            'EmployeeID': row[2],
            'PaymentMethod': row[3],
            'DiscountApplied': row[4],
            'Amount': row[5],
            'PaymentDate': row[6],
            'PaymentStatus': row[7]
        } for row in payments]

        cursor.close()
        conn.close()

        return jsonify(payment_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to notify manager of failed or incomplete transactions
@app.route('/payment/failed', methods=['GET'])
def failed_transactions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Payments WHERE PaymentStatus = \'Failed\' OR PaymentStatus = \'Incomplete\'')
        failed_payments = cursor.fetchall()
        failed_list = [{
            'PaymentID': row[0],
            'OrderID': row[1],
            'EmployeeID': row[2],
            'PaymentMethod': row[3],
            'DiscountApplied': row[4],
            'Amount': row[5],
            'PaymentDate': row[6],
            'PaymentStatus': row[7]
        } for row in failed_payments]

        cursor.close()
        conn.close()

        return jsonify(failed_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
