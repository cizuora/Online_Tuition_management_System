"""
@file init_db.py
@date 4-8-2026
@author Chidera Izuora and Murat Talum
@version 1.0

@brief This script initializes the SQLite database for the project. It creates the necessary tables and inserts initial data, including a default admin user with a hashed password.

This module creates the SQLite database with necessary tables and default data
- students: stores student account information and current balance
- fee_items: stores semester-specific fee line items per student
- payments: records payment transaction history

Usage:
    python init_db.py
"""

# init_db.py
import sqlite3
import hashlib
from datetime import datetime

"""
    @brief Hashes a plain-text password using SHA-256.
    @param password The plain-text password to hash.
    @return The hashed password as a hexadecimal string.
    """
def hash_password(password: str) -> str:
  

    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

"""
        @class InitDB
        @brief Handles the initialization of the SQLite database, including creating tables, schema setup and inserting default data.

        This class is responsible for all database setup operations including:
        - Creating database tables with proper schema
        - Inserting default/sample data for testing and initial use
        - Managing database connections

        @note Run only once when setting up the application for the first time. Subsequent runs may overwrite existing data.
    """
class InitDB:
    """
        @brief constructor for InitDB class.
        @param db_path The file path for the SQLite database. Defaults to 'tuition.db'.
        @note conn and cursor are initialized to None and will be set when connect() is called.

        Initializes the database connection but does not create tables yet.
        Call create_tables() and insert_sample_data() separately
    """
    
    def __init__(self, db_path: str = 'tuition.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    """
        @brief Etablish a connection to SQLite database.
        @throws sqlite3.Error if connection fails.
        @note Automatically creates database file if it does not exist.
    """        
    def connect(self) -> None:
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    """
        @brief Closes the database connection and cursor if they are open.
        @note Always call this method after database operations to free resources.
    """        
    def disconnect(self) -> None:
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Database connection closed.")    


    """

    """
    def create_tables(self) -> None: