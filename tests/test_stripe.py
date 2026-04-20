"""
Test Stripe configuration and environment variables.
Run in VSCode Test Explorer or with: python -m unittest tests.test_stripe
"""

import unittest
import os
import subprocess


class TestStripeConfig(unittest.TestCase):
    """Test Stripe environment configuration."""

    def test_stripe_env_file_exists(self):
        """Test that stripe.env file exists."""
        env_file = "stripe.env"
        self.assertTrue(
            os.path.exists(env_file),
            f"{env_file} file not found. Please create it with your Stripe keys.",
        )
        print(f"✅ stripe.env file exists")

    def test_stripe_env_has_secret_key(self):
        """Test that stripe.env contains STRIPE_SECRET_KEY."""
        env_file = "stripe.env"
        if not os.path.exists(env_file):
            self.skipTest("stripe.env not found")

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("STRIPE_SECRET_KEY=", content)
        self.assertNotIn("your_actual_secret_key_here", content.lower())
        print(f"✅ STRIPE_SECRET_KEY found in stripe.env")

    def test_stripe_env_has_publishable_key(self):
        """Test that stripe.env contains STRIPE_PUBLISHABLE_KEY."""
        env_file = "stripe.env"
        if not os.path.exists(env_file):
            self.skipTest("stripe.env not found")

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("STRIPE_PUBLISHABLE_KEY=", content)
        self.assertNotIn("your_actual_publishable_key_here", content.lower())
        print(f"✅ STRIPE_PUBLISHABLE_KEY found in stripe.env")

    def test_keys_are_not_placeholders(self):
        """Test that actual keys (not placeholders) are in stripe.env."""
        env_file = "stripe.env"
        if not os.path.exists(env_file):
            self.skipTest("stripe.env not found")

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        secret_line = [
            line for line in content.split("\n") if "STRIPE_SECRET_KEY=" in line
        ]
        publishable_line = [
            line for line in content.split("\n") if "STRIPE_PUBLISHABLE_KEY=" in line
        ]

        if secret_line:
            secret_key = secret_line[0].split("=")[1].strip()
            self.assertTrue(
                secret_key.startswith("sk_test_"),
                f"Secret key should start with 'sk_test_', got {secret_key[:15]}...",
            )
            print(f"✅ Secret key format valid (starts with sk_test_)")

        if publishable_line:
            pub_key = publishable_line[0].split("=")[1].strip()
            self.assertTrue(
                pub_key.startswith("pk_test_"),
                f"Publishable key should start with 'pk_test_', got {pub_key[:15]}...",
            )
            print(f"✅ Publishable key format valid (starts with pk_test_)")


class TestGitIgnore(unittest.TestCase):
    """Test that stripe.env is properly ignored by Git."""

    def test_gitignore_contains_stripe_env(self):
        """Test that .gitignore includes stripe.env."""
        gitignore_file = ".gitignore"

        if not os.path.exists(gitignore_file):
            self.skipTest(f"{gitignore_file} not found")

        with open(gitignore_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("stripe.env", content)
        print(f"✅ .gitignore contains 'stripe.env'")

    def test_gitignore_contains_env_pattern(self):
        """Test that .gitignore includes *.env pattern."""
        gitignore_file = ".gitignore"

        if not os.path.exists(gitignore_file):
            self.skipTest(f"{gitignore_file} not found")

        with open(gitignore_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("*.env", content)
        print(f"✅ .gitignore contains '*.env' pattern")

    def test_stripe_env_not_tracked_by_git(self):
        """Test that stripe.env is not already tracked by Git."""
        result = subprocess.run(
            ["git", "ls-files", "stripe.env"], capture_output=True, text=True
        )

        is_tracked = bool(result.stdout.strip())

        self.assertFalse(
            is_tracked,
            "stripe.env is tracked by Git! Remove it with: git rm --cached stripe.env",
        )

        if not is_tracked:
            print(f"✅ stripe.env is NOT tracked by Git (good - your secret is safe)")


class TestAppStripeRoutes(unittest.TestCase):
    """Test that app.py has Stripe routes configured."""

    def test_app_has_stripe_import(self):
        """Test that app.py imports stripe."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("import stripe", content)
        print(f"✅ app.py imports stripe")

    def test_app_has_checkout_route(self):
        """Test that app.py has /api/create-checkout route."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("/api/create-checkout", content)
        print(f"✅ /api/create-checkout route found")

    def test_app_has_success_route(self):
        """Test that app.py has /payment-success route."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("/payment-success", content)
        print(f"✅ /payment-success route found")

    def test_app_has_cancel_route(self):
        """Test that app.py has /payment-cancel route."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("/payment-cancel", content)
        print(f"✅ /payment-cancel route found")

    def test_app_loads_stripe_env(self):
        """Test that app.py loads stripe.env."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("load_dotenv", content)
        self.assertIn("stripe.env", content)
        print(f"✅ app.py loads stripe.env")


class TestStudentDashboard(unittest.TestCase):
    """Test that student_dashboard.html has Stripe button."""

    def test_dashboard_has_stripe_button(self):
        """Test that student_dashboard.html has Stripe payment button."""
        template_file = "templates/student_dashboard.html"

        self.assertTrue(os.path.exists(template_file), f"{template_file} not found")

        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("makeStripePayment", content)
        self.assertIn("/api/create-checkout", content)
        print(f"✅ student_dashboard.html has Stripe payment button")

    def test_dashboard_has_both_buttons(self):
        """Test that dashboard has both Mock Pay and Stripe buttons."""
        template_file = "templates/student_dashboard.html"

        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("makeMockPayment", content)
        self.assertIn("makeStripePayment", content)
        self.assertIn("Mock Pay", content)
        self.assertIn("Pay with Stripe", content)
        print(f"✅ Dashboard has both Mock Pay and Stripe buttons")


class TestSuccessCancelPages(unittest.TestCase):
    """Test that success.html and cancel.html exist and have correct content."""

    def test_success_page_exists(self):
        """Test that success.html exists."""
        template_file = "templates/success.html"
        self.assertTrue(os.path.exists(template_file), f"{template_file} not found")
        print(f"✅ success.html exists")

    def test_cancel_page_exists(self):
        """Test that cancel.html exists."""
        template_file = "templates/cancel.html"
        self.assertTrue(os.path.exists(template_file), f"{template_file} not found")
        print(f"✅ cancel.html exists")

    def test_success_page_has_success_message(self):
        """Test that success.html shows success message."""
        template_file = "templates/success.html"
        if not os.path.exists(template_file):
            self.skipTest("success.html not found")

        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Successful", content)
        self.assertIn("dashboard", content.lower())
        print(f"✅ success.html has correct content")

    def test_cancel_page_has_cancel_message(self):
        """Test that cancel.html shows cancel message."""
        template_file = "templates/cancel.html"
        if not os.path.exists(template_file):
            self.skipTest("cancel.html not found")

        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Cancelled", content)
        self.assertIn("dashboard", content.lower())
        print(f"✅ cancel.html has correct content")


if __name__ == "__main__":
    unittest.main()
