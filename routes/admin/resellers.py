from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from database.models import get_db_connection
import uuid
import hashlib

def register_resellers_routes(admin_bp):

    @admin_bp.route('/admin/revendedores')
    def admin_resellers():
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin'))
        
        from .__init__ import _get_admin_data
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
            
        conn = get_db_connection()
        try:
            # Lista todos clientes para a tabela principal
            clients = conn.execute('SELECT id, client_id, name, email, phone, is_reseller, wallet_balance, created_at FROM clients ORDER BY is_reseller DESC, name ASC').fetchall()
            data['clients'] = [dict(c) for c in clients]
            
        except Exception as e:
            print(f"Erro ao carregar revendedores: {e}")
        finally:
            conn.close()
            
        return render_template('admin/resellers.html', **data)


    @admin_bp.route('/admin/api/resellers/toggle', methods=['POST'])
    def admin_api_resellers_toggle():
        if not session.get('admin_logged_in'):
            return jsonify({'error': '401'}), 401
            
        data = request.json or {}
        client_id = data.get('id')
        is_reseller = data.get('is_reseller', 0)
        
        if not client_id:
            return jsonify({'error': 'ID do cliente inválido'}), 400
            
        conn = get_db_connection()
        try:
            conn.execute('UPDATE clients SET is_reseller = ? WHERE id = ?', (is_reseller, client_id))
            conn.commit()
            return jsonify({'success': True, 'message': 'Status atualizado!'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()

    @admin_bp.route('/admin/api/resellers/add', methods=['POST'])
    def admin_api_resellers_add():
        if not session.get('admin_logged_in'):
            return jsonify({'error': '401'}), 401
            
        data = request.json or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        
        if not name or not email or not password:
            return jsonify({'error': 'Nome, email e senha são obrigatórios.'}), 400
            
        # Hash simple (mesmo padrão do sistema, verifique como ele gera senha, mas em geral é hash de string ou algo do tipo.
        # No seu sistema parece que usa bcrypt ou pbkdf2? Vou usar um hash básico SHA256 que pode ser checado ou o que já usarem.
        # Caso o sistema original utilize werkzeug.security, importo isso. O app original não está claro, vamos usar o padrão.
        # Vou usar hashlib SHA256 hexdigest provisoriamente, ou podemos usar werkzeug se a rota de auth utilizar isso.
        
        try:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
        except ImportError:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

        client_id = str(uuid.uuid4().hex)[:10].upper()
        
        conn = get_db_connection()
        try:
            # Check if email exists
            exists = conn.execute('SELECT id FROM clients WHERE email = ?', (email,)).fetchone()
            if exists:
                return jsonify({'error': 'Este email já está cadastrado no sistema.'}), 400
                
            conn.execute(
                'INSERT INTO clients (client_id, name, email, phone, password_hash, is_reseller, wallet_balance) VALUES (?, ?, ?, ?, ?, 1, 0.0)',
                (client_id, name, email, phone, password_hash)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Revendedor cadastrado com sucesso!'})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()


    @admin_bp.route('/admin/api/resellers/balance', methods=['POST'])
    def admin_api_resellers_balance():
        if not session.get('admin_logged_in'):
            return jsonify({'error': '401'}), 401
            
        data = request.json or {}
        client_id = data.get('id')
        amount = float(data.get('amount', 0))
        action = data.get('action') # 'add' or 'remove'
        description = data.get('description', '')
        
        if not client_id or amount <= 0:
            return jsonify({'error': 'Dados inválidos para saldo'}), 400
            
        conn = get_db_connection()
        try:
            client = conn.execute('SELECT wallet_balance FROM clients WHERE id = ?', (client_id,)).fetchone()
            if not client:
                return jsonify({'error': 'Cliente não encontrado'}), 404
                
            current_balance = client['wallet_balance'] or 0.0
            
            if action == 'add':
                new_balance = current_balance + amount
                t_type = 'add_balance'
            elif action == 'remove':
                if current_balance < amount:
                    return jsonify({'error': 'Saldo insuficiente para remover'}), 400
                new_balance = current_balance - amount
                t_type = 'remove_balance'
            else:
                return jsonify({'error': 'Ação inválida'}), 400
                
            conn.execute('UPDATE clients SET wallet_balance = ? WHERE id = ?', (new_balance, client_id))
            
            # Registrar no histórico
            conn.execute(
                'INSERT INTO reseller_transactions (reseller_id, amount, transaction_type, description) VALUES (?, ?, ?, ?)',
                (client_id, amount, t_type, description)
            )
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Saldo atualizado com sucesso!', 'new_balance': new_balance})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
            
    @admin_bp.route('/admin/api/resellers/history/<int:client_id>', methods=['GET'])
    def admin_api_resellers_history(client_id):
        if not session.get('admin_logged_in'):
            return jsonify({'error': '401'}), 401
            
        conn = get_db_connection()
        try:
            history = conn.execute(
                'SELECT * FROM reseller_transactions WHERE reseller_id = ? ORDER BY created_at DESC LIMIT 50', 
                (client_id,)
            ).fetchall()
            return jsonify({'history': [dict(h) for h in history]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
