# Online_Tuition_management_System

 app.py # MAIN APPLICATION FILE
 # Contains Flask routes (URL handlers)
 # This is the "controller" - decides what to show for each URL
 # Example: /login, /dashboard, /api/balance
 models.py # DATABASE MODELS & DATA STRUCTURES
 # Defines what a "Student" or "FeeStatement" looks like
 # Contains ALL database queries (SELECT, INSERT, UPDATE)
 # This is the "Data Access Layer"

 services.py # BUSINESS LOGIC (The "brain" of the app)
 # Contains algorithms for:
 # - Calculating fees
 # - Processing payments
 # - Generating statements
 # Does NOT talk directly to database (uses models.py)

 utils.py # HELPER FUNCTIONS (will create later)
 # Password hashing, email validation, date formatting
 # Reusable utilities used across the app

 init_db.py # DATABASE SETUP SCRIPT
 # Run ONCE to create tables and insert sample students
 # Creates tuition.db file with:
 # - 2 sample students (John, Jane)
 # - 1 admin user
 # - Fee items for Spring 2026 semester

 requirements.txt # PYTHON DEPENDENCIES LIST
 # Run pip install -r requirements.txt to install:
 # - flask
 # - sqlite3 (built-in, no install needed)

 tuition.db # SQLITE DATABASE FILE (auto-created)
 # Stores all actual data (students, fees, payments)
 # DO NOT commit this to GitHub (add to .gitignore)

 static/ # STATIC FILES (served directly to browser)
  css/
 style.css # All styling rules (colors, layout, fonts)
  js/
  dashboard.js # Client-side JavaScript (runs in browser)
 # Handles: form validation, dynamic updates, API calls

 templates/ # HTML TEMPLATES (Flask renders these)
 login.html # Login page form
 student_dashboard.html # Student view (balance, pay button)
 admin_dashboard.html # Admin view (lookup by ID, payment plans)

 README.md # THIS FILE - explains the project