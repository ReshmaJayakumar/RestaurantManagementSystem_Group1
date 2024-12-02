import pyodbc
import pandas as pd

# Database connection setup
def connect_to_database():
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=GurjotsAcer\\SQLEXPRESS01;"
        "Database=pRestMgt;"
        "Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        print("Successfully connected to the database.")
        return conn
    except pyodbc.Error as e:
        print("Error connecting to the database:", e)
        return None

# Establish connection and create a cursor object
conn = connect_to_database()
if conn:
    cursor = conn.cursor()
else:
    raise Exception("Failed to connect to the database.")

# Function to fetch data and convert to DataFrame
def fetch_data(query):
    return pd.read_sql(query, conn)

# Function to view & download financial reports
def generate_financial_report(filter_type='daily'):
    if filter_type == 'daily':
        query = """
        SELECT * FROM FinancialReports
        WHERE CONVERT(date, Date) = CONVERT(date, GETDATE())
        """
    elif filter_type == 'weekly':
        query = """
        SELECT * FROM FinancialReports
        WHERE DATEPART(week, Date) = DATEPART(week, GETDATE()) AND DATEPART(year, Date) = DATEPART(year, GETDATE())
        """
    elif filter_type == 'monthly':
        query = """
        SELECT * FROM FinancialReports
        WHERE DATEPART(month, Date) = DATEPART(month, GETDATE()) AND DATEPART(year, Date) = DATEPART(year, GETDATE())
        """
    elif filter_type == 'yearly':
        query = """
        SELECT * FROM FinancialReports
        WHERE DATEPART(year, Date) = DATEPART(year, GETDATE())
        """
    else:
        print("Invalid filter type. Please choose from 'daily', 'weekly', 'monthly', or 'yearly'.")
        return None

    df = fetch_data(query)
    df.to_csv(f'financial_report_{filter_type}.csv')
    return df

# User management functions
def view_users():
    query = """
    SELECT * FROM Users
    """
    return fetch_data(query)

def create_user(username, role):
    query = """
    INSERT INTO Users (Username, Role)
    VALUES (?, ?)
    """
    cursor.execute(query, username, role)
    conn.commit()
    print(f"User '{username}' with role '{role}' has been added successfully.")

def delete_user(username):
    query = """
    DELETE FROM Users WHERE Username = ?
    """
    cursor.execute(query, username)
    conn.commit()
    print(f"User '{username}' has been deleted successfully.")

def change_user_role(username, new_role):
    query = """
    UPDATE Users
    SET Role = ?
    WHERE Username = ?
    """
    cursor.execute(query, new_role, username)
    conn.commit()
    print(f"User '{username}' role has been changed to '{new_role}' successfully.")

# Performance tracking
def track_performance():
    query = """
    SELECT KPI, Value FROM PerformanceIndicators
    """
    return fetch_data(query)

def generate_comparative_report(period='weekdays'):
    query = """
    SELECT * FROM PerformanceReports
    WHERE Period = ?
    """
    return fetch_data(query, [period])

# Customer analytics functions
def monitor_customer_trends():
    query = """
    SELECT TOP 10 Item, SUM(Quantity) AS TotalSold
    FROM Sales
    GROUP BY Item
    ORDER BY TotalSold DESC
    """
    return fetch_data(query)

def review_customer_feedback():
    query = """
    SELECT Feedback, COUNT(*) AS Frequency
    FROM CustomerFeedback
    GROUP BY Feedback
    """
    return fetch_data(query)

# Promotion management functions
def view_promotions():
    query = """
    SELECT * FROM Promotions
    """
    return fetch_data(query)

def add_promotion(promo_code, discount, expiry_date):
    query = """
    INSERT INTO Promotions (PromoCode, Discount, ExpiryDate)
    VALUES (?, ?, ?)
    """
    cursor.execute(query, promo_code, discount, expiry_date)
    conn.commit()
    print(f"Promotion '{promo_code}' with discount {discount}% has been added successfully.")

def delete_promotion(promo_code):
    query = """
    DELETE FROM Promotions WHERE PromoCode = ?
    """
    cursor.execute(query, promo_code)
    conn.commit()
    print(f"Promotion '{promo_code}' has been deleted successfully.")

