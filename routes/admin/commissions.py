from flask import Blueprint, request, jsonify, render_template, session
from database.models import get_db_connection

def admin_commissions_page():
    if not session.get('admin_logged_in'):
        from flask import redirect, url_for
        return redirect(url_for('admin.admin'))
    
    # Needs to get data for the base admin template
    from routes.admin import _get_admin_data
    try:
        data = _get_admin_data()
        if data is None:
            from flask import redirect, url_for
            return redirect(url_for('admin.admin'))
        return render_template('admin/comissoes.html', **data)
    except Exception as e:
        print(f"Erro ao carregar comissões: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


def list_commissions():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    conn = get_db_connection()
    try:
        # Resumo por vendedor
        summary_query = '''
            SELECT 
                seller_coupon, 
                SUM(CASE WHEN status = 'pending' THEN commission_amount ELSE 0 END) as total_pending,
                SUM(CASE WHEN status = 'paid' THEN commission_amount ELSE 0 END) as total_paid
            FROM commissions
            GROUP BY seller_coupon
        '''
        summary = conn.execute(summary_query).fetchall()
        
        # Histórico detalhado
        history_query = '''
            SELECT c.*, 
                   COALESCE(o.external_reference, 'Manual #' || c.manual_sale_id) as order_ref
            FROM commissions c
            LEFT JOIN orders o ON c.order_id = o.id
            ORDER BY c.created_at DESC
        '''
        history = conn.execute(history_query).fetchall()
        
        return jsonify({
            'summary': [dict(s) for s in summary],
            'history': [dict(h) for h in history]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def pay_commissions():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    data = request.json or {}
    seller_coupon = data.get('seller_coupon')
    
    if not seller_coupon:
        return jsonify({'error': 'Vendedor não especificado'}), 400
        
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE commissions 
            SET status = 'paid', paid_at = CURRENT_TIMESTAMP
            WHERE seller_coupon = ? AND status = 'pending'
        ''', (seller_coupon,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Comissões marcadas como pagas!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def debit_commissions():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    data = request.json or {}
    seller_coupon = data.get('seller_coupon')
    amount_str = data.get('amount')
    
    if not seller_coupon or not amount_str:
        return jsonify({'error': 'Vendedor ou valor não especificado'}), 400
        
    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'error': 'O valor deve ser maior que zero'}), 400
    except ValueError:
        return jsonify({'error': 'Valor inválido'}), 400
        
    conn = get_db_connection()
    try:
        # Registra um débito como uma comissão negativa
        conn.execute('''
            INSERT INTO commissions (seller_coupon, sale_amount, commission_amount, status)
            VALUES (?, 0, ?, 'pending')
        ''', (seller_coupon, -amount))
        conn.commit()
        return jsonify({'success': True, 'message': f'R$ {amount:.2f} debitados com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

def register_commissions_routes(bp):
    bp.route('/admin/commissions')(admin_commissions_page)
    bp.route('/admin/api/commissions/list', methods=['GET'])(list_commissions)
    bp.route('/admin/api/commissions/pay', methods=['POST'])(pay_commissions)
    bp.route('/admin/api/commissions/debit', methods=['POST'])(debit_commissions)
