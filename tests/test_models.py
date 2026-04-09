"""
@file test_models.py
@brief Unit tests for models.py
"""

import unittest
import os
import sqlite3
from models import Student, FeeItem


class TestStudentModel(unittest.TestCase):
    """Test cases for Student model."""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests – store original balances."""
        cls.original_balances = {}

        # Store original balances for students we'll modify
        for student_id in ["sh046186", "sh089234"]:
            student = Student.find_by_student_id(student_id)
            if student:
                cls.original_balances[student_id] = student.balance

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests – restore original balances."""
        for student_id, original_balance in cls.original_balances.items():
            student = Student.find_by_student_id(student_id)
            if student and student.balance != original_balance:
                student.update_balance(original_balance)
                print(f"   Restored {student_id} balance to ${original_balance:.2f}")

    def setUp(self):
        """Run before each test – ensure clean state."""
        # Restore John Doe's balance before each test
        student = Student.find_by_student_id("sh046186")
        if student and student.balance != 4250.00:
            student.update_balance(4250.00)

    def test_find_by_student_id(self):
        """Test finding student by student ID."""
        student = Student.find_by_student_id("sh046186")

        # Assertions
        self.assertIsNotNone(student)
        self.assertEqual(student.name, "John Doe")
        self.assertEqual(student.balance, 4250.00)  # Now this will pass
        self.assertEqual(student.student_id, "sh046186")

    def test_find_by_student_id_not_found(self):
        """Test searching for non-existent student."""
        student = Student.find_by_student_id("fake999")
        self.assertIsNone(student)

    def test_update_balance(self):
        """Test updating student balance."""
        student = Student.find_by_student_id("sh046186")
        original_balance = student.balance

        # Update balance
        result = student.update_balance(1000.00)

        # Verify
        self.assertTrue(result)
        self.assertEqual(student.balance, 1000.00)

        # Clean up – restore original balance
        student.update_balance(original_balance)

    def test_make_payment(self):
        """Test payment processing."""
        student = Student.find_by_student_id("sh089234")
        original_balance = student.balance

        # Make a payment
        success, message = student.make_payment(200.00)

        self.assertTrue(success)
        self.assertEqual(student.balance, original_balance - 200.00)

        # Clean up
        student.update_balance(original_balance)


class TestFeeItemModel(unittest.TestCase):
    """Test cases for FeeItem model."""

    def test_get_statement(self):
        """Test getting fee statement for a student."""
        student = Student.find_by_student_id("sh046186")
        items = FeeItem.get_statement(student.id, "Spring 2026")

        self.assertIsNotNone(items)
        self.assertGreater(len(items), 0)
        # FIXED: Don't assume first item is Tuition – check if any Tuition exists
        tuition_items = [item for item in items if item.category == "Tuition"]
        self.assertGreater(len(tuition_items), 0, "No tuition items found")
        self.assertEqual(tuition_items[0].description, "Tuition - 12 credits")

    def test_statement_total(self):
        """Test that statement totals match expected."""
        student = Student.find_by_student_id("sh046186")
        items = FeeItem.get_statement(student.id, "Spring 2026")

        # Calculate total
        total = sum(item.amount for item in items)

        # Expected total: 3600 + 350 + 150 + 150 = 4250
        self.assertEqual(total, 4250.00)
        print(f"   Statement total: ${total:.2f}")

    def test_statement_categories(self):
        """Test that fee items have correct categories."""
        student = Student.find_by_student_id("sh046186")
        items = FeeItem.get_statement(student.id, "Spring 2026")

        categories = set(item.category for item in items)

        # Should have both Tuition and Fees categories
        self.assertIn("Tuition", categories)
        self.assertIn("Fees", categories)
        print(f"   Categories found: {categories}")


if __name__ == "__main__":
    unittest.main()
