from flask import Flask, request, send_file, jsonify
from datetime import datetime
from decimal import Decimal
import pyodbc
import os

app = Flask(__name__)

# Configure SQL Server connection
connection = pyodbc.connect(
    'DRIVER={SQL Server};SERVER=RESHMA\\SQLEXPRESS;DATABASE=RestaurantManagementSystem;Trusted_Connection=yes;'
)

# Route to display availability form
@app.route('/availability', methods=['POST'])
def availability():
    return submit_availability()

# Function to handle availability submission
def submit_availability():
    try:
        data = request.get_json()        
        employee_id = data.get('employee_id')
        availability = data.get('availability')

        if not employee_id or not availability:
            return jsonify({"error": "Missing required fields"}), 400
        
        cursor = connection.cursor()

        for entry in availability:
            day = entry.get('date')
            start_hour = entry.get('start_hour')
            start_minute = entry.get('start_minute')
            end_hour = entry.get('end_hour')
            end_minute = entry.get('end_minute')

            #Validate required fields in each entry
            if not day or not start_hour or not start_minute or not end_hour or not end_minute:
                return jsonify({"error": "Incomplete availability data"}), 400
            
            # Construct start and end time
            start_time = f"{start_hour}:{start_minute}:00"
            end_time = f"{end_hour}:{end_minute}:00"

            # Insert into SQL Server
            cursor.execute("""
                INSERT INTO EmployeeAvailability (EmployeeID, Date, DayOfWeek, AvailableStartTime, AvailableEndTime, Status)
                VALUES (?, ?, DATENAME(dw, ?), ?, ?, 'Active')
            """, employee_id, day, day, start_time, end_time)
        
        # Commit transaction
        connection.commit()
        cursor.close()

    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

    # Return success message
    return jsonify({"status": "Availability submitted successfully"}), 200

# Route to view and download pay stubs
@app.route('/paystubs', methods=['POST'])
def paystubs():
        return download_paystub()

# Function to fetch and download the pay stub
def download_paystub():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')

        if not employee_id or not month or not year:
            return jsonify({"error": "Missing required fields"}), 400

        cursor = connection.cursor()

        # Query to fetch the path for the requested pay stub
        cursor.execute("""
            SELECT PathToFile FROM PayStubs
            WHERE EmployeeID = ? AND Month = ? AND Year = ?
            """, employee_id, month, year)
        result = cursor.fetchone()

        if result:
            path_to_file = result[0]
            if os.path.exists(path_to_file):
                return send_file(path_to_file, as_attachment=True)
            else:
                return jsonify({"error": "File not found on the server."}), 404
        else:
            return jsonify({"error": "No matching pay stub found."}), 404
    except Exception as e:
        return jsonify({"error": "Database error", "details":str(e)}), 500

#Route to register order from dine-in users
@app.route('/register/dinein', methods = ['POST'])
def register():
    return handle_dinein_order()

