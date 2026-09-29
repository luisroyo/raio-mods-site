from flask import request, jsonify, session, render_template, redirect, url_for
from database.models import get_db_connection

def get_analytics_data():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'error': '401'}), 401
        
        conn = get_db_connection()
        # Pega ultimas 500 visitas
        visits = conn.execute('''
            SELECT * FROM visits 
            WHERE user_agent NOT LIKE '%bot%' 
              AND user_agent NOT LIKE '%spider%' 
              AND user_agent NOT LIKE '%crawler%'
            ORDER BY created_at DESC 
            LIMIT 1000
        ''').fetchall()
        
        # Sumariza pageviews por dia (ultimos 30 dias)
        daily_views = conn.execute('''
            SELECT date(created_at) as day, count(*) as total, count(DISTINCT ip_address) as unique_visits
            FROM visits
            WHERE created_at >= date('now', '-30 days')
              AND user_agent NOT LIKE '%bot%' 
              AND user_agent NOT LIKE '%spider%' 
              AND user_agent NOT LIKE '%crawler%'
            GROUP BY day
            ORDER BY day ASC
        ''').fetchall()
        
        # Top referrers (Ignorando tráfego interno)
        raw_referrers = conn.execute('''
            SELECT referrer
            FROM visits
            WHERE referrer != '' AND referrer IS NOT NULL
              AND referrer NOT LIKE '%raiomodsgames.pythonanywhere.com%'
              AND referrer NOT LIKE '%127.0.0.1%'
              AND referrer NOT LIKE '%localhost%'
              AND user_agent NOT LIKE '%bot%' 
              AND user_agent NOT LIKE '%spider%' 
              AND user_agent NOT LIKE '%crawler%'
        ''').fetchall()
        
        from urllib.parse import urlparse
        from collections import Counter
        
        domains = []
        for r in raw_referrers:
            try:
                domain = urlparse(r['referrer']).hostname
                if domain:
                    domains.append(domain)
                else:
                    domains.append(r['referrer'])
            except:
                domains.append(r['referrer'])
                
        domain_counts = Counter(domains)
        top_referrers = [{'referrer': k, 'total': v} for k, v in domain_counts.most_common(10)]
        
        # Top pages
        top_pages = conn.execute('''
            SELECT path, count(*) as total
            FROM visits
            WHERE user_agent NOT LIKE '%bot%' 
              AND user_agent NOT LIKE '%spider%' 
              AND user_agent NOT LIKE '%crawler%'
            GROUP BY path
            ORDER BY total DESC
            LIMIT 10
        ''').fetchall()

        conn.close()
        
        return jsonify({
            'visits': [dict(v) for v in visits],
            'daily': [dict(d) for d in daily_views],
            'referrers': [dict(r) for r in top_referrers],
            'pages': [dict(p) for p in top_pages]
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 200

def register_analytics_routes(bp):
    @bp.route('/admin/analytics')
    def analytics_page():
        if not session.get('admin_logged_in'):
            return redirect(url_for('public.admin_login'))
        
        # O base admin precisa de algumas variáveis, mas vamos tentar renderizar direto
        # Caso quebre algo, precisaremos importar _get_admin_data ou passar vars básicas
        from .__init__ import _get_admin_data
        admin_data = _get_admin_data()
        
        return render_template('admin/analytics.html', **admin_data)

    bp.add_url_rule('/admin/analytics/data', view_func=get_analytics_data, methods=['GET'])
