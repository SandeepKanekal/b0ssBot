# Copyright (c) 2022 Sandeep Kanekal
import psycopg2
import os
from typing import Any


class SQL(object):

    def __init__(self, database: str) -> None:
        self.database = database

    def commit_and_close_connection(self, conn, cursor):
        conn.commit()
        cursor.close()
        conn.close()

    def select(self, elements: list, table: str, where: str = None) -> list[tuple[Any, ...]]:
        """
        Selects elements from a database.

        Parameters
        ----------
        elements : list
            The elements to select.
        table : str
            The table to select from.
        where : str, optional
            The where clause. The default is None.

        Returns
        -------
        list[tuple[Any, ...]]
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
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

        Parameters
        ----------
        table : str
            The table to update.
        column : str
            The column to update.
        value : Any
            The value to update.
        where : str, optional
            The where clause. The default is None.

        Returns
        -------
        None
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Update the database
        if where is None:
            cursor.execute(f'UPDATE {table} SET {column} = {value}')
        else:
            cursor.execute(f'UPDATE {table} SET {column} = {value} WHERE {where}')
        self.commit_and_close_connection(conn, cursor)

    def insert(self, table: str, columns: list, values: list) -> None:
        """
        Inserts into a database.

        Parameters
        ----------
        table : str
            The table to insert into.
        columns : list
            The columns to insert.
        values : list
            The values to insert.

        Returns
        -------
        None
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Converting to strings
        column_str = ', '.join(columns)
        value_str = ', '.join(values)
        # Insert into the database
        cursor.execute(f'INSERT INTO {table}({column_str}) VALUES({value_str})')
        self.commit_and_close_connection(conn, cursor)

    def delete(self, table: str, where: str = None) -> None:
        """
        Deletes from a database.

        Parameters
        ----------
        table : str
            The table to delete from.
        where : str, optional
            The where clause. The default is None.

        Returns
        -------
        None
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Delete from the database
        cursor.execute(f'DELETE FROM {table} WHERE {where}' if where else f'DELETE FROM {table}')
        self.commit_and_close_connection(conn, cursor)

    def query(self, q) -> Any:
        """
        Queries a database.

        Parameters
        ----------
        q : str
            The query to run.

        Returns
        -------
        Any
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Query the database
        cursor.execute(q)
        # Fetch the results
        results = cursor.fetchall() if q.startswith('SELECT') or q.startswith('select') else None
        if not q.startswith('SELECT') or not q.startswith('select'):
            conn.commit()  # Commit
        # Close the connection
        cursor.close()
        conn.close()
        return results
# Copyright (c) 2022 Sandeep Kanekal
import psycopg2
import os
from typing import Any


class SQL(object):

    def __init__(self, database: str) -> None:
        self.database = database

    def commit_and_close_connection(self, conn, cursor):
        conn.commit()
        cursor.close()
        conn.close()

    def select(self, elements: list, table: str, where: str = None) -> list[tuple[Any, ...]]:
        """
        Selects elements from a database.

        Parameters
        ----------
        elements : list
            The elements to select.
        table : str
            The table to select from.
        where : str, optional
            The where clause. The default is None.

        Returns
        -------
        list[tuple[Any, ...]]
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
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

        Parameters
        ----------
        table : str
            The table to update.
        column : str
            The column to update.
        value : Any
            The value to update.
        where : str, optional
            The where clause. The default is None.

        Returns
        -------
        None
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Update the database
        if where is None:
            cursor.execute(f'UPDATE {table} SET {column} = {value}')
        else:
            cursor.execute(f'UPDATE {table} SET {column} = {value} WHERE {where}')
        self.commit_and_close_connection(conn, cursor)

    def insert(self, table: str, columns: list, values: list) -> None:
        """
        Inserts into a database.

        Parameters
        ----------
        table : str
            The table to insert into.
        columns : list
            The columns to insert.
        values : list
            The values to insert.

        Returns
        -------
        None
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Converting to strings
        column_str = ', '.join(columns)
        value_str = ', '.join(values)
        # Insert into the database
        cursor.execute(f'INSERT INTO {table}({column_str}) VALUES({value_str})')
        self.commit_and_close_connection(conn, cursor)

    def delete(self, table: str, where: str = None) -> None:
        """
        Deletes from a database.

        Parameters
        ----------
        table : str
            The table to delete from.
        where : str, optional
            The where clause. The default is None.

        Returns
        -------
        None
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Delete from the database
        cursor.execute(f'DELETE FROM {table} WHERE {where}' if where else f'DELETE FROM {table}')
        self.commit_and_close_connection(conn, cursor)

    def query(self, q) -> Any:
        """
        Queries a database.

        Parameters
        ----------
        q : str
            The query to run.

        Returns
        -------
        Any
        """
        # Connect to the database
        conn = psycopg2.connect(user=os.getenv('sql_user'), password=os.getenv('sql_password'), database=self.database,
                                host=os.getenv('sql_host'))
        cursor = conn.cursor()
        # Query the database
        cursor.execute(q)
        # Fetch the results
        results = cursor.fetchall() if q.startswith('SELECT') or q.startswith('select') else None
        if not q.startswith('SELECT') or not q.startswith('select'):
            conn.commit()  # Commit
        # Close the connection
        cursor.close()
        conn.close()
        return results