# Compliance management functions
def view_compliance_info():
    query = """
    SELECT * FROM ComplianceDocuments
    """
    return fetch_data(query)

def review_compliance_info():
    query = """
    SELECT * FROM ComplianceDocuments
    """
    return fetch_data(query)

def check_compliance_deadlines():
    query = """
    SELECT * FROM ComplianceDeadlines
    WHERE Deadline > GETDATE()
    """
    return fetch_data(query)

# Console application menu
def menu():
    print("Restaurant Management System")
    print("1. View & Download Financial Reports")
    print("2. User Management")
    print("3. Performance Tracking")
    print("4. Customer Analytics")
    print("5. Promotion Management")
    print("6. Compliance Management")
    print("7. Exit")

def user_management_menu():
    print("User Management")
    print("1. View Users")
    print("2. Create User")
    print("3. Delete User")
    print("4. Change User Role")
    print("5. Back to Main Menu")

def customer_analytics_menu():
    print("Customer Analytics")
    print("1. Monitor Customer Trends")
    print("2. Review Customer Feedback")
    print("3. Back to Main Menu")

def promotion_management_menu():
    print("Promotion Management")
    print("1. View Promotions")
    print("2. Add Promotion")
    print("3. Delete Promotion")
    print("4. Back to Main Menu")

def compliance_management_menu():
    print("Compliance Management")
    print("1. View Compliance Info")
    print("2. Review Compliance Info")
    print("3. Check Compliance Deadlines")
    print("4. Back to Main Menu")

def main():
    while True:
        menu()
        choice = input("Enter your choice: ")
        
        if choice == '1':
            filter_type = input("Enter filter type (daily, weekly, monthly, yearly): ")
            df = generate_financial_report(filter_type)
            if df is not None:
                print(df)
        elif choice == '2':
            while True:
                user_management_menu()
                user_choice = input("Enter your choice: ")
                if user_choice == '1':
                    df = view_users()
                    if not df.empty:
                        print(df)
                elif user_choice == '2':
                    username = input("Enter username: ")
                    role = input("Enter role (employee, manager): ")
                    create_user(username, role)
                elif user_choice == '3':
                    username = input("Enter username: ")
                    delete_user(username)
                elif user_choice == '4':
                    username = input("Enter username: ")
                    new_role = input("Enter new role (employee, manager): ")
                    change_user_role(username, new_role)
                elif user_choice == '5':
                    break
                else:
                    print("Invalid action.")
        elif choice == '3':
            df = track_performance()
            if not df.empty:
                print(df)
        elif choice == '4':
            while True:
                customer_analytics_menu()
                analytics_choice = input("Enter your choice: ")
                if analytics_choice == '1':
                    df = monitor_customer_trends()
                    if not df.empty:
                        print(df)
                elif analytics_choice == '2':
                    df = review_customer_feedback()
                    if not df.empty:
                        print(df)
                elif analytics_choice == '3':
                    break
                else:
                    print("Invalid action.")
        elif choice == '5':
            while True:
                promotion_management_menu()
                promo_choice = input("Enter your choice: ")
                if promo_choice == '1':
                    df = view_promotions()
                    if not df.empty:
                        print(df)
                elif promo_choice == '2':
                    promo_code = input("Enter promo code: ")
                    discount = float(input("Enter discount percentage: "))
                    expiry_date = input("Enter expiry date (YYYY-MM-DD): ")
                    add_promotion(promo_code, discount, expiry_date)
                elif promo_choice == '3':
                    promo_code = input("Enter promo code: ")
                    delete_promotion(promo_code)
                elif promo_choice == '4':
                    break
                else:
                    print("Invalid action.")
        elif choice == '6':
            while True:
                compliance_management_menu()
                compliance_choice = input("Enter your choice: ")
                if compliance_choice == '1':
                    df = view_compliance_info()
                    if not df.empty:
                        print(df)
                elif compliance_choice == '2':
                    df = review_compliance_info()
                    if not df.empty:
                        print(df)
                elif compliance_choice == '3':
                    df = check_compliance_deadlines()
                    if not df.empty:
                        print(df)
                elif compliance_choice == '4':
                    break
                else:
                    print("Invalid action.")
        elif choice == '7':
            print("Exiting the system.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
