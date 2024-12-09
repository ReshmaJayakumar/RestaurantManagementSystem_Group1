from flask import Flask, jsonify,request,session,send_file
import pyodbc
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime
import json as js
from flask import Response
from decimal import Decimal
import os

app=Flask(__name__)
server = 'DESKTOP-6CJA95D\SQLEXPRESS'
database = 'Project'
app.config['SECRET_KEY']="group1"
connection = pyodbc.connect(
    'DRIVER={SQL Server};SERVER=RESHMA\\SQLEXPRESS;DATABASE=RestaurantManagementSystem;Trusted_Connection=yes;'
)

#connection = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')

class MyException(Exception):
    pass

@app.route('/')
def index():
    if 'username' in session:
        username=session['username']
        role=session['role']
        return jsonify({'message': 'You are already logged in','username':username,'role':role})
    else:
        resp=jsonify({'message':'Unauthorized'})
        resp.status_code=401
        return resp

@app.route('/login',methods=['POST' ])
def login():    
    json=request.json
    username=json['username']
    password=json['password']
    if username and password:
        try:
            #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            conn=connection
            cursor = conn.cursor()
            print("\n DB Connected")
            cursor.execute('SELECT * FROM employees WHERE employeeid=?',(username))
            row=cursor.fetchone()
            print("\nFetched")
            
            
            if row:
                print(row)
                uName=row[0]
                pWord=row[6]
                role=row[3]
                
                if check_password_hash(pWord,password):
                    session['username']=uName
                    cursor.execute('SELECT RoleName FROM roles WHERE roleid=?',(role))
                    row=cursor.fetchone()
                    role=row[0]
                    session['role']=role
                    resp=checkClockin(uName)
                    return jsonify({'message':'Success','role':role})
                    
                else:
                    resp=jsonify({'message':'Fail','reason':'Invalid password'})
                    resp.status_code=400
                    return resp
            else:
                resp=jsonify({'message':'Fail','reason':'Invalid Username'})
                resp.status_code=400
                return resp
        except pyodbc.Error as db_error:
            resp=jsonify({'message':'Fail','reason':str(db_error)})
            resp.status_code=400
            return resp
        except ValueError as val_error:
            resp=jsonify({'message':'Fail','reason':str(val_error)})
            resp.status_code=400
            return resp
        except Exception as e:
            resp=jsonify({'message':'Fail','reason':str(e)})
            resp.status_code=400
            return resp
        except MyException as e:
            resp=jsonify({'message':'Fail','reason':str(e)})
        #finally:
         #if conn is not None:
            #conn.close()
    else:
        resp=jsonify({'message':'Fail','reason':'empty username or password'})
        resp.status_code=400
        return resp
    
@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username',None)
    return jsonify({"message":"Logged Out"})


@app.route('/clockout')
def clockout():
    
    try:
        empid=session['username']
        time=datetime.today().strftime('%H:%M:%S')
        date=datetime.today().strftime('%Y-%m-%d')
        conn=connection
        #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
        cursor = conn.cursor()
        print("\n Clock  out Connected")
        cursor.execute('UPDATE shift set ends=? where empid=? and date=?',(time,empid,date))
        print("\n Clock  out update 1")
        cursor.execute('UPDATE shift set hours=DATEDIFF(minute, starts ,ends) where empid=? and date=?',(empid,date))
        cursor.commit()
        print("clock out inserted")
        return jsonify({"message":"Clocked Out"})
    except pyodbc.Error as db_error:
        return jsonify({f"message":"Fail","reason":str(db_error)})
    except KeyError:
        return jsonify({f"message":"Fail",'reason':'you are not logged in or session expired'})
        


