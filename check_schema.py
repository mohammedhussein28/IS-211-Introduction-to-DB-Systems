import pyodbc

# Update with your connection string
conn_str = (
    "Driver={SQL Server};"
    "Server=localhost;"  # Change this to your server
    "Database=RenewableEnergyGridDB;"  # Fixed database name
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

tables = ['Technician', 'PowerUnit', 'Inspection', 'InspectionRecord', 'Replacement']

for table in tables:
    print(f"\n{'='*50}")
    print(f"TABLE: {table}")
    print('='*50)
    
    try:
        query = f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
        """
        cursor.execute(query)
        columns = cursor.fetchall()
        
        if columns:
            for col in columns:
                print(f"  {col[0]} ({col[1]}) - Nullable: {col[2]}")
        else:
            print(f"  Table '{table}' not found or no columns")
    except Exception as e:
        print(f"  Error: {e}")

conn.close()