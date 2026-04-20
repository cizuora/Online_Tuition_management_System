"""
@file app.py
@date 2026-04-08
@author Chidera Izuora and Murat Talum
@version 1.0

@brief Main Flask web application for Tuition Management System.

This module handles:
- User authentication (login/logout)
- Student dashboard (view balance, make payments)
- Admin dashboard (lookup students, create payment plans)
- API endpoints for dynamic data
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import stripe
import os
from dotenv import load_dotenv
from datetime import datetime
from models import Student
from services import TuitionService

# Load Stripe keys from stripe.env
load_dotenv("stripe.env")
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

print(
    f"✅ Stripe configured. Secret key loaded: {stripe.api_key[:15] if stripe.api_key else 'NOT FOUND'}..."
)

# Create Flask app
app = Flask(__name__)
app.secret_key = "your-secret-key-here-change-in-production"  # Required for sessions

# Initialize service
tuition_service = TuitionService()


# ========================================================================
# ROUTES
# ========================================================================


@app.route("/")
def home():
    """Home page – redirect to login."""
    if "student_id" in session:
        # Already logged in, redirect to appropriate dashboard
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle student/admin login."""
    error = None

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        # Find student by ID
        student = Student.find_by_student_id(student_id)

        if not student:
            error = "Invalid Student ID"
        else:
            # In production, use proper password verification with hashing
            # For demo, we compare with stored hash
            from init_db import hash_password

            expected_hash = hash_password(password)

            # For simplicity in demo, also allow plain text comparison
            # This is just for testing with sample data
            if (
                student.password_hash == expected_hash
                or password == "pass123"
                or password == "admin123"
            ):
                # Login successful
                session["student_id"] = student.student_id
                session["user_id"] = student.id
                session["name"] = student.name
                session["role"] = student.role

                if student.role == "admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else:
                error = "Invalid password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Log out user."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/student/dashboard")
def student_dashboard():
    """Student dashboard – view balance, make payments."""
    if "student_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    student_id = session["student_id"]

    # Get any payment message
    payment_message = session.pop("payment_message", None)

    # Get student data
    balance_info = tuition_service.get_student_balance(student_id)
    statement = tuition_service.generate_fee_statement(student_id)
    payment_history = tuition_service.get_payment_history(student_id)

    return render_template(
        "student_dashboard.html",
        student=balance_info,
        statement=statement,
        payment_history=payment_history,
        payment_message=payment_message,
        current_year=datetime.now().year,
    )


@app.route("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard – lookup students, manage payment plans."""
    if "student_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("student_dashboard"))

    return render_template(
        "admin_dashboard.html",
        admin_name=session.get("name"),
        current_year=datetime.now().year,
    )


@app.route("/api/balance", methods=["GET"])
def api_get_balance():
    """API endpoint to get student balance (for AJAX calls)."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    student_id = session["student_id"]
    balance_info = tuition_service.get_student_balance(student_id)

    if balance_info:
        return jsonify(balance_info)
    return jsonify({"error": "Student not found"}), 404


@app.route("/api/statement", methods=["GET"])
def api_get_statement():
    """API endpoint to get fee statement."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    student_id = session["student_id"]
    semester = request.args.get("semester")
    statement = tuition_service.generate_fee_statement(student_id, semester)

    if statement:
        return jsonify(statement)
    return jsonify({"error": "Statement not found"}), 404


@app.route("/api/pay", methods=["POST"])
def api_make_payment():
    """API endpoint to process a payment."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    amount = float(data.get("amount", 0))
    student_id = session["student_id"]

    result = tuition_service.process_payment(student_id, amount)
    return jsonify(result)


@app.route("/api/enroll-plan", methods=["POST"])
def api_enroll_plan():
    """API endpoint for student to enroll in standard payment plan."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    student_id = session["student_id"]
    result = tuition_service.student_enroll_standard_plan(student_id)
    return jsonify(result)


@app.route("/api/admin/lookup", methods=["GET"])
def api_admin_lookup():
    """API endpoint for admin to look up a student."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    target_id = request.args.get("student_id")
    if not target_id:
        return jsonify({"error": "Missing student_id parameter"}), 400

    result = tuition_service.admin_lookup(session["student_id"], target_id)
    return jsonify(result)


@app.route("/api/admin/create-plan", methods=["POST"])
def api_admin_create_plan():
    """API endpoint for admin to create custom payment plan."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    target_id = data.get("student_id")
    num_payments = int(data.get("num_payments", 4))
    custom_amount = data.get("custom_amount")

    if custom_amount:
        custom_amount = float(custom_amount)

    result = tuition_service.admin_create_payment_plan(
        session["student_id"], target_id, num_payments, custom_amount
    )
    return jsonify(result)


@app.route("/api/create-checkout", methods=["POST"])
def create_checkout():
    """Create Stripe Checkout session for payment."""
    if "student_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    try:
        data = request.get_json()
        amount = float(data.get("amount", 0))
        amount_cents = int(amount * 100)

        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

        student_id = session.get("student_id")
        student = Student.find_by_student_id(student_id)

        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Store amount in session to use after payment
        session["pending_payment_amount"] = amount

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Tuition Payment",
                            "description": f"Payment for {student.name} - ID: {student_id}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:5000/payment-success?amount=" + str(amount),
            cancel_url="http://localhost:5000/payment-cancel",
            metadata={"student_id": student_id, "amount": amount},
        )

        return jsonify({"url": checkout_session.url})

    except Exception as e:
        print(f"Stripe error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/debug-data")
def debug_data():
    from services import TuitionService

    service = TuitionService()

    student_id = "sh046186"
    balance = service.get_student_balance(student_id)
    statement = service.generate_fee_statement(student_id)

    return {
        "balance_exists": balance is not None,
        "statement_exists": statement is not None,
        "statement_keys": list(statement.keys()) if statement else [],
        "items_type": str(type(statement.get("items"))) if statement else "N/A",
        "items_length": (
            len(statement.get("items")) if statement and statement.get("items") else 0
        ),
        "first_item": (
            statement.get("items")[0] if statement and statement.get("items") else None
        ),
    }


@app.route("/payment-success")
def payment_success():
    """Handle successful payment and update balance."""
    # Get amount from URL parameter
    amount = request.args.get("amount", type=float)
    student_id = session.get("student_id")

    if student_id and amount:
        # Process the payment
        result = tuition_service.process_payment(student_id, amount)
        print(f"Payment processed: {result}")

        if result.get("success"):
            # Store success message for dashboard
            session["payment_message"] = f"Payment of ${amount:.2f} was successful!"

    return render_template("success.html")


@app.route("/payment-cancel")
def payment_cancel():
    return render_template("cancel.html")


# ERROR HANDLERS


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


# MAIN ENTRY POINT


if __name__ == "__main__":
    print("=" * 50)
    print("Tuition Management System")
    print("=" * 50)
    print("Starting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("\nTest Logins:")
    print("  Student 1: sh046186 / pass123")
    print("  Student 2: sh089234 / pass123")
    print("  Admin:     admin001 / admin123")
    print("=" * 50)

    app.run(debug=True, host="0.0.0.0", port=5000)
