from flask import Flask, render_template, request, send_file, jsonify
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
    if request.method == 'POST':
        return submit_availability()
    return render_template('availability.html')

# Function to handle availability submission
def submit_availability():
    employee_id = request.form.get('employee_id')
    available_days = request.form.getlist('available_day')
    start_hours = request.form.getlist('start_hour')
    start_minutes = request.form.getlist('start_minute')
    end_hours = request.form.getlist('end_hour')
    end_minutes = request.form.getlist('end_minute')

    try:
        cursor = connection.cursor()
        for day, start_hour, start_minute, end_hour, end_minute in zip(available_days, start_hours, start_minutes, end_hours, end_minutes):
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
        return jsonify({"error": str(e)})

    # Return success message
    return jsonify({"status": "Availability submitted successfully"})


# Route to view and download pay stubs
@app.route('/paystubs', methods=['POST'])
def paystubs():
    if request.method == 'POST':
        return download_paystub()
    return render_template('paystubs.html')
# Function to fetch and download the pay stub
def download_paystub():
    employee_id = request.form.get('employee_id')
    month = request.form.get('month')
    year = request.form.get('year')

    try:
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
                return jsonify({"error": "File not found on the server."})
        else:
            return jsonify({"error": "No matching pay stub found."})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
