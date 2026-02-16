
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('radius.db' if 'database.db' not in __file__ else 'database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Mock connection since we are running standalone
def mock_db_connection():
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except:
        print("Could not connect to database.db")
        return None

conn = mock_db_connection()
if not conn:
    exit()

print("--- DEBUGGING SALES REPORT ---")

# 1. Check Orders
print("\n[ORDERS - Approved]")
orders = conn.execute("SELECT id, amount, status FROM orders WHERE status = 'approved'").fetchall()
for o in orders:
    print(dict(o))
print(f"Count: {len(orders)}")

# 2. Check Manual Sales
print("\n[MANUAL SALES]")
manual = conn.execute("SELECT id, total_price FROM manual_sales").fetchall()
for m in manual:
    print(dict(m))
print(f"Count: {len(manual)}")

# 3. Simulate Report Logic
print("\n[SIMULATION]")
try:
    # Online Revenue
    online_rev_row = conn.execute("SELECT SUM(CAST(REPLACE(REPLACE(amount, 'R$', ''), ',', '.') AS REAL)) as total FROM orders WHERE status = 'approved'").fetchone()
    online_rev = online_rev_row['total']
    print(f"Online Revenue (SQL): {online_rev}")

    # Manual Revenue
    manual_rev_row = conn.execute("SELECT SUM(total_price) as total FROM manual_sales").fetchone()
    manual_rev = manual_rev_row['total']
    print(f"Manual Revenue (SQL): {manual_rev}")

    # Counts
    online_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'approved'").fetchone()[0]
    manual_count = conn.execute("SELECT COUNT(*) FROM manual_sales").fetchone()[0]
    print(f"Online Count: {online_count}")
    print(f"Manual Count: {manual_count}")

except Exception as e:
    print(f"Error during simulation: {e}")

conn.close()
