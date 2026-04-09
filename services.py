"""
@file services.py
@date 2026-04-08
@author Chidera Izuora and Murat Talum
@version 1.1

@brief Business logic layer for Tuition Management System.

This module contains all the "brain" of the application including:
- Balance calculations
- Fee statement generation
- Late fee policies
- Payment validation
- Student self-enrollment in standard payment plan
- Admin creation of custom payment plans
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from models import Student, FeeItem


class TuitionService:
    """
    @class TuitionService
    @brief Main service class for tuition management business logic.

    This class handles:
    - Student balance operations
    - Fee statement generation
    - Late fee calculations
    - Payment processing rules
    - Payment plan enrollment (student and admin)
    """

    def __init__(self):
        """
        @brief Initialize the Tuition Service.

        Sets up configuration like late fee percentage and payment deadlines.
        """
        self.late_fee_percentage = 0.05  # 5% late fee
        self.grace_period_days = 30  # Days after semester start before late fee
        self._active_plans = (
            {}
        )  # Simulate database for payment plans {student_id: plan_details}

    def get_student_balance(self, student_id: str) -> Optional[Dict]:
        """
        @brief Get current balance for a student with formatted output.

        @param student_id Public student ID (e.g., "sh046186")
        @return Dictionary with balance info or None if student not found

        @note This is the main method for the "View Balance" feature.
        """
        student = Student.find_by_student_id(student_id)

        if not student:
            return None

        # Check if student is on a payment plan
        on_plan = self._is_on_payment_plan(student.id)
        plan_details = self._get_payment_plan(student.id) if on_plan else None

        return {
            "student_id": student.student_id,
            "name": student.name,
            "balance": student.balance,
            "balance_formatted": f"${student.balance:,.2f}",
            "has_balance_due": student.balance > 0,
            "role": student.role,
            "on_payment_plan": on_plan,
            "payment_plan": plan_details,
        }

    def generate_fee_statement(
        self, student_id: str, semester: str = None
    ) -> Optional[Dict]:
        """
        @brief Generate a detailed fee statement for a student.

        @param student_id Public student ID (e.g., "sh046186")
        @param semester Semester name (defaults to current semester)
        @return Dictionary with complete statement or None if student not found

        This method:
        1. Finds the student
        2. Gets all fee items for the semester
        3. Calculates subtotals by category
        4. Applies any late fees if applicable
        5. Returns formatted statement
        """
        # Find the student
        student = Student.find_by_student_id(student_id)
        if not student:
            return None

        # Determine semester if not provided
        if not semester:
            semester = self._get_current_semester()

        # Get fee items from database
        fee_items = FeeItem.get_statement(student.id, semester)

        if not fee_items:
            return {
                "student_id": student.student_id,
                "name": student.name,
                "semester": semester,
                "items": [],
                "subtotal": 0.0,
                "late_fee": 0.0,
                "total_due": student.balance,
                "message": f"No fee items found for {semester}",
            }

        # Calculate subtotal by category
        categories = {}
        subtotal = 0.0

        for item in fee_items:
            subtotal += item.amount

            if item.category not in categories:
                categories[item.category] = 0.0
            categories[item.category] += item.amount

        # Check for late fee
        late_fee = self._calculate_late_fee(student, semester, subtotal)

        # Calculate total due
        total_due = student.balance

        # Format items for display
        formatted_items = []
        for item in fee_items:
            formatted_items.append(
                {
                    "description": item.description,
                    "amount": item.amount,
                    "amount_formatted": f"${item.amount:,.2f}",
                    "category": item.category,
                }
            )

        return {
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "semester": semester,
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": formatted_items,
            "categories": categories,
            "subtotal": subtotal,
            "subtotal_formatted": f"${subtotal:,.2f}",
            "late_fee": late_fee,
            "late_fee_formatted": f"${late_fee:,.2f}" if late_fee > 0 else None,
            "current_balance": student.balance,
            "current_balance_formatted": f"${student.balance:,.2f}",
            "total_due": total_due,
            "total_due_formatted": f"${total_due:,.2f}",
            "is_overdue": self._is_payment_overdue(semester),
            "payment_deadline": self._get_payment_deadline(semester),
        }

    def process_payment(self, student_id: str, amount: float) -> Dict:
        """
        @brief Process a tuition payment.

        @param student_id Public student ID
        @param amount Payment amount
        @return Dictionary with payment result

        This method:
        1. Validates the amount
        2. Checks if student exists
        3. Processes the payment
        4. Returns result with new balance
        """
        # Find the student
        student = Student.find_by_student_id(student_id)

        if not student:
            return {"success": False, "message": f"Student {student_id} not found"}

        # Validate amount
        if amount <= 0:
            return {
                "success": False,
                "message": "Payment amount must be greater than zero",
                "current_balance": student.balance,
                "current_balance_formatted": f"${student.balance:,.2f}",
            }

        # Round to 2 decimal places
        amount = round(amount, 2)

        # Check if amount exceeds balance
        if amount > student.balance:
            return {
                "success": False,
                "message": f"Payment amount (${amount:.2f}) exceeds current balance (${student.balance:.2f})",
                "current_balance": student.balance,
                "current_balance_formatted": f"${student.balance:,.2f}",
                "suggested_amount": student.balance,
            }

        # Process the payment using the student model
        success, message = student.make_payment(amount)

        if success:
            # If student was on a payment plan, check if plan is complete
            if self._is_on_payment_plan(student.id) and student.balance == 0:
                self._complete_payment_plan(student.id)

            return {
                "success": True,
                "message": message,
                "student_id": student.student_id,
                "name": student.name,
                "amount_paid": amount,
                "amount_paid_formatted": f"${amount:,.2f}",
                "new_balance": student.balance,
                "new_balance_formatted": f"${student.balance:,.2f}",
                "fully_paid": student.balance == 0,
            }
        else:
            return {
                "success": False,
                "message": message,
                "current_balance": student.balance,
                "current_balance_formatted": f"${student.balance:,.2f}",
            }

    def get_payment_history(self, student_id: str) -> Optional[Dict]:
        """
        @brief Get payment history for a student.

        @param student_id Public student ID
        @return Dictionary with payment history or None if student not found
        """
        student = Student.find_by_student_id(student_id)

        if not student:
            return None

        payments = student.get_payment_history()

        # Calculate total paid
        total_paid = sum(p["amount"] for p in payments)

        return {
            "student_id": student.student_id,
            "name": student.name,
            "current_balance": student.balance,
            "current_balance_formatted": f"${student.balance:,.2f}",
            "total_paid": total_paid,
            "total_paid_formatted": f"${total_paid:,.2f}",
            "payment_count": len(payments),
            "payments": payments,
        }

    # PAYMENT PLAN METHODS
    def student_enroll_standard_plan(self, student_id: str) -> Dict:
        """
        @brief Student self-enrolls in the standard payment plan.

        @param student_id Public student ID
        @return Dictionary with enrollment result

        Business rules:
        - Standard plan: 4 monthly payments
        - Balance must be > $500 to qualify
        - Student cannot already be on a plan

        This method is called from the STUDENT dashboard.
        """
        # Find the student
        student = Student.find_by_student_id(student_id)

        if not student:
            return {"success": False, "message": f"Student {student_id} not found"}

        # Check eligibility
        if not self._can_enroll_payment_plan(student):
            return {
                "success": False,
                "message": "You are not eligible for a payment plan. Balance must be over $500.",
                "current_balance": student.balance,
                "current_balance_formatted": f"${student.balance:,.2f}",
                "minimum_required": "$500.00",
            }

        # Check if already on a plan
        if self._is_on_payment_plan(student.id):
            return {
                "success": False,
                "message": "You are already enrolled in a payment plan.",
                "current_balance": student.balance,
                "current_balance_formatted": f"${student.balance:,.2f}",
            }

        # Calculate standard plan (4 monthly payments)
        num_payments = 4
        payment_amount = round(student.balance / num_payments, 2)

        # Save the payment plan
        plan_id = self._save_payment_plan(
            student.id, "standard", num_payments, payment_amount
        )

        # Generate payment schedule
        schedule = self._generate_payment_schedule(num_payments, payment_amount)

        return {
            "success": True,
            "message": f"You have been enrolled in the Standard Payment Plan.",
            "plan_details": {
                "plan_id": plan_id,
                "plan_type": "standard",
                "total_balance": student.balance,
                "total_balance_formatted": f"${student.balance:,.2f}",
                "num_payments": num_payments,
                "payment_amount": payment_amount,
                "payment_amount_formatted": f"${payment_amount:,.2f}",
                "first_payment_due": (
                    schedule[0]["due_date"] if schedule else "30 days from now"
                ),
                "payment_schedule": schedule,
            },
        }

    def admin_create_payment_plan(
        self,
        admin_student_id: str,
        target_student_id: str,
        num_payments: int,
        custom_amount: float = None,
    ) -> Dict:
        """
        @brief Admin creates a custom payment plan for a specific student.

        @param admin_student_id Admin's student ID (must have role='admin')
        @param target_student_id Student ID to create plan for
        @param num_payments Number of payments (e.g., 3, 4, 6, 12)
        @param custom_amount Optional custom payment amount (if None, split equally)
        @return Dictionary with enrollment result

        Business rules:
        - Admin can set ANY number of payments (1-24)
        - Admin can set custom payment amounts or auto-calculate
        - Admin can override eligibility requirements
        - Must have admin privileges

        This method is called from the ADMIN dashboard.
        """
        # Verify admin exists and has admin role
        admin = Student.find_by_student_id(admin_student_id)

        if not admin or admin.role != "admin":
            return {
                "success": False,
                "message": "Unauthorized: Admin privileges required",
            }

        # Find target student
        target = Student.find_by_student_id(target_student_id)

        if not target:
            return {
                "success": False,
                "message": f"Student {target_student_id} not found",
            }

        # Validate number of payments
        if num_payments < 1 or num_payments > 24:
            return {
                "success": False,
                "message": "Number of payments must be between 1 and 24",
            }

        # Calculate payment amount
        if custom_amount:
            # Admin specified a custom amount
            payment_amount = round(custom_amount, 2)
            # Verify total payments cover the balance
            total_payments = payment_amount * num_payments
            if total_payments < target.balance:
                return {
                    "success": False,
                    "message": f"Custom payment amount ${payment_amount:.2f} over {num_payments} payments totals ${total_payments:.2f}, but balance is ${target.balance:.2f}",
                    "suggestion": f"Try ${round(target.balance / num_payments, 2):.2f} per payment",
                }
        else:
            # Auto-calculate equal payments
            payment_amount = round(target.balance / num_payments, 2)

        # Check if already on a plan
        if self._is_on_payment_plan(target.id):
            # Admin can override existing plan
            return {
                "success": False,
                "message": f"Student {target_student_id} is already on a payment plan. Use admin_override_payment_plan() to override.",
                "requires_override": True,
                "current_plan": self._get_payment_plan(target.id),
            }

        # Create the custom plan
        plan_id = self._save_payment_plan(
            target.id, "custom", num_payments, payment_amount
        )

        # Generate schedule
        schedule = self._generate_payment_schedule(num_payments, payment_amount)

        return {
            "success": True,
            "message": f"Custom payment plan created for {target.name}",
            "admin_notes": {
                "created_by": admin.name,
                "created_by_id": admin.student_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "plan_details": {
                "plan_id": plan_id,
                "plan_type": "custom",
                "student_id": target.student_id,
                "student_name": target.name,
                "student_email": target.email,
                "total_balance": target.balance,
                "total_balance_formatted": f"${target.balance:,.2f}",
                "num_payments": num_payments,
                "payment_amount": payment_amount,
                "payment_amount_formatted": f"${payment_amount:,.2f}",
                "payment_schedule": schedule,
                "total_to_pay": payment_amount * num_payments,
                "total_to_pay_formatted": f"${payment_amount * num_payments:,.2f}",
            },
        }

    def admin_override_payment_plan(
        self,
        admin_student_id: str,
        target_student_id: str,
        num_payments: int,
        custom_amount: float = None,
    ) -> Dict:
        """
        @brief Admin overrides an existing payment plan.

        @param admin_student_id Admin's student ID
        @param target_student_id Student to override plan for
        @param num_payments New number of payments
        @param custom_amount Optional custom payment amount
        @return Dictionary with override result

        This removes the existing plan and creates a new one.
        """
        # Verify admin
        admin = Student.find_by_student_id(admin_student_id)

        if not admin or admin.role != "admin":
            return {
                "success": False,
                "message": "Unauthorized: Admin privileges required",
            }

        # Find target student
        target = Student.find_by_student_id(target_student_id)

        if not target:
            return {
                "success": False,
                "message": f"Student {target_student_id} not found",
            }

        # Delete existing plan
        self._delete_payment_plan(target.id)

        # Create new plan
        return self.admin_create_payment_plan(
            admin_student_id, target_student_id, num_payments, custom_amount
        )

    def admin_lookup(
        self, admin_student_id: str, target_student_id: str
    ) -> Optional[Dict]:
        """
        @brief Admin lookup of another student's account.

        @param admin_student_id Admin's student ID (must have role='admin')
        @param target_student_id Student ID to look up
        @return Dictionary with student details or None if unauthorized/not found

        @note This implements the "Admin Lookup" feature requirement
        """
        # Verify admin exists and has admin role
        admin = Student.find_by_student_id(admin_student_id)

        if not admin or admin.role != "admin":
            return {
                "success": False,
                "message": "Unauthorized: Admin privileges required",
            }

        # Find target student
        target = Student.find_by_student_id(target_student_id)

        if not target:
            return {
                "success": False,
                "message": f"Student {target_student_id} not found",
            }

        # Get payment history for target
        payments = target.get_payment_history()
        total_paid = sum(p["amount"] for p in payments)

        # Get current semester statement
        current_semester = self._get_current_semester()
        fee_items = FeeItem.get_statement(target.id, current_semester)
        semester_total = sum(item.amount for item in fee_items)

        # Check if on payment plan
        on_plan = self._is_on_payment_plan(target.id)
        plan_details = self._get_payment_plan(target.id) if on_plan else None

        return {
            "success": True,
            "student": {
                "student_id": target.student_id,
                "name": target.name,
                "email": target.email,
                "balance": target.balance,
                "balance_formatted": f"${target.balance:,.2f}",
                "role": target.role,
                "on_payment_plan": on_plan,
                "payment_plan": plan_details,
            },
            "payment_history": {
                "count": len(payments),
                "total_paid": total_paid,
                "total_paid_formatted": f"${total_paid:,.2f}",
                "recent_payments": payments[:5],  # Last 5 payments
            },
            "current_semester": {
                "name": current_semester,
                "total_fees": semester_total,
                "total_fees_formatted": f"${semester_total:,.2f}",
            },
            "can_enroll_payment_plan": self._can_enroll_payment_plan(target)
            and not on_plan,
        }

    # PRIVATE HELPER METHODS
    def _get_current_semester(self) -> str:
        """
        @brief Determine current semester based on date.

        @return String like "Spring 2026", "Summer 2026", or "Fall 2026"
        """
        now = datetime.now()
        year = now.year

        if now.month <= 5:
            return f"Spring {year}"
        elif now.month <= 8:
            return f"Summer {year}"
        else:
            return f"Fall {year}"

    def _get_semester_start_date(self, semester: str) -> datetime:
        """
        @brief Get the start date of a semester.
        """
        try:
            season, year = semester.split()
            year = int(year)

            if season == "Spring":
                return datetime(year, 1, 15)
            elif season == "Summer":
                return datetime(year, 6, 1)
            else:  # Fall
                return datetime(year, 9, 1)
        except:
            return datetime.now()

    def _get_payment_deadline(self, semester: str) -> str:
        """Get the payment deadline for a semester."""
        start_date = self._get_semester_start_date(semester)
        deadline = start_date + timedelta(days=self.grace_period_days)
        return deadline.strftime("%B %d, %Y")

    def _is_payment_overdue(self, semester: str) -> bool:
        """Check if payment deadline has passed."""
        start_date = self._get_semester_start_date(semester)
        deadline = start_date + timedelta(days=self.grace_period_days)
        return datetime.now() > deadline

    def _calculate_late_fee(
        self, student: Student, semester: str, subtotal: float
    ) -> float:
        """Calculate late fee if applicable."""
        if self._is_payment_overdue(semester) and student.balance > 0:
            late_fee = round(student.balance * self.late_fee_percentage, 2)
            return late_fee
        return 0.0

    # PAYMENT PLAN HELPER METHODS (Simulated Database)
    def _can_enroll_payment_plan(self, student: Student) -> bool:
        """
        @brief Check if student is eligible for a payment plan.

        Business rule: Balance must be > $500
        """
        return student.balance > 500.00

    def _is_on_payment_plan(self, student_id: int) -> bool:
        """Check if student is already on a payment plan."""
        return student_id in self._active_plans

    def _get_payment_plan(self, student_id: int) -> Optional[Dict]:
        """Get active payment plan for a student."""
        return self._active_plans.get(student_id)

    def _save_payment_plan(
        self, student_id: int, plan_type: str, num_payments: int, payment_amount: float
    ) -> int:
        """Save a payment plan to the simulated database."""
        plan_id = len(self._active_plans) + 1000

        self._active_plans[student_id] = {
            "plan_id": plan_id,
            "plan_type": plan_type,
            "num_payments": num_payments,
            "payment_amount": payment_amount,
            "remaining_payments": num_payments,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": True,
        }

        return plan_id

    def _delete_payment_plan(self, student_id: int) -> bool:
        """Delete an existing payment plan."""
        if student_id in self._active_plans:
            del self._active_plans[student_id]
            return True
        return False

    def _complete_payment_plan(self, student_id: int) -> bool:
        """Mark a payment plan as complete when balance reaches zero."""
        if student_id in self._active_plans:
            self._active_plans[student_id]["is_active"] = False
            self._active_plans[student_id]["completed_at"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            return True
        return False

    def _generate_payment_schedule(
        self, num_payments: int, payment_amount: float
    ) -> List[Dict]:
        """Generate a schedule of payment due dates."""
        schedule = []
        current_date = datetime.now() + timedelta(
            days=30
        )  # First payment due in 30 days

        for i in range(num_payments):
            due_date = current_date + timedelta(days=i * 30)
            schedule.append(
                {
                    "payment_number": i + 1,
                    "due_date": due_date.strftime("%B %d, %Y"),
                    "amount": payment_amount,
                    "amount_formatted": f"${payment_amount:,.2f}",
                    "status": "pending",
                }
            )

        return schedule


# STANDALONE TESTING
if __name__ == "__main__":
    """
    @brief Test the TuitionService functionality.
    """
    print("=" * 70)
    print("Testing TuitionService with Payment Plan Features")
    print("=" * 70)

    # Create service instance
    service = TuitionService()

    # Test 1: Get student balance
    print("\n1. Testing get_student_balance()...")
    balance_info = service.get_student_balance("sh046186")
    if balance_info:
        print(f"   ✓ Student: {balance_info['name']}")
        print(f"   ✓ Balance: {balance_info['balance_formatted']}")
        print(f"   ✓ On payment plan: {balance_info['on_payment_plan']}")

    # Test 2: Generate fee statement
    print("\n2. Testing generate_fee_statement()...")
    statement = service.generate_fee_statement("sh046186")
    if statement:
        print(f"   ✓ Semester: {statement['semester']}")
        print(f"   ✓ Subtotal: {statement['subtotal_formatted']}")
        print(f"   ✓ Current Balance: {statement['current_balance_formatted']}")
        print(f"   ✓ Items: {len(statement['items'])} fee items")

    # Test 3: Student self-enroll in standard plan
    print("\n3. Testing student_enroll_standard_plan()...")
    enrollment = service.student_enroll_standard_plan(
        "sh089234"
    )  # Jane Smith with $1250 balance
    if enrollment["success"]:
        print(f"   ✓ {enrollment['message']}")
        print(
            f"   ✓ Plan: {enrollment['plan_details']['num_payments']} payments of {enrollment['plan_details']['payment_amount_formatted']}"
        )
    else:
        print(f"   ✗ {enrollment['message']}")

    # Test 4: Admin creates custom payment plan
    print("\n4. Testing admin_create_payment_plan()...")
    custom_plan = service.admin_create_payment_plan("admin001", "sh089234", 6, None)
    if custom_plan["success"]:
        print(f"   ✓ {custom_plan['message']}")
        print(
            f"   ✓ Custom plan: {custom_plan['plan_details']['num_payments']} payments of {custom_plan['plan_details']['payment_amount_formatted']}"
        )
    else:
        print(f"   ✗ {custom_plan['message']}")

    # Test 5: Process payment
    print("\n5. Testing process_payment()...")
    payment_result = service.process_payment("sh046186", 500.00)
    if payment_result["success"]:
        print(f"   ✓ {payment_result['message']}")
    else:
        print(f"   ✗ {payment_result['message']}")

    # Test 6: Admin lookup with payment plan info
    print("\n6. Testing admin_lookup() with payment plan...")
    admin_lookup = service.admin_lookup("admin001", "sh089234")
    if admin_lookup["success"]:
        print(f"   ✓ Student: {admin_lookup['student']['name']}")
        print(f"   ✓ Balance: {admin_lookup['student']['balance_formatted']}")
        print(f"   ✓ On payment plan: {admin_lookup['student']['on_payment_plan']}")
        if admin_lookup["student"]["payment_plan"]:
            print(
                f"   ✓ Plan type: {admin_lookup['student']['payment_plan']['plan_type']}"
            )
            print(
                f"   ✓ Payments: {admin_lookup['student']['payment_plan']['num_payments']} of {admin_lookup['student']['payment_plan']['payment_amount']:.2f}"
            )

    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)
