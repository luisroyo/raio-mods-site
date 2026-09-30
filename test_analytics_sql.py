import os
from dotenv import load_dotenv
load_dotenv()
from database.models import get_db_connection
from database.connection import init_db

init_db()
conn = get_db_connection()

print("Connection successful")
try:
    print("Testing basic query...")
    # Pega ultimas 500 visitas
    visits = conn.execute('''
        SELECT * FROM visits 
        ORDER BY created_at DESC 
        LIMIT 10
    ''').fetchall()
    print("Basic visits query success", len(visits))

    print("Testing daily views query...")
    # Sumariza pageviews por dia (ultimos 30 dias)
    daily_views = conn.execute('''
        SELECT date(created_at) as day, count(*) as total, count(DISTINCT session_id) as unique_visits
        FROM visits
        WHERE created_at >= date('now', '-30 days')
        GROUP BY day
        ORDER BY day ASC
    ''').fetchall()
    print("Daily views query success")

    print("Testing top referrers...")
    top_referrers = conn.execute('''
        SELECT referrer, count(*) as total
        FROM visits
        WHERE referrer != '' AND referrer IS NOT NULL
        GROUP BY referrer
        ORDER BY total DESC
        LIMIT 10
    ''').fetchall()
    print("Top referrers success")

    print("Testing top pages...")
    top_pages = conn.execute('''
        SELECT path, count(*) as total
        FROM visits
        GROUP BY path
        ORDER BY total DESC
        LIMIT 10
    ''').fetchall()
    print("Top pages success")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    conn.close()
