"""
@file init_db.py
@date 2026-04-08
@author Chidera Izuora and Murat Talum
@version 1.2

@brief Initializes the database with necessary tables and default data.

This module creates the SQLite database 'tuition.db' with three tables:
- students: Stores student account information and current balance
- fee_items: Stores semester-specific fee line items per student
- payments: Records payment transaction history

The database is pre-populated with sample data for testing:
- 2 student accounts (John Doe, Jane Smith) with student IDs
- 1 admin account
- Fee items for Spring 2026 semester

Changes in v1.2:
- Changed balance/amount columns from REAL to DECIMAL(10,2) for precise currency
- Added two decimal place formatting for all monetary values

Usage:
    python init_db.py
"""

import sqlite3
import hashlib
from datetime import datetime


def hash_password(password: str) -> str:
    """
    @brief Hashes a plaintext password using SHA-256 algorithm.

    @param password Plaintext password string to hash
    @return Hexadecimal string representation of the SHA-256 hash

    @note This is a one-way hash - cannot be reversed to original password
    @warning For production, use bcrypt or PBKDF2 with salt instead of SHA-256
    """
    return hashlib.sha256(password.encode()).hexdigest()


class InitDB:
    """
    @class InitDB
    @brief Handles database initialization and schema setup.

    This class encapsulates all database setup operations including:
    - Creating database tables with proper schema
    - Inserting default/sample data
    - Managing database connections

    @note Run only once when setting up the application for the first time
    """

    def __init__(self, db_path: str = "tuition.db"):
        """
        @brief Constructor for InitDB class.
        @param db_path Path to SQLite database file (default: 'tuition.db')
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    def connect(self) -> None:
        """
        @brief Establishes connection to SQLite database.

        @throws sqlite3.Error If connection fails (file permissions, disk full, etc.)
        @note Automatically creates database file if it doesn't exist
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f"✓ Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"✗ Database connection failed: {e}")
            raise

    def disconnect(self) -> None:
        """
        @brief Closes database connection and cursor.

        @note Always call this after database operations to free resources
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✓ Database connection closed")

    def reset_database(self) -> None:
        """
        @brief Drops all tables (for fresh start).

        @warning This deletes ALL data! Use carefully.
        """
        print("Resetting database (deleting all tables)...")

        self.cursor.execute("DROP TABLE IF EXISTS payments")
        self.cursor.execute("DROP TABLE IF EXISTS fee_items")
        self.cursor.execute("DROP TABLE IF EXISTS students")
        print("  ✓ All tables dropped")

        self.connection.commit()

    def create_tables(self) -> None:
        """
        @brief Creates all necessary tables if they don't exist.

        Creates three tables:
        1. students - Account information and current balance (DECIMAL for currency)
        2. fee_items - Semester-specific charges per student (DECIMAL for amounts)
        3. payments - Payment transaction history (DECIMAL for amounts)

        @throws sqlite3.Error If SQL syntax is invalid or constraint fails
        @note Uses IF NOT EXISTS so running multiple times is safe
        """
        print("Creating tables...")

        # Table 1: students with DECIMAL for balance (two decimal places)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                balance DECIMAL(10,2) DEFAULT 0.00,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("  ✓ students table created")

        # Create index for fast student_id lookups (login optimization)
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_student_id ON students(student_id)
        """
        )
        print("  ✓ index on student_id created")

        # Table 2: fee_items with DECIMAL for amount
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fee_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """
        )
        print("  ✓ fee_items table created")

        # Table 3: payments with DECIMAL for amount
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mock_mode BOOLEAN DEFAULT 1,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """
        )
        print("  ✓ payments table created")

        self.connection.commit()
        print("✓ All tables created successfully")

    def insert_sample_data(self) -> None:
        """
        @brief Populates database with sample data for testing.

        Inserts:
        - 2 student accounts (John Doe, Jane Smith) with different balances
        - 1 admin account with ID 99
        - Fee items for Spring 2026 semester for John Doe

        @note Uses INSERT OR REPLACE to allow re-running without errors
        @warning Sample passwords are 'pass123' for students and 'admin123' for admin
        """
        print("Inserting sample data...")

        # Updated: (id, student_id, name, email, password_hash, balance, role)
        # Balance values are DECIMAL - will store exactly with 2 decimal places
        sample_students = [
            (
                1,
                "sh046186",
                "John Doe",
                "john@university.edu",
                hash_password("pass123"),
                4250.00,
                "student",
            ),
            (
                2,
                "sh089234",
                "Jane Smith",
                "jane@university.edu",
                hash_password("pass123"),
                1250.00,
                "student",
            ),
            (
                99,
                "admin001",
                "Admin User",
                "admin@university.edu",
                hash_password("admin123"),
                0.00,
                "admin",
            ),
        ]

        self.cursor.executemany(
            """
            INSERT OR REPLACE INTO students (id, student_id, name, email, password_hash, balance, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            sample_students,
        )
        print("  ✓ 3 user accounts inserted (2 students, 1 admin)")
        print("    Student logins: sh046186, sh089234")
        print("    Admin login: admin001")

        # Fee items with DECIMAL amounts
        sample_fee_items = [
            (1, 1, "Spring 2026", "Tuition - 12 credits", 3600.00, "Tuition"),
            (2, 1, "Spring 2026", "Lab Fees - Chemistry 101", 350.00, "Fees"),
            (3, 1, "Spring 2026", "Library Services Fee", 150.00, "Fees"),
            (4, 1, "Spring 2026", "Student Activity Fee", 150.00, "Fees"),
        ]

        self.cursor.executemany(
            """
            INSERT OR REPLACE INTO fee_items (id, student_id, semester, description, amount, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            sample_fee_items,
        )
        print("  ✓ Fee items inserted for John Doe (Spring 2026)")

        self.connection.commit()
        print("✓ All sample data inserted successfully")

    def verify_data(self) -> dict:
        """
        @brief Verifies that database was populated correctly.

        @return Dictionary containing counts of records in each table
        @throws sqlite3.Error If verification queries fail
        @note Useful for debugging and confirming successful initialization
        """
        print("\nVerifying database contents...")

        verification = {}

        # Count students
        self.cursor.execute("SELECT COUNT(*) FROM students")
        verification["students"] = self.cursor.fetchone()[0]
        print(f"  Students: {verification['students']}")

        # Count fee items
        self.cursor.execute("SELECT COUNT(*) FROM fee_items")
        verification["fee_items"] = self.cursor.fetchone()[0]
        print(f"  Fee items: {verification['fee_items']}")

        # Count payments
        self.cursor.execute("SELECT COUNT(*) FROM payments")
        verification["payments"] = self.cursor.fetchone()[0]
        print(f"  Payments: {verification['payments']}")

        # Show student details with formatted balance (2 decimal places)
        self.cursor.execute(
            """
            SELECT id, student_id, name, email, balance, role FROM students
        """
        )
        students = self.cursor.fetchall()
        print("\n  Student accounts created:")
        for student in students:
            # Format balance to always show 2 decimal places
            balance_formatted = f"${student[4]:.2f}"
            print(
                f"    - ID: {student[0]}, Student ID: {student[1]}, "
                f"Name: {student[2]}, Balance: {balance_formatted}, Role: {student[5]}"
            )

        return verification

    def run(self, reset: bool = False) -> bool:
        """
        @brief Executes complete database initialization workflow.

        @param reset If True, drops existing tables before creating new ones
        @return True if initialization successful, False otherwise

        Workflow:
        1. Connect to database
        2. Optionally reset (drop all tables)
        3. Create all tables
        4. Insert sample data
        5. Verify data integrity
        6. Disconnect

        @note This is the main method to call for full initialization
        """
        try:
            print("=" * 50)
            print("Tuition Management System - Database Initialization")
            print("=" * 50)

            self.connect()

            if reset:
                self.reset_database()

            self.create_tables()
            self.insert_sample_data()
            verification = self.verify_data()

            print("\n" + "=" * 50)
            print("✓ Database initialization completed successfully!")
            print(f"  - {verification['students']} students")
            print(f"  - {verification['fee_items']} fee items")
            print("=" * 50)

            return True

        except sqlite3.Error as e:
            print(f"\n✗ Database error occurred: {e}")
            return False
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            return False
        finally:
            self.disconnect()


# MAIN EXECUTION
if __name__ == "__main__":
    print(
        """
    
            Online Tuition Management System - Database Setup        
                                                                  
            Authors: Chidera Izuora & Murat Talum                    
            Date: April 8, 2026                                      
            Version: 1.2                                             
    """
    )

    # Create and run database initializer
    # Set reset=True to completely rebuild the database
    db_initializer = InitDB()
    success = db_initializer.run(reset=False)  # Change to True to force reset

    # Exit with appropriate code
    if success:
        print("\n✅ Ready to start the application!")
        print("   Run 'python app.py' to launch the web server.\n")
    else:
        print("\n❌ Initialization failed. Check errors above.\n")
        exit(1)
