from database.db_wrappers import get_db_connection
import sys

def migrate():
    try:
        with get_db_connection() as conn:
            # Add commission_percentage to coupons
            try:
                conn.execute("ALTER TABLE coupons ADD COLUMN commission_percentage REAL DEFAULT 0;")
                print("Added commission_percentage to coupons.")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                    print("Column commission_percentage already exists.")
                else:
                    print(f"Error adding column: {e}")

            # Create commissions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS commissions (
                    id SERIAL PRIMARY KEY,
                    seller_coupon TEXT NOT NULL,
                    order_id INTEGER,
                    manual_sale_id INTEGER,
                    sale_amount REAL NOT NULL,
                    commission_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP
                )
            ''')
            print("Created commissions table.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    migrate()
