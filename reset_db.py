import os
import subprocess

# Delete existing database
if os.path.exists("tuition.db"):
    os.remove("tuition.db")
    print("✅ Old database deleted")

# Run initialization
subprocess.run(["python", "init_db.py"])
print("✅ Database reset complete!")
print("\nTest Logins:")
print("  Student 1: sh046186 / pass123")
print("  Student 2: sh089234 / pass123")
print("  Admin:     admin001 / admin123")
