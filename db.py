import pyodbc


class Database:
    def __init__(self):
        self.connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=RenewableEnergyGridDB;"
            "Trusted_Connection=yes;"
        )

    def get_connection(self):
        return pyodbc.connect(self.connection_string)

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return rows

    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        columns = [col[0] for col in cursor.description]
        result = dict(zip(columns, row))
        conn.close()
        return result

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        conn.close()

    def next_id(self, table, column):
        query = f"SELECT ISNULL(MAX({column}), 0) + 1 AS next_id FROM {table}"
        result = self.fetch_one(query)
        return result["next_id"]