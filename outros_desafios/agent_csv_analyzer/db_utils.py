import sqlite3
import tempfile
from typing import Dict, List, Any
import threading

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.db_path = None
        self._local = threading.local()

    def initialize(self):
        """Initialize SQLite database in memory"""
        # Create a new connection for the current thread
        self._local.conn = sqlite3.connect(':memory:')
        self._local.cursor = self._local.conn.cursor()
        return self

    def _get_connection(self):
        """Get the connection for the current thread"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(':memory:')
            self._local.cursor = self._local.conn.cursor()
        return self._local.conn, self._local.cursor

    def _escape_identifier(self, identifier: str) -> str:
        """Escape SQLite identifier (table or column name)"""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    def _sanitize_column_name(self, column_name: str) -> str:
        """Transform column name to lowercase and replace spaces with underscores"""
        # Convert to lowercase
        sanitized = column_name.lower()
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Remove any special characters except underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
        # Remove consecutive underscores
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        # Remove leading and trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized

    def create_table_from_csv(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """Create a table from CSV data"""
        if not data:
            return

        conn, cursor = self._get_connection()

        # Create table with appropriate columns
        original_columns = list(data[0].keys())
        sanitized_columns = [self._sanitize_column_name(col) for col in original_columns]
        
        # Create a mapping of original column names to sanitized names
        column_mapping = dict(zip(original_columns, sanitized_columns))
        
        # Create table with sanitized column names
        escaped_columns = [self._escape_identifier(col) for col in sanitized_columns]
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self._escape_identifier(table_name)} (
            {', '.join(f'{col} TEXT' for col in escaped_columns)}
        )
        """
        cursor.execute(create_table_sql)

        # Insert data with sanitized column names
        placeholders = ', '.join(['?' for _ in sanitized_columns])
        insert_sql = f"""
        INSERT INTO {self._escape_identifier(table_name)} ({', '.join(escaped_columns)})
        VALUES ({placeholders})
        """
        # Transform data to use sanitized column names
        transformed_data = []
        for row in data:
            transformed_row = [str(row[orig_col]) for orig_col in original_columns]
            transformed_data.append(transformed_row)

        cursor.executemany(insert_sql, transformed_data)
        conn.commit()

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information for all tables"""
        conn, cursor = self._get_connection()
        schema_info = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({self._escape_identifier(table_name)})")
            columns = cursor.fetchall()
            schema_info[table_name] = {
                'columns': [col[1] for col in columns],
                'types': [col[2] for col in columns]
            }
        return schema_info

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results"""
        try:
            conn, cursor = self._get_connection()
            print(query)
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(e)
            raise Exception(f"Error executing query: {str(e)}")

    def export_database(self) -> bytes:
        """Export database to bytes"""
        conn, _ = self._get_connection()
        if not conn:
            return None
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Export the in-memory database to the temporary file
            backup = sqlite3.connect(tmp.name)
            conn.backup(backup)
            backup.close()
            
            # Read the file and return its contents
            with open(tmp.name, 'rb') as f:
                return f.read() 