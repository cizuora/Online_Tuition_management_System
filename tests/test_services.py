import unittest
from services import TuitionService


class TestTuitionService(unittest.TestCase):
    """Test cases for TuitionService."""

    @classmethod
    def setUpClass(cls):
        """Store original balances before tests."""
        from models import Student

        cls.service = TuitionService()
        cls.original_balances = {}

        for student_id in ["sh046186", "sh089234"]:
            student = Student.find_by_student_id(student_id)
            if student:
                cls.original_balances[student_id] = student.balance

    @classmethod
    def tearDownClass(cls):
        """Restore original balances after tests."""
        from models import Student

        print("\n   Restoring original balances...")
        for student_id, original_balance in cls.original_balances.items():
            student = Student.find_by_student_id(student_id)
            if student and student.balance != original_balance:
                student.update_balance(original_balance)

    def setUp(self):
        """Reset before each test."""
        from models import Student

        # Reset John Doe's balance
        original = self.original_balances.get("sh046186", 4250.00)
        student = Student.find_by_student_id("sh046186")
        if student and student.balance != original:
            student.update_balance(original)

        # Reset Jane Smith's balance
        original = self.original_balances.get("sh089234", 1250.00)
        student = Student.find_by_student_id("sh089234")
        if student and student.balance != original:
            student.update_balance(original)