#Function to handle in-house orders
def handle_dinein_order():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        table_number = data.get('table_number')
        items = data.get('items')

        if not employee_id or not table_number or not items:
            return jsonify({"error": "Missing required fields"}), 400
        
        if not all(
            isinstance(item.get('item_name'), str) and 
            isinstance(item.get('quantity'), int) and item['quantity'] > 0 
            for item in items
        ):
            return jsonify({"error": "Invalid items format: ensure all items have valid names and positive quantities."}), 400
    
        cursor = connection.cursor()
        created_at = datetime.now()

        # Insert into Orders table
        cursor.execute(""" 
            INSERT INTO Orders(EmployeeID, OrderType, TableNumber, Source, OrderStatus, CreatedAt)
                                VALUES (?, 'Dine-in', ?, 'Dine-in', 'Pending', ?)
                    """, (employee_id, table_number, created_at))
        print("Inserted")

        # Fetch the OrderID
        cursor.execute("SELECT @@IDENTITY;")
        order_id_result = cursor.fetchone()
        cursor.commit()
        if order_id_result:
            order_id = order_id_result[0]
        else:
            return jsonify({"error": "Failed to retrieve OrderID."}), 500

        total_amount = Decimal(0)
        for item in items:
            item_name = item['item_name']
            quantity = item['quantity']
            notes = item.get('notes', '')

            cursor.execute("""
                SELECT ItemID, Price FROM MenuItems
                WHERE Name LIKE ? AND IsAvailable = 1
            """, (item_name,))

            menu_item = cursor.fetchone()
            if not menu_item:
                return jsonify({"error": f"Menu item '{item_name}' not found or unavailable"}), 404
            
            item_id, item_price = menu_item
            total_amount += item_price * quantity
            
            cursor.execute("""
                INSERT INTO OrderItems(OrderID, ItemID, Quantity, Price, Notes)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, item_id, quantity, item_price, notes))
        
        # Calculate total amount with tax
        tax_rate = Decimal("1.13")
        total_amount_with_tax = total_amount * tax_rate

        cursor.execute("""
            UPDATE Orders 
            SET TotalAmount = ? 
            WHERE OrderID = ?
        """, (total_amount_with_tax, order_id))

        connection.commit()
        return jsonify({"status": "Order placed successfully", "order_id": order_id}), 201

    except Exception as e:
        connection.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
    finally:
        cursor.close()

#Route to cancel orders
@app.route('/cancel-order',methods = ['POST'])
def cancel():
    return cancel_order()

#Function to cancel the order
def cancel_order():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        order_id = data.get('order_id')

        if not employee_id or not order_id:
            return jsonify({"error": "Missing required fields"}), 400

        cursor = connection.cursor()
        cursor.execute("""
                        SELECT OrderStatus from Orders
                        WHERE OrderID = ? AND EmployeeID = ?
                        """, order_id, employee_id)
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error":"Order not found"})

        current_status = result[0]
        if current_status == 'Cancelled':
            return jsonify({"error":"This order is already cancelled"})
        
        cursor.execute("""
                        UPDATE Orders
                        SET OrderStatus = 'Cancelled', CompletedAt = ?
                        WHERE OrderID = ? AND EmployeeID = ?
                        """, datetime.now(),order_id, employee_id)
        
        cursor.execute("""
                       UPDATE OrderItems
                       SET Status = 'Cancelled'
                       WHERE OrderID = ?
                       """, order_id)
        
        connection.commit()
        return jsonify({"status":"Order cancelled successfully"})
    except Exception as e:
        return jsonify({"error":"Database error", "details": str(e)}), 500

#Route to cancel particular order item
@app.route('/cancel-particular-orderitem', methods=['POST'])
def cancel_item():
    return cancel_item()

#Function to cancel a particular order item
def cancel_item():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        order_item_id = data.get('order_item_id')

        if not employee_id or not order_item_id:
            return jsonify({"error": "Missing required fields"}), 400
        
        cursor = connection.cursor()

        cursor.execute("""
                        SELECT oi.Status, o.EmployeeID, oi.OrderID, (oi.Price * oi.Quantity) AS ItemTotal
                        FROM OrderItems oi
                        INNER JOIN Orders o ON oi.OrderID = o.OrderID
                        WHERE oi.OrderItemID = ? AND o.EmployeeID = ?
                        """, order_item_id, employee_id)
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error":"Order Item not found"})

        current_status, employee_id, order_id, item_total = result
        if current_status == 'Cancelled':
            return jsonify({"error": "This item is already cancelled"}), 400
        
        # Update the OrderItems table
        cursor.execute("""
            UPDATE OrderItems
            SET Status = 'Cancelled'
            WHERE OrderItemID = ?
        """, (order_item_id,))

        #Reduce the TotalAmount in Orders table
        cursor.execute("""
            UPDATE Orders
            SET TotalAmount = TotalAmount - ?
            WHERE OrderID = ?
        """, (item_total, order_id))

        connection.commit()
        return jsonify({"status": "Order item cancelled successfully"})
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

#Route to process payments
@app.route('/process-payments', methods=['POST'])
def payments():
    return process_payment()

#Function to process payments
def process_payment():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        employee_id = data.get('employee_id')
        payment_method = data.get('payment_method')
        promo_code = data.get('promo_code')
        split_details = data.get('split_details')

        if not order_id or not employee_id or not payment_method:
            return jsonify({"error":"Missing required fields"}), 400
        
        cursor = connection.cursor()

        #Fetching TotalAmount from Orders Table
        cursor.execute("""
                       SELECT TotalAmount from Orders
                       WHERE OrderID = ?
                       """, order_id)
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"error":"Order not found"}), 404
        
        original_amount = result[0]

        #Adding Discounts
        discount = Decimal(0)
        if promo_code:
            cursor.execute("""
                           SELECT Discount from Promotions
                           WHERE PromoCode = ? AND ExpiryDate >= GETDATE()
                           """, promo_code)
            promo_result = cursor.fetchone()
            if promo_result:
                discount = promo_result[0]
            else:
                return jsonify({"error":"Invalid or expired promo codo"}), 400

        #Calculating FinalAmount after adding discount    
        final_amount = Decimal(original_amount - discount)
        if final_amount < 0:
                final_amount = Decimal(0)

        #Update discount column in Orders table
        if promo_code:
            cursor.execute("""
                           UPDATE Orders
                           SET Discounts = ?
                           WHERE OrderID = ?
                           """,(promo_code, order_id))

        #Handle Split Payments
        if split_details:
            total_splits = split_details.get('total_splits')
            if not total_splits:
                return jsonify({"error":"Invalid split details"}),400
            
            #Insert into SplitPayments table
            cursor.execute("""
                INSERT INTO SplitPayments (OrderID, TotalSplits, SplitStatus)
                VALUES (?, ?, ?)
                """, (order_id, total_splits, "Completed"))
            
            split_payment_id = cursor.execute("SELECT @@IDENTITY;").fetchone()[0]

            # Distribute the payment equally among splits
            split_amount = final_amount / Decimal(total_splits)
            for _ in range(total_splits):
                cursor.execute("""
                    INSERT INTO Payments (OrderID, EmployeeID, PaymentMethod, DiscountApplied, Amount, PaymentDate, PaymentStatus, SplitPaymentID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, employee_id, payment_method, promo_code, split_amount, datetime.now(), "Completed", split_payment_id))
        
        # Handle regular payments
        else:
            cursor.execute("""
                INSERT INTO Payments (OrderID, EmployeeID, PaymentMethod, DiscountApplied, Amount, PaymentDate, PaymentStatus)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, employee_id, payment_method, promo_code, final_amount, datetime.now(), "Completed"))

        # Mark the order as paid
        cursor.execute("""
            UPDATE Orders
            SET OrderStatus = 'Paid', CompletedAt = ?
            WHERE OrderID = ?
        """, (datetime.now(), order_id))

        # Mark the order as completed in OrderItems table
        cursor.execute("""
            UPDATE OrderItems
            SET Status = 'Completed'
            WHERE OrderID = ?
        """, (order_id))

        connection.commit()
        return jsonify({"status": "Payment processed successfully", "final_amount": str(final_amount)}), 201
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500   
        
#Route to handle refunds
@app.route('/process-refund',methods =['POST'])
def handle_refunds():
    return process_refund()

#Function to process refunds
def process_refund():
    try:
        data = request.get_json()

        # Required fields from JSON input
        order_id = data.get('order_id')
        payment_id = data.get('payment_id')
        employee_id = data.get('employee_id')
        refund_amount = data.get('refund_amount')
        refund_method = data.get('refund_method')

        # Validate input
        if not all([order_id, payment_id, employee_id, refund_amount, refund_method]):
            return jsonify({"error": "Missing required fields"}), 400

        cursor = connection.cursor()

        # Check if the order exists and is paid
        cursor.execute("""
            SELECT Amount, PaymentStatus 
            FROM Payments 
            WHERE OrderID = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({"error": "Order not found"}), 404

        total_amount, payment_status = order

        if payment_status != 'Completed':
            return jsonify({"error": "Only paid orders can be refunded"}), 400

        # Check if refund amount exceeds remaining refundable amount
        cursor.execute("""
            SELECT COALESCE(SUM(RefundAmount), 0) 
            FROM Refunds 
            WHERE OrderID = ?
        """, (order_id))
        total_refunded = cursor.fetchone()[0]

        remaining_amount = total_amount - total_refunded

        if refund_amount > remaining_amount:
            return jsonify({"error": f"Refund amount exceeds remaining refundable amount of {remaining_amount}"}), 400

        # Insert refund record
        cursor.execute("""
            INSERT INTO Refunds (OrderID, PaymentID, EmployeeID, RefundAmount, RefundMethod, RefundDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, payment_id, employee_id, refund_amount, refund_method, datetime.now()))

        # Add a record in Payments table for the refund
        cursor.execute("""
            INSERT INTO Payments (OrderID, EmployeeID, PaymentMethod, Amount, PaymentDate, PaymentStatus)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, employee_id, refund_method, -refund_amount, datetime.now(), "Refunded"))

        # Update order status to 'Refunded' if fully refunded
        if refund_amount == remaining_amount:
            cursor.execute("""
                UPDATE Payments
                SET PaymentStatus = 'Refunded'
                WHERE OrderID = ?
            """, (order_id,))

        connection.commit()

        return jsonify({
            "status": "Refund processed successfully",
            "refund_amount": refund_amount,
            "remaining_amount": remaining_amount - refund_amount
        }), 201

    except Exception as e:
        connection.rollback()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