@app.route('/orders',defaults={'orderno': None})
@app.route('/orders/',defaults={'orderno': None})
@app.route('/orders/<orderno>')
def orders(orderno):
    if request.method=='GET':
        if 'username' in session:
            if orderno:
                try:
                    query=f"Select * from Orders where OrderID ='{orderno}'"
                    #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
                    conn=connection
                    cursor = conn.cursor()
                    print("\n DB Connected")
                    cursor.execute(query)
                    row=cursor.fetchone()
                    if row:
                        orderid=str(row[0])
                        employeeid=str(row[1])
                        ordertype=str(row[2])
                        table=str(row[3])
                        source=str(row[4])
                        phone=str(row[5])
                        time=str(row[6])
                        orderstatus=str(row[7])
                        amount=str(row[8])
                        created=str(row[9])
                        completed=str(row[10])
                        cursor.execute(f"Select * from OrderItems WHERE OrderID={orderid}")
                        items=[]
                        for row in cursor:
                            ItemID=row[2]
                            Quantity=row[3]
                            Price=row[4]
                            Notes=row[5]
                            item={'ItemID':str(ItemID),'Quantity':str(Quantity),'Price':str(Price),'Notes':str(Notes)}
                            items.append(item)
                        innerresp={'orderid':orderid,'employeeid':employeeid,'ordertype':ordertype,'table':table,'source':source,
                        'phone':phone,'time':time,'orderstatus':orderstatus,'amount':amount,'createdat':created,'completed':completed,'items':items}
                        return Response(js.dumps(innerresp),content_type='application/json')
                    else:
                        return jsonify({'message':"No order found for given order ID"})
                except pyodbc.Error as db_error:
                    sqlstate = db_error.args[0]
                    if sqlstate == '22018':
                        return jsonify({f"message":"Fail","reason":"Invalid OrderID Type"})
                    else:
                        return jsonify({f"message":"Fail","reason":str(db_error)})
                except Exception as e:
                    return jsonify({f"message":"Fail","reason":str(e)})
            else:
                try:
                    resp=[]
                    resp2=""
                    query="select * from Orders"
                    where=''
                    print("hello")
                    json=request.json
                    
                    count=0
                    statusflag=False
                    typeflag=False
                    dateflag=False
                    if "orderstatus" in json:
                        status=json['orderstatus']
                        where=where+f"OrderStatus='{status}'"
                        count=count+1
                        statusflag=True
                    if "ordertype" in json:
                        type=json['ordertype']
                        where=where+f" and OrderType='{type}'"
                        count=count+1
                        typeflag=True
                    if "date" in json:
                        date=json['date']
                        where=where+f" and CreatedAt>'{date}'"
                        count=count+1
                        dateflag=True
                    if statusflag!=True:
                        if typeflag:
                            where=where.replace("and OrderType","OrderType")
                        elif dateflag:
                            where=where.replace("and CreatedAt","CreatedAt")
                    if statusflag or typeflag or dateflag:
                        query=query+" where "+where
                    #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
                    conn=connection
                    cursor = conn.cursor()
                    print("\n DB Connected")
                    cursor.execute(query)
                    rows=cursor.fetchall()
                    for row in rows:
                        orderid=str(row[0])
                        employeeid=str(row[1])
                        ordertype=str(row[2])
                        table=str(row[3])
                        source=str(row[4])
                        phone=str(row[5])
                        time=str(row[6])
                        orderstatus=str(row[7])
                        amount=str(row[8])
                        created=str(row[9])
                        completed=str(row[10])
                        cursor.execute(f"Select * from OrderItems WHERE OrderID={orderid}")
                        items=[]
                        for row in cursor:
                            ItemID=row[2]
                            Quantity=row[3]
                            Price=row[4]
                            Notes=row[5]
                            item={'ItemID':str(ItemID),'Quantity':str(Quantity),'Price':str(Price),'Notes':str(Notes)}
                            items.append(item)
                        innerresp={'orderid':orderid,'employeeid':employeeid,'ordertype':ordertype,'table':table,'source':source,
                        'phone':phone,'time':time,'orderstatus':orderstatus,'amount':amount,'createdat':created,'completed':completed,'items':items}
                        resp.append(innerresp)
                    print("all worked")
                    resp= js.dumps(resp)
                    return Response(resp,status=200,content_type='application/json')
                    
                    
                except pyodbc.Error as db_error:
                    return jsonify({f"message":"Fail","reason":db_error})
                    
                except Exception as e:
                    return jsonify({f"message":"Fail","reason":str(e)})
        else:
            return jsonify({f"message":"Fail","reason":"you are not logged, in please login"})


@app.route('/schedule',methods=['GET','POST'])
def schedule():
    if request.method=='GET':
        schedules=[]
        try:
            username=session['username']
            date=datetime.today().strftime('%Y-%m-%d')
            print(date)
            print(username)
            conn=connection
            #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            cursor = conn.cursor()
            print("\n Schedule DB Connected")
            cursor.execute(f"SELECT * FROM schedule WHERE userid='{username}' and date>='{date}'")
            print("\n Schedule Fetched")
            rows=cursor.fetchall()
            for row in rows:
                print("loop")
                id=str(row[0])
                date=str(row[2])
                starts=str(row[3])
                ends=str(row[4])
                hours=str(row[5])
                sched={'id':id,'date':date,'start':starts,'ends':ends,'hours':hours}
                schedules.append(sched)
            print(schedules)
            schedules=js.dumps(schedules)
            return(Response(schedules,status=200,content_type='application/json'))
        except Exception as e:
            return jsonify({f"message":"Fail","reason":e})

    elif request.method=='POST':
        return 'post'


