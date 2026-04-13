"""
@file models.py
@date 2026-04-08
@author Chidera Izuora and Murat Talum
@version 1.2

@brief Data access layer with student ID authentication and decimal currency.

Changes in v1.2:
- Added balance formatting with two decimal places
- Improved docstrings for clarity
- Added helper method for formatted balance display
"""

import sqlite3
from typing import Optional


class Student:
    """
    @class Student
    @brief Represents a student record in the database.

    Maps to the 'students' table. Provides static methods for database
    queries and instance methods for updating individual records.
    All monetary values are stored as DECIMAL(10,2) in the database.
    """

    def __init__(
        self,
        id: int,
        student_id: str,
        name: str,
        email: str,
        password_hash: str,
        balance: float,
        role: str,
    ):
        """
        @brief Constructor for Student object.

        @param id Internal database ID (auto-increment)
        @param student_id Public-facing ID like "sh046186"
        @param name Full name of student
        @param email Email address (for notifications)
        @param balance Current outstanding tuition balance (float with 2 decimals)
        @param role Either 'student' or 'admin'
        """
        self.id = id
        self.student_id = student_id
        self.name = name
        self.email = email
        self.password_hash = password_hash  # ADD this line
        self.balance = balance
        self.role = role

    def get_formatted_balance(self) -> str:
        """
        @brief Returns balance formatted as currency with two decimal places.

        @return String like "$4,250.00" or "$1,250.50"

        @note Always use this for display to ensure proper formatting
        """
        return f"${self.balance:,.2f}"

    @staticmethod
    def find_by_student_id(student_id: str) -> Optional["Student"]:
        """
        @brief Find a student by their public student ID.

        @param student_id Format like "sh046186"
        @return Student object if found, None if not found

        This is the PRIMARY login method. Uses indexed column for fast lookup.
        """
        conn = sqlite3.connect("tuition.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Using the indexed column for fast lookup
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return Student(
                id=row["id"],
                student_id=row["student_id"],
                name=row["name"],
                email=row["email"],
                password_hash=row["password_hash"],  # ADD this
                balance=row["balance"],
                role=row["role"],
            )
        return None

    @staticmethod
    def find_by_id(id: int) -> Optional["Student"]:
        """
        @brief Find a student by internal database ID.

        @param id Internal ID (used for foreign keys)
        @return Student object if found, None if not found
        """
        conn = sqlite3.connect("tuition.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return Student(
                id=row["id"],
                student_id=row["student_id"],
                name=row["name"],
                email=row["email"],
                password_hash=row["password_hash"],  # ADD this
                balance=row["balance"],
                role=row["role"],
            )
        return None

    @staticmethod
    def get_all_students() -> list["Student"]:
        """
        @brief Get all students (for admin dashboard).

        @return List of Student objects
        """
        conn = sqlite3.connect("tuition.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students ORDER BY student_id")
        rows = cursor.fetchall()

        conn.close()

        students = []
        for row in rows:
            students.append(
                Student(
                    id=row["id"],
                    student_id=row["student_id"],
                    name=row["name"],
                    email=row["email"],
                    balance=row["balance"],
                    role=row["role"],
                )
            )
        return students

    def update_balance(self, new_balance: float) -> bool:
        """
        @brief Update this student's balance in the database.

        @param new_balance New balance amount (will be stored with 2 decimal precision)
        @return True if update succeeded, False otherwise

        @note Updates both database and instance attribute
        """
        conn = sqlite3.connect("tuition.db")
        cursor = conn.cursor()

        try:
            # Round to 2 decimal places before storing
            rounded_balance = round(new_balance, 2)
            cursor.execute(
                "UPDATE students SET balance = ? WHERE id = ?",
                (rounded_balance, self.id),
            )
            conn.commit()
            self.balance = rounded_balance
            return True
        except sqlite3.Error as e:
            print(f"Database error updating balance: {e}")
            return False
        finally:
            conn.close()

    def make_payment(self, amount: float) -> tuple[bool, str]:
        """
        @brief Process a payment for this student.

        @param amount Payment amount (positive number)
        @return Tuple of (success, message)

        This method:
        1. Validates the amount
        2. Checks if sufficient balance
        3. Updates balance
        4. Records payment in history
        """
        # Validate amount
        if amount <= 0:
            return False, "Payment amount must be positive"

        # Round to 2 decimal places
        amount = round(amount, 2)

        # Check sufficient balance
        if amount > self.balance:
            return False, f"Insufficient balance. Current balance: ${self.balance:.2f}"

        # Calculate new balance
        new_balance = round(self.balance - amount, 2)

        # Update balance
        conn = sqlite3.connect("tuition.db")
        cursor = conn.cursor()

        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")

            # Update balance
            cursor.execute(
                "UPDATE students SET balance = ? WHERE id = ?", (new_balance, self.id)
            )

            # Record payment
            cursor.execute(
                """
                INSERT INTO payments (student_id, amount, mock_mode)
                VALUES (?, ?, 1)
            """,
                (self.id, amount),
            )

            conn.commit()

            # Update instance attribute
            self.balance = new_balance

            return (
                True,
                f"Payment of ${amount:.2f} successful. New balance: ${new_balance:.2f}",
            )

        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error: {e}"
        finally:
            conn.close()

    def get_payment_history(self) -> list[dict]:
        """
        @brief Get payment history for this student.

        @return List of payment dictionaries with keys: amount, date, mock_mode
        """
        conn = sqlite3.connect("tuition.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT amount, payment_date, mock_mode
            FROM payments
            WHERE student_id = ?
            ORDER BY payment_date DESC
        """,
            (self.id,),
        )

        rows = cursor.fetchall()
        conn.close()

        payments = []
        for row in rows:
            payments.append(
                {
                    "amount": row["amount"],
                    "amount_formatted": f"${row['amount']:.2f}",
                    "date": row["payment_date"],
                    "mock_mode": row["mock_mode"],
                }
            )
        return payments

    def __repr__(self) -> str:
        """
        @brief String representation for debugging.

        Shows balance with exactly 2 decimal places.
        """
        return f"Student(student_id='{self.student_id}', name='{self.name}', balance=${self.balance:.2f})"


class FeeItem:
    """
    @class FeeItem
    @brief Represents a single fee line item for a semester.
    """

    def __init__(
        self,
        id: int,
        student_id: int,
        semester: str,
        description: str,
        amount: float,
        category: str,
    ):
        self.id = id
        self.student_id = student_id
        self.semester = semester
        self.description = description
        self.amount = amount
        self.category = category

    @staticmethod
    def get_statement(student_id: int, semester: str) -> list["FeeItem"]:
        """
        @brief Get all fee items for a student in a specific semester.

        @param student_id Internal student ID
        @param semester Semester name (e.g., "Spring 2026")
        @return List of FeeItem objects
        """
        conn = sqlite3.connect("tuition.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM fee_items
            WHERE student_id = ? AND semester = ?
            ORDER BY category, description
        """,
            (student_id, semester),
        )

        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            items.append(
                FeeItem(
                    id=row["id"],
                    student_id=row["student_id"],
                    semester=row["semester"],
                    description=row["description"],
                    amount=row["amount"],
                    category=row["category"],
                )
            )
        return items

    def get_formatted_amount(self) -> str:
        """Return amount formatted as currency."""
        return f"${self.amount:.2f}"

    def __repr__(self) -> str:
        return f"FeeItem(description='{self.description}', amount=${self.amount:.2f})"
