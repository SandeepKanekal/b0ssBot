import psycopg2
import os
from typing import Any


class SQL(object):

    def __init__(self, database: str) -> None:
        self.database = database

    def select(self, elements: list, table: str, where: str = None) -> list[tuple[Any, ...]]:
        """
        Selects elements from a database.
        """
        # Connect to the database
        conn = psycopg2.connect(user='postgres', password=os.getenv('sql_password'), database=self.database,
                                host='localhost')
        cursor = conn.cursor()
        element_str = ', '.join(elements)
        # Select the elements
        if where is None:
            cursor.execute(f'SELECT {element_str} FROM {table}')
        else:
            cursor.execute(f'SELECT {element_str} FROM {table} WHERE {where}')
        # Fetch the results
        results = cursor.fetchall()
        # Close the connection
        cursor.close()
        conn.close()
        return results

    def update(self, table: str, column: str, value: Any, where: str = None) -> None:
        """
        Updates a database.
        """
        # Connect to the database
        conn = psycopg2.connect(user='postgres', password=os.getenv('sql_password'), database=self.database,
                                host='localhost')
        cursor = conn.cursor()
        # Update the database
        if where is None:
            cursor.execute(f'UPDATE {table} SET {column} = {value}')
        else:
            cursor.execute(f'UPDATE {table} SET {column} = {value} WHERE {where}')
        # Commit
        conn.commit()
        # Close the connection
        cursor.close()
        conn.close()

    def insert(self, table: str, columns: list, values: list) -> None:
        """
        Inserts into a database.
        """
        # Connect to the database
        conn = psycopg2.connect(user='postgres', password=os.getenv('sql_password'), database=self.database,
                                host='localhost')
        cursor = conn.cursor()
        # Converting to strings
        column_str = ', '.join(columns)
        value_str = ', '.join(values)
        # Insert into the database
        cursor.execute(f'INSERT INTO {table}({column_str}) VALUES({value_str})')
        # Commit
        conn.commit()
        # Close the connection
        cursor.close()
        conn.close()

    def delete(self, table: str, where: str):
        """
        Deletes from a database.
        """
        # Connect to the database
        conn = psycopg2.connect(user='postgres', password=os.getenv('sql_password'), database=self.database,
                                host='localhost')
        cursor = conn.cursor()
        # Delete from the database
        cursor.execute(f'DELETE FROM {table} WHERE {where}')
        # Commit
        conn.commit()
        # Close the connection
        cursor.close()
        conn.close()

    def query(self, q) -> Any:
        """
        Queries a database.
        """
        # Connect to the database
        conn = psycopg2.connect(user='postgres', password=os.getenv('sql_password'), database=self.database,
                                host='localhost')
        cursor = conn.cursor()
        # Query the database
        cursor.execute(q)
        # Fetch the results
        results = cursor.fetchall() if q.startswith('SELECT') else None
        # Close the connection
        cursor.close()
        conn.close()
        return results
