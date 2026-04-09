Great! Let me show you how to run and test each Python file individually. This is perfect for your teammates to understand and test each component.

---

## How to Run and Test Each Python File

### 1. Testing `init_db.py`

**What it does:** Creates database and inserts sample data

**How to run:**
```bash
python init_db.py



**To verify database was created:**
terminal 
# Check if file exists
dir tuition.db


## Prerequisites
```bash
pip install -r requirements.txt for flask
python init_db.py
```

#
### 1. Test Database Setup
```bash
python init_db.py
```

### 2. Test Models (Data Layer)
```bash
python test_models.py
```

### 3. Test Services (Business Logic)
```bash
python test_services.py
```


## Troubleshooting

### Error: "no such table: students"
**Fix:** Run `python init_db.py`

### Error: "ModuleNotFoundError: No module named 'flask'"
**Fix:** Run `pip install -r requirements.txt`


## Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| models.py | Find student, update balance, make payment | ✅ |
| services.py | Balance, statements, payments, payment plans | ✅ |
| integration.py | Complete workflows | ✅ |

