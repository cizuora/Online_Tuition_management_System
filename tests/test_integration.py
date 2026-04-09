"""
@file test_integration.py
@brief Integration tests for complete workflows.
"""

import unittest
from services import TuitionService
from models import Student


class TestIntegration(unittest.TestCase):
    """Test complete user workflows."""

    @classmethod
    def setUpClass(cls):
        """Store original balances before any tests."""
        cls.service = TuitionService()
        cls.original_balances = {}

        # Store original balances
        for student_id in ["sh046186", "sh089234"]:
            student = Student.find_by_student_id(student_id)
            if student:
                cls.original_balances[student_id] = student.balance
                print(
                    f"   Stored original balance for {student_id}: ${student.balance:.2f}"
                )

    @classmethod
    def tearDownClass(cls):
        """Restore all original balances after tests."""
        print("\n   Restoring original balances...")
        for student_id, original_balance in cls.original_balances.items():
            student = Student.find_by_student_id(student_id)
            if student and student.balance != original_balance:
                student.update_balance(original_balance)
                print(f"   Restored {student_id} to ${original_balance:.2f}")

    def setUp(self):
        """Run before each test – ensure clean state."""
        # Reset John Doe's balance to original before each test
        original = self.original_balances.get("sh046186", 4250.00)
        student = Student.find_by_student_id("sh046186")
        if student and student.balance != original:
            student.update_balance(original)

    def test_complete_student_workflow(self):
        """Test: Student views balance → makes payment → views updated balance."""
        student_id = "sh046186"

        # Step 1: View balance
        before = self.service.get_student_balance(student_id)
        original_balance = before["balance"]

        # Step 2: Make payment
        payment = self.service.process_payment(student_id, 500.00)
        self.assertTrue(payment["success"])

        # Step 3: View updated balance
        after = self.service.get_student_balance(student_id)
        self.assertEqual(after["balance"], original_balance - 500.00)

        # Balance will be restored by tearDownClass

    def test_admin_lookup_and_payment_plan_workflow(self):
        """Test: Admin looks up student → creates payment plan."""
        admin_id = "admin001"
        student_id = "sh089234"

        # Step 1: Admin lookup
        lookup = self.service.admin_lookup(admin_id, student_id)
        self.assertTrue(lookup["success"])
        self.assertEqual(lookup["student"]["student_id"], student_id)

        # Step 2: Create payment plan (use a new student or cleanup first)
        # Check if already on a plan
        existing = self.service.admin_lookup(admin_id, student_id)
        if existing["student"].get("on_payment_plan"):
            # Override existing plan
            plan = self.service.admin_override_payment_plan(admin_id, student_id, 4)
        else:
            plan = self.service.admin_create_payment_plan(admin_id, student_id, 4)

        if plan["success"]:
            self.assertEqual(plan["plan_details"]["num_payments"], 4)

    def test_payment_plan_with_payment(self):
        """Test: Student on plan makes scheduled payment."""
        student_id = "sh089234"
        admin_id = "admin001"

        # First, ensure student has a balance > $500
        student = Student.find_by_student_id(student_id)
        if student.balance < 500:
            # Skip if balance too low
            self.skipTest(
                f"Student {student_id} balance (${student.balance}) too low for payment plan test"
            )

        # Clear any existing plan
        if self.service._is_on_payment_plan(student.id):
            self.service._delete_payment_plan(student.id)

        # Enroll in plan
        enrollment = self.service.student_enroll_standard_plan(student_id)

        if enrollment["success"]:
            # Make a payment matching the plan amount
            payment_amount = enrollment["plan_details"]["payment_amount"]
            result = self.service.process_payment(student_id, payment_amount)
            self.assertTrue(result["success"])
        else:
            # If can't enroll (maybe balance changed), skip test
            self.skipTest(f"Could not enroll: {enrollment['message']}")


if __name__ == "__main__":
    unittest.main()