def checkClockin(username):
    date=datetime.today().strftime('%Y-%m-%d')
    time=datetime.today().strftime('%H:%M:%S')
    try:
        #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
        conn=connection
        cursor = conn.cursor()
        print("\n Clock in DB Connected")
        print(username)
        cursor.execute('SELECT * FROM shift WHERE EmployeeID=? and date=?',(username,date))
        print("\n Clock in Fetched")
        row=cursor.fetchone()
        if row:
            return(0)
        else:
            conn=connection
            #conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;')
            cursor = conn.cursor()
            print("\n Clock in 2 DB Connected")
            cursor.execute('insert into shift (date,EmployeeID,starts) values(?,?,?)',(date,username,time))
            cursor.commit()
            print("clock in inserted")
            return(1)
    except pyodbc.Error as db_error:
        raise MyException(f"Clock in Failed,{db_error}")
    except Exception as e:
        raise MyException(f"Clock in Failed :",str(e))


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
    #finally:
     #   cursor.close()

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
    

        
@app.route('/employee/add', methods=['POST'])
def add_employee():
    try:
        data = request.json
        if not data or not all(key in data for key in ('Name', 'PhoneNumber', 'RoleID', 'StartDate', 'PasswordHash')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = connection
        cursor = conn.cursor()
        passw = generate_password_hash(data['PasswordHash'])
        cursor.execute('''
            INSERT INTO Employees (Name, PhoneNumber, RoleID, StartDate, Status, PasswordHash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data['Name'], data['PhoneNumber'], data['RoleID'], data['StartDate'], data['Status'], passw)
        conn.commit()
        cursor.close()
        #conn.close()

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
        query = f"UPDATE Employees SET {', '.join(update_fields)} WHERE EmployeeId = ?"

        conn = connection
        cursor = conn.cursor()
        cursor.execute(query, *update_values)
        conn.commit()
        cursor.close()
        #conn.close()

        return jsonify({'message': 'Employee updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to remove an employee
@app.route('/employee/remove/<int:employee_id>', methods=['DELETE'])
def remove_employee(employee_id):
    try:
        conn = connection
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Employees WHERE EmployeeId = ?', employee_id)
        conn.commit()
        cursor.close()
        #conn.close()

        return jsonify({'message': 'Employee removed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to view all employees
@app.route('/employee/view', methods=['GET'])
def view_employees():
    try:
        conn = connection
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Employees')
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
        #conn.close()

        return jsonify(employee_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#Route to add or update a menu item
@app.route('/menu/add_update', methods=['POST', 'PUT'])
def add_or_update_menu_item():
    try:
        data = request.json
        #Check for required fields in the request data
        if not data or not all(key in data for key in ('name', 'description', 'price', 'category', 'isavailable', 'quantity_available', 'manager_id')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = connection
        cursor = conn.cursor()

        if request.method == 'POST':  #Add new menu item
            #Insert into menu_items table
            cursor.execute('''
                INSERT INTO MenuItems (name, description, price, category, isavailable)
                VALUES (?, ?, ?, ?, ?)
            ''', data['name'], data['description'], data['price'], data['category'], data['isavailable'])
            conn.commit()

            #Get the id of the newly added menu item
            cursor.execute("SELECT @@IDENTITY;")
            item_id = cursor.fetchone()[0]

            #Insert into inventory table
            cursor.execute('''
                INSERT INTO inventory (itemid, quantity_available, last_updated, manager_id)
                VALUES (?, ?, GETDATE(), ?)
            ''', item_id, data['quantity_available'], data['manager_id'])
            conn.commit()

            message = 'Menu item added successfully'

        elif request.method == 'PUT':  #Update existing menu item
            if 'id' not in data:
                return jsonify({'error': 'Missing id'}), 400  #Ensure 'id' is provided for updating

            #Update menu_items table
            cursor.execute('''
                UPDATE MenuItems
                SET name = ?, description = ?, price = ?, category = ?, isavailable = ?
                WHERE ItemId = ?  -- Using 'id' to update the item
            ''', data['name'], data['description'], data['price'], data['category'], data['isavailable'], data['id'])
            conn.commit()

            #Update inventory table if quantity_available is provided
            if 'quantity_available' in data:
                cursor.execute('''
                    UPDATE inventory
                    SET quantity_available = ?, last_updated = GETDATE()
                    WHERE itemid = ?
                ''', data['quantity_available'], data['id'])  #Use 'id' in the inventory table
                conn.commit()

            message = 'Menu item updated successfully'

        cursor.close()
        #conn.close()
        return jsonify({'message': message}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

#------ Remove menu items -----

#Route to remove a menu item
@app.route('/menu/remove', methods=['DELETE'])
def remove_menu_item():
    try:
        data = request.json
        
        #Check if itemid is provided in the request body
        if not data or 'menu_item_id' not in data:
            return jsonify({'error': 'Missing menu_item_id'}), 400

        menu_item_id = data['menu_item_id']

        conn = connection
        cursor = conn.cursor()

        #Remove from inventory table where menu_item_id matches
        cursor.execute('DELETE FROM inventory WHERE itemid = ?', menu_item_id)
        conn.commit()

        #Remove from menu_items table where id matches
        cursor.execute('DELETE FROM MenuItems WHERE ItemId = ?', menu_item_id)
        conn.commit()

        cursor.close()
        #conn.close()
        return jsonify({'message': 'Menu item removed successfully'}), 200

    except pyodbc.IntegrityError as e:
        #Handle integrity errors (e.g., foreign key violations)
        return jsonify({'error': 'Foreign key constraint violation. Could not delete menu item.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

#-------------  View menu items by categories -------

#Route to view menu items organized by categories
@app.route('/menu/view', methods=['GET'])
def view_menu():
    try:
        conn = connection
        cursor = conn.cursor()
        cursor.execute('SELECT category, ItemId, name, description, price, isavailable FROM MenuItems ORDER BY category')
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
        #conn.close()
        return jsonify(menu), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Route to respond to feedback and categorize it, with urgent feedback flagging
@app.route('/feedback/respond', methods=['POST'])
def respond_to_feedback():
    try:
        data = request.json
        if not data or not all(key in data for key in ('FeedbackID', 'Response', 'Category')):
            return jsonify({'error': 'Missing required fields'}), 400

        #Check if the feedback should be flagged as urgent based on Response or Category
        urgency_flag = False
        if 'Urgent' in data.get('Response', '') or 'Urgent' in data.get('Category', ''):
            urgency_flag = True
            data['Response'] = f"{data['Response']} - Urgent"

        conn = connection
        cursor = conn.cursor()
        
        #Update feedback response, category, and review status (flagging urgent feedback if needed)
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


#Route to add customer feedback (without UrgencyFlag in table, logic handled in response)
@app.route('/feedback/add', methods=['POST'])
def add_feedback():
    try:
        data = request.json
        if not data or not all(key in data for key in ('EmployeeID', 'FeedbackType', 'Description')):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = connection
        cursor = conn.cursor()

        #Insert feedback into the Feedback table
        cursor.execute('''
            INSERT INTO Feedback (EmployeeID, FeedbackType, Description, CreatedAt, ReviewStatus)
            VALUES (?, ?, ?, GETDATE(), 'Pending')
        ''', data['EmployeeID'], data['FeedbackType'], data['Description'])

        #Check if feedback is urgent and update accordingly
        if 'Urgent' in data.get('FeedbackType', ''):
            cursor.execute('''
                UPDATE Feedback
                SET ReviewStatus = 'Urgent'
                WHERE FeedbackID = (SELECT MAX(FeedbackID) FROM Feedback)
            ''')
            conn.commit()

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Feedback added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/view', methods=['GET'])
def view_feedback():
    try:
        conn = connection
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

#----------- Inventory management  -----------

@app.route('/inventory/view', methods=['GET'])
def view_inventory():
    try:
        conn = connection
        cursor = conn.cursor()
        
        #Join inventory with menu_items to get more detailed information
        cursor.execute('''
            SELECT i.id, i.itemid, i.quantity_available, i.last_updated, i.manager_id,
                   m.name AS menu_item_name, m.category AS menu_item_category
            FROM inventory i
            JOIN menu_items m ON i.itemid = m.id
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
        conn.close()
        
        return jsonify(inventory_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

#-------  Alert for low inventory -----

@app.route('/inventory/alerts', methods=['GET'])
def inventory_alerts():
    try:
        conn = connection
        cursor = conn.cursor()
        
        #Query for low inventory (e.g., threshold of 10 units)
        cursor.execute('''
            SELECT i.id, i.itemid, i.quantity_available, m.name AS menu_item_name
            FROM inventory i
            JOIN menu_items m ON i.itemid = m.id
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
        conn.close()
        
        return jsonify(low_inventory_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
  

if __name__ == '__main__':
    app.run(debug=True)



