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
                c.seller_coupon, 
                SUM(CASE WHEN c.status = 'pending' THEN c.commission_amount ELSE 0 END) as total_pending,
                SUM(CASE WHEN c.status = 'paid' THEN c.commission_amount ELSE 0 END) as total_paid,
                COUNT(CASE WHEN c.status = 'pending' THEN 1 END) as pending_count,
                COALESCE(cp.commission_percentage, 0.0) as commission_percentage
            FROM commissions c
            LEFT JOIN coupons cp ON cp.code = c.seller_coupon COLLATE NOCASE AND cp.is_seller = 1
            GROUP BY c.seller_coupon
        '''
        summary = conn.execute(summary_query).fetchall()
        
        # Histórico detalhado
        history_query = '''
            SELECT c.*, 
                   COALESCE(o.external_reference, CASE WHEN c.manual_sale_id IS NOT NULL THEN 'Manual #' || c.manual_sale_id ELSE 'Ajuste Manual' END) as order_ref,
                   COALESCE(p.name, 'Lançamento Direto') as product_name
            FROM commissions c
            LEFT JOIN orders o ON c.order_id = o.id
            LEFT JOIN manual_sales ms ON c.manual_sale_id = ms.id
            LEFT JOIN products p ON COALESCE(o.product_id, ms.product_id) = p.id
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
    notes = data.get('notes', 'Débito manual de saldo')
    
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
        conn.execute('''
            INSERT INTO commissions (seller_coupon, sale_amount, commission_amount, status, notes)
            VALUES (?, 0, ?, 'pending', ?)
        ''', (seller_coupon, -amount, notes))
        conn.commit()
        return jsonify({'success': True, 'message': f'R$ {amount:.2f} debitados com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def adjust_commission():
    """Registra um bônus (crédito) ou desconto (débito) manual com justificativa no extrato."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    data = request.json or {}
    seller_coupon = (data.get('seller_coupon') or '').strip().upper()
    adj_type = data.get('type', 'credit')  # 'credit' or 'debit'
    amount_str = data.get('amount')
    reason = (data.get('reason') or '').strip()
    
    if not seller_coupon or not amount_str:
        return jsonify({'error': 'Vendedor ou valor não especificado'}), 400
        
    try:
        amount = float(str(amount_str).replace(',', '.'))
        if amount <= 0:
            return jsonify({'error': 'O valor deve ser maior que zero'}), 400
    except ValueError:
        return jsonify({'error': 'Valor inválido'}), 400
        
    final_amount = amount if adj_type == 'credit' else -amount
    default_reason = f"Bônus/Crédito manual (R$ {amount:.2f})" if adj_type == 'credit' else f"Desconto/Adiantamento (-R$ {amount:.2f})"
    final_notes = reason or default_reason
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO commissions (seller_coupon, sale_amount, commission_amount, status, notes)
            VALUES (?, 0, ?, 'pending', ?)
        ''', (seller_coupon, final_amount, final_notes))
        conn.commit()
        return jsonify({'success': True, 'message': f'Ajuste de R$ {final_amount:+.2f} registrado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def update_commission_amount(comm_id):
    """Permite alterar o valor R$ de um lançamento de comissão pendente específico."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    data = request.json or {}
    try:
        new_amount = float(str(data.get('amount')).replace(',', '.'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Valor de comissão inválido'}), 400
        
    notes = (data.get('notes') or '').strip()
    
    conn = get_db_connection()
    try:
        comm = conn.execute('SELECT * FROM commissions WHERE id = ?', (comm_id,)).fetchone()
        if not comm:
            return jsonify({'error': 'Comissão não encontrada'}), 404
        if comm['status'] == 'paid':
            return jsonify({'error': 'Não é possível editar uma comissão já paga'}), 400
            
        final_notes = notes or comm['notes'] or 'Valor editado manualmente'
        conn.execute('UPDATE commissions SET commission_amount = ?, notes = ? WHERE id = ?', (new_amount, final_notes, comm_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Valor da comissão atualizado!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def delete_commission(comm_id):
    """Exclui um lançamento de comissão pendente."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    conn = get_db_connection()
    try:
        comm = conn.execute('SELECT * FROM commissions WHERE id = ?', (comm_id,)).fetchone()
        if not comm:
            return jsonify({'error': 'Comissão não encontrada'}), 404
        if comm['status'] == 'paid':
            return jsonify({'error': 'Não é possível excluir uma comissão que já foi paga'}), 400
            
        conn.execute('DELETE FROM commissions WHERE id = ?', (comm_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Lançamento de comissão excluído com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def update_seller_rate():
    """Permite atualizar a taxa percentual de um vendedor (cupom) diretamente."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    data = request.json or {}
    seller_coupon = (data.get('seller_coupon') or '').strip()
    rate_str = data.get('rate')
    
    if not seller_coupon or rate_str is None:
        return jsonify({'error': 'Vendedor ou taxa não especificada'}), 400
        
    try:
        rate = float(str(rate_str).replace(',', '.'))
        if rate < 0 or rate > 100:
            return jsonify({'error': 'A taxa deve estar entre 0% e 100%'}), 400
    except ValueError:
        return jsonify({'error': 'Taxa inválida'}), 400
        
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            UPDATE coupons 
            SET commission_percentage = ?
            WHERE code = ? COLLATE NOCASE AND is_seller = 1
        ''', (rate, seller_coupon))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': f'Cupom de vendedor "{seller_coupon}" não encontrado na tabela de cupons.'}), 404
        return jsonify({'success': True, 'message': f'Taxa do vendedor {seller_coupon} atualizada para {rate}%!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


def register_commissions_routes(bp):
    bp.route('/painel-mestre/commissions')(admin_commissions_page)
    bp.route('/painel-mestre/api/commissions/list', methods=['GET'])(list_commissions)
    bp.route('/painel-mestre/api/commissions/pay', methods=['POST'])(pay_commissions)
    bp.route('/painel-mestre/api/commissions/debit', methods=['POST'])(debit_commissions)
    bp.route('/painel-mestre/api/commissions/adjust', methods=['POST'])(adjust_commission)
    bp.route('/painel-mestre/api/commissions/update/<int:comm_id>', methods=['POST'])(update_commission_amount)
    bp.route('/painel-mestre/api/commissions/delete/<int:comm_id>', methods=['POST'])(delete_commission)
    bp.route('/painel-mestre/api/commissions/update-seller-rate', methods=['POST'])(update_seller_rate)
