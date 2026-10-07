import sys
from app import app
from flask import session
from routes.admin.sales import sales_report

with app.test_request_context('/painel-mestre/sales/report?date_start=2026-09-01&date_end=2026-10-06'):
    session['admin_logged_in'] = True
    try:
        response = sales_report()
        print(response.get_data(as_text=True))
    except Exception as e:
        import traceback
        traceback.print_exc()
