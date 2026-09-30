import os
from flask import Flask, session
from routes.admin.analytics import get_analytics_data
from database.connection import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

with app.test_request_context('/admin/analytics/data'):
    session['admin_logged_in'] = True
    try:
        init_db()
        response = get_analytics_data()
        if hasattr(response, 'get_json'):
            print("SUCCESS")
            print(response.get_json())
        else:
            print("Response:", response)
    except Exception as e:
        import traceback
        traceback.print_exc()
