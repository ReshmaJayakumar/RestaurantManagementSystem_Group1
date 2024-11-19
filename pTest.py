import pyodbc
import csv
from datetime import datetime, timedelta

# Database Connection
def connect_to_database():
    """
    Establish a connection to the SQL Server database.
    Returns the connection object if successful, otherwise None.
    """
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=GurjotsAcer\\SQLEXPRESS01;"
        "Database=RestaurantManagement;"
        "Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        print("Successfully connected to the database.")
        return conn
    except pyodbc.Error as e:
        print("Error connecting to the database:", e)
        return None

# Financial Reports
def view_financial_reports(cursor):
    """View all financial reports."""
    try:
        cursor.execute("SELECT * FROM FinancialReports")
        reports = cursor.fetchall()
        if reports:
            print("Financial Reports:")
            for row in reports:
                print(row)
        else:
            print("No financial reports found.")
    except Exception as e:
        print("Error retrieving financial reports:", e)

def download_financial_reports(cursor):
    """Download financial reports to a CSV file."""
    file_name = input("Enter file name to save the reports: ") + ".csv"
    try:
        cursor.execute("SELECT * FROM FinancialReports")
        reports = cursor.fetchall()
        if reports:
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([column[0] for column in cursor.description])  # Write headers
                writer.writerows(reports)
            print(f"Reports downloaded successfully to {file_name}.")
        else:
            print("No financial reports found to download.")
    except Exception as e:
        print("Error downloading financial reports:", e)

def view_filtered_reports(cursor):
    """View financial reports filtered by time range."""
    print("\nFilter options:")
    print("1. Daily")
    print("2. Weekly")
    print("3. Monthly")
    print("4. Yearly")
    choice = input("Enter your choice for filter: ")

    filter_map = {
        '1': timedelta(days=1),
        '2': timedelta(weeks=1),
        '3': timedelta(days=30),
        '4': timedelta(days=365)
    }

    if choice not in filter_map:
        print("Invalid choice.")
        return

    try:
        filter_date = datetime.now() - filter_map[choice]
        cursor.execute("SELECT * FROM FinancialReports WHERE CreatedDate >= ?", filter_date)
        reports = cursor.fetchall()
        if reports:
            for row in reports:
                print(row)
        else:
            print("No financial reports found for the selected period.")
    except Exception as e:
        print("Error retrieving filtered financial reports:", e)

# User Management
def manage_users(cursor, conn):
    """User management options."""
    while True:
        print("\nUser Management:")
        print("1. Create User")
        print("2. Delete User")
        print("3. Change User Role")
        print("4. Back to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            create_user(cursor, conn)
        elif choice == '2':
            delete_user(cursor, conn)
        elif choice == '3':
            change_user_role(cursor, conn)
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

def create_user(cursor, conn):
    """Create a new user."""
    user_name = input("Enter user name: ")
    user_role = input("Enter user role (Employee/Manager): ")
    try:
        cursor.execute("INSERT INTO Users (UserName, UserRole) VALUES (?, ?)", (user_name, user_role))
        conn.commit()
        print(f"User {user_name} with role {user_role} created successfully.")
    except Exception as e:
        print("Error creating user:", e)

def delete_user(cursor, conn):
    """Delete an existing user."""
    user_id = input("Enter user ID to delete: ")
    try:
        cursor.execute("DELETE FROM Users WHERE UserID=?", (user_id,))
        conn.commit()
        print(f"User with ID {user_id} deleted successfully.")
    except Exception as e:
        print("Error deleting user:", e)

def change_user_role(cursor, conn):
    """Change a user's role."""
    user_id = input("Enter user ID to change role: ")
    new_role = input("Enter new role (Employee/Manager): ")
    try:
        cursor.execute("UPDATE Users SET UserRole=? WHERE UserID=?", (new_role, user_id))
        conn.commit()
        print(f"User with ID {user_id} role changed to {new_role}.")
    except Exception as e:
        print("Error changing user role:", e)

# Main Menu
def main():
    """Main program loop."""
    conn = connect_to_database()
    if not conn:
        return

    cursor = conn.cursor()

    while True:
        print("\nMain Menu:")
        print("1. View Financial Reports")
        print("2. Download Financial Reports")
        print("3. View Filtered Financial Reports")
        print("4. Manage Users")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            view_financial_reports(cursor)
        elif choice == '2':
            download_financial_reports(cursor)
        elif choice == '3':
            view_filtered_reports(cursor)
        elif choice == '4':
            manage_users(cursor, conn)
        elif choice == '5':
            print("Exiting the application.")
            break
        else:
            print("Invalid choice. Please try again.")

    conn.close()

if __name__ == "__main__":
    main()
