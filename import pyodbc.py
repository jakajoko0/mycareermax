import os
import pyodbc

# Initialize conn to None
conn = None

# Read environment variables
DB_NAME = os.environ.get("DB_NAME")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_SERVER = os.environ.get("DB_SERVER")
DRIVER = "{ODBC Driver 18 for SQL Server}"

# Create the connection string
connection_string = f"Driver={DRIVER};Server={DB_SERVER};Database={DB_NAME};User Id={DB_USERNAME};Password={DB_PASSWORD};"

try:
    # Create a new database connection and cursor
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # Test the connection
    cursor.execute("SELECT @@VERSION;")
    row = cursor.fetchone()
    if row:
        print("Successfully connected to the database. SQL Server version is:", row[0])
    else:
        print("Failed to retrieve data.")

except pyodbc.Error as e:
    print(f"An error occurred: {e}")

finally:
    # Close the database connection
    if conn:
        conn.close()
