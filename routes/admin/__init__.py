"""
Admin Routes - Blueprint principal
Importa e registra todas as rotas dos módulos
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from database.models import get_db_connection
from database.connection import init_db
import sqlite3
import time
import logging
import os

# Importa helpers e funções dos módulos
from .helpers import (
    get_dolar_hoje, _read_cache, IOF, CUSTO_FIXO_PAINEL_USD, legacy_catalog_ids
)
from utils.image_utils import PILLOW_AVAILABLE

# Importa as rotas dos submódulos
from .products import register_products_routes
from .keys import register_keys_routes
from .links import register_links_routes
from .sales import register_sales_routes
from .recharges import register_recharges_routes
from .config import register_config_routes
from .feedbacks import register_feedbacks_routes
from .coupons import register_coupons_routes
from .resellers import register_resellers_routes

admin_bp = Blueprint('admin', __name__)

# Registra as rotas diretamente no Blueprint admin
register_products_routes(admin_bp)
register_keys_routes(admin_bp)
register_links_routes(admin_bp)
register_sales_routes(admin_bp)
register_recharges_routes(admin_bp)
register_config_routes(admin_bp)
register_feedbacks_routes(admin_bp)
register_coupons_routes(admin_bp)
register_resellers_routes(admin_bp)


# --- FUNÇÃO AUXILIAR PARA DADOS ADMIN ---

def _get_admin_data():
    """Retorna todos os dados necessários para as páginas admin"""
    conn = get_db_connection()
    try:
        all_products = conn.execute('SELECT * FROM products ORDER BY sort_order ASC, id ASC').fetchall()
        all_links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
        config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
        
        stock_query = conn.execute('SELECT product_id, COUNT(*) as total FROM product_keys WHERE is_used = 0 GROUP BY product_id').fetchall()
        stock_map = {row['product_id']: row['total'] for row in stock_query}
        
    except sqlite3.OperationalError:
        conn.close()
        init_db()
        return None

    # Cálculos financeiros
    dolar_hoje = get_dolar_hoje()
    
    # 1. Vendas Online (Orders)
    try:
        approved_orders = conn.execute('''
            SELECT amount, p.cost_usd, p.price, p.apply_iof
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.status = 'approved'
        ''').fetchall()
    except sqlite3.OperationalError:
        approved_orders = []

    online_revenue = 0.0
    for order in approved_orders:
        try:
            val = float(str(order['amount']).replace('R$', '').replace(',', '.').strip())
            online_revenue += val
        except:
            pass

    # 2. Vendas Manuais
    manual_sales = conn.execute('SELECT SUM(total_price) as total FROM manual_sales').fetchone()
    manual_revenue = float(manual_sales['total'] or 0) if manual_sales else 0.0

    # 3. Custos (Regime de Caixa - Apenas Recargas)
    recharges = conn.execute('SELECT SUM(total_cost_usd * dolar_rate) as total_brl FROM panel_recharges').fetchone()
    total_recharged_brl = float(recharges['total_brl'] or 0) if recharges else 0.0
    
    # Totais
    faturamento_total = online_revenue + manual_revenue
    custo_total = total_recharged_brl
    lucro_liquido = faturamento_total - custo_total
    
    financeiro = {
        'dolar_hoje': round(dolar_hoje, 4),
        'faturamento_total': round(faturamento_total, 2),
        'custo_total': round(custo_total, 2),
        'lucro_liquido': round(lucro_liquido, 2),
        'total_vendas': len(approved_orders) + conn.execute('SELECT COUNT(*) FROM manual_sales').fetchone()[0],
        'iof': IOF,
        'online_revenue': online_revenue,
        'manual_revenue': manual_revenue
    }

    try:
        cached = _read_cache()
        if cached and 'ts' in cached:
            financeiro['dolar_updated'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cached['ts']))
        else:
            financeiro['dolar_updated'] = '---'
    except Exception:
        financeiro['dolar_updated'] = '---'
        
    estoque_stats = {
        'total_chaves': sum(stock_map.values()),
        'valor_venda': 0.0,
        'valor_custo': 0.0,
        'lucro_potencial': 0.0
    }
    
    import re
    
    catalogs, simple_products, subproducts_by_parent, subproducts_by_category, parent_products = [], [], {}, {}, []
    
    for p in all_products:
        p_dict = dict(p)
        stock = stock_map.get(p['id'], 0)
        p_dict['stock'] = stock
        
        if stock > 0:
            price_str = str(p['price'] if p['price'] else '0')
            match = re.search(r'[\d\.,]+', price_str)
            price_val = 0.0
            if match:
                num_str = match.group()
                if ',' in num_str and '.' in num_str:
                    num_str = num_str.replace('.', '').replace(',', '.')
                elif ',' in num_str:
                    num_str = num_str.replace(',', '.')
                try:
                    price_val = float(num_str)
                except:
                    pass
            
            cost_brl = float(p['cost_brl'] if 'cost_brl' in p.keys() and p['cost_brl'] else 0.0)
            cost_usd = float(p['cost_usd'] if 'cost_usd' in p.keys() and p['cost_usd'] else 0.0)
            apply_iof = p['apply_iof'] if 'apply_iof' in p.keys() else 1
            
            cost_val = 0.0
            if cost_brl > 0:
                cost_val = cost_brl
            elif cost_usd > 0:
                if apply_iof:
                    cost_val = cost_usd * dolar_hoje * IOF
                else:
                    cost_val = cost_usd * dolar_hoje
                    
            estoque_stats['valor_venda'] += price_val * stock
            estoque_stats['valor_custo'] += cost_val * stock
            estoque_stats['lucro_potencial'] += (price_val - cost_val) * stock
        
        keys = p.keys()
        pid = p['parent_id'] if 'parent_id' in keys else None
        is_cat = p['is_catalog'] if 'is_catalog' in keys else 0

        if is_cat == 1 or p['id'] in legacy_catalog_ids:
            p_dict['is_folder'] = True
            parent_products.append(p_dict)
            if p['id'] not in subproducts_by_parent:
                subproducts_by_parent[p['id']] = []
            if p['id'] not in subproducts_by_category:
                subproducts_by_category[p['id']] = {}
        else:
            p_dict['is_folder'] = False

        if pid is None:
            if is_cat == 1 or p['id'] in legacy_catalog_ids:
                catalogs.append(p_dict)
            else:
                simple_products.append(p_dict) 
        else:
            if pid not in subproducts_by_parent:
                subproducts_by_parent[pid] = []
            subproducts_by_parent[pid].append(p_dict)
            
            if pid not in subproducts_by_category:
                subproducts_by_category[pid] = {}
            try:
                category = p.get('category', 'Sem categoria') if 'category' in keys else 'Sem categoria'
                if not category or category.strip() == '':
                    category = 'Sem categoria'
                if category not in subproducts_by_category[pid]:
                    subproducts_by_category[pid][category] = []
                subproducts_by_category[pid][category].append(p_dict)
            except Exception as e:
                if 'Sem categoria' not in subproducts_by_category[pid]:
                    subproducts_by_category[pid]['Sem categoria'] = []
                subproducts_by_category[pid]['Sem categoria'].append(p_dict)
                
    # Ordenar categorias baseadas no menor sort_order
    for pid in subproducts_by_category:
        sorted_items = sorted(
            subproducts_by_category[pid].items(),
            key=lambda item: min(p.get('sort_order', 0) for p in item[1]) if item[1] else 0
        )
        subproducts_by_category[pid] = {k: v for k, v in sorted_items}

    # Conta feedbacks pendentes
    try:
        pending_feedbacks_count = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE status = 'pending'").fetchone()[0]
    except sqlite3.OperationalError:
        pending_feedbacks_count = 0

    stats = {
        'total_products': len(all_products),
        'total_catalogs': len(catalogs),
        'total_links': len(all_links),
        'total_simple': len(simple_products),
        'pillow_available': PILLOW_AVAILABLE,
        'pending_feedbacks': pending_feedbacks_count
    }

    # Extract unique categories
    categories = sorted(list(set(p['category'] for p in all_products if p['category'] and p['category'].strip() != '')))

    # Extract unique suppliers
    suppliers = sorted(list(set(p['supplier'] for p in all_products if 'supplier' in p.keys() and p['supplier'] and p['supplier'].strip() != '')))

    # Security Audit
    security_warnings = []
    if current_app.config.get('SECRET_KEY') == 'dev-secret-key-change-me':
        security_warnings.append('SECRET_KEY insegura detectada (valor padrão). Configure uma chave forte no .env.')
    
    if current_app.config.get('ADMIN_PASSWORD') == 'admin123':
        security_warnings.append('ADMIN_PASSWORD insegura detectada (padrão "admin123"). Altere imediatamente no .env.')

    conn.close()
    
    return {
        'catalogs': catalogs,
        'simple_products': simple_products,
        'subproducts_by_parent': subproducts_by_parent,
        'subproducts_by_category': subproducts_by_category,
        'parent_products': parent_products,
        'categories': categories,
        'suppliers': suppliers,
        'links': all_links,
        'config': config,
        'stats': stats,
        'financeiro': financeiro,
        'estoque_stats': estoque_stats,
        'security_warnings': security_warnings,
        'pending_feedbacks_count': pending_feedbacks_count
    }


# --- ROTA PRINCIPAL (DASHBOARD) ---

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and session.get('admin_logged_in'):
        try:
            data = _get_admin_data()
            if data is None:
                return redirect(url_for('admin.admin'))
            return render_template('admin/dashboard.html', **data)
        except Exception as e:
            print(f"Erro ao carregar página admin: {e}")
            return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    
    if request.method == 'POST':
        if request.form.get('password') == current_app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin'))
        return render_template('admin_login.html', error='Senha incorreta!')
    return render_template('admin_login.html')


# --- ROTA DE PRODUTOS ---

@admin_bp.route('/admin/produtos')
def admin_produtos():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/produtos.html', **data)
    except Exception as e:
        print(f"Erro ao carregar produtos: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


# --- ROTA DE VENDAS ---

@admin_bp.route('/admin/vendas')
def admin_vendas():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/vendas.html', **data)
    except Exception as e:
        print(f"Erro ao carregar vendas: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@admin_bp.route('/admin/pendentes')
def admin_pendentes():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/pendentes.html', **data)
    except Exception as e:
        print(f"Erro ao carregar pendentes: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


# --- ROTA DE LINKS ---

@admin_bp.route('/admin/links')
def admin_links():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/links_page.html', **data)
    except Exception as e:
        print(f"Erro ao carregar links: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@admin_bp.route('/admin/cupons')
def admin_cupons():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/cupons.html', **data)
    except Exception as e:
        print(f"Erro ao carregar cupons: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/debug/dolar', methods=['GET'])
def debug_dolar():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    rate = get_dolar_hoje()
    cached = _read_cache()
    ts = cached.get('ts') if cached else time.time()
    return jsonify({'dolar_rate': round(rate, 4), 'timestamp': ts})


# --- ROTAS DE FEEDBACKS ---
@admin_bp.route('/admin/feedbacks')
def admin_feedbacks():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/feedbacks.html', **data)
    except Exception as e:
        print(f"Erro ao carregar feedbacks: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


# --- ROTAS DE FIDELIDADE (LOYALTY) ---

@admin_bp.route('/admin/loyalty')
def admin_loyalty():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    try:
        data = _get_admin_data()
        if data is None:
            return redirect(url_for('admin.admin'))
        return render_template('admin/loyalty.html', **data)
    except Exception as e:
        print(f"Erro ao carregar fidelidade: {e}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@admin_bp.route('/admin/api/loyalty/list', methods=['GET'])
def admin_loyalty_list():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        search = request.args.get('search', '').strip().lower()
        
        conn = get_db_connection()
        
        # Lista de clientes com pontos + dados de cadastro
        query_clients = '''
            SELECT cp.*, c.name, c.client_id, c.phone
            FROM client_points cp
            LEFT JOIN clients c ON cp.email = c.email
        '''
        params = []
        if search:
            query_clients += ' WHERE cp.email LIKE ? OR c.name LIKE ? OR c.client_id LIKE ?'
            params.append(f'%{search}%')
            params.append(f'%{search}%')
            params.append(f'%{search}%')
        query_clients += ' ORDER BY cp.points DESC, cp.updated_at DESC'
        
        clients = conn.execute(query_clients, params).fetchall()
        
        # Histórico recente de pontos geral (limite 50)
        history_query = '''
            SELECT email, points_changed, action_type, description, created_at
            FROM points_history
            ORDER BY created_at DESC LIMIT 50
        '''
        history = conn.execute(history_query).fetchall()
        
        conn.close()
        
        return jsonify({
            'clients': [dict(c) for c in clients],
            'history': [dict(h) for h in history]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/api/loyalty/adjust', methods=['POST'])
def admin_loyalty_adjust():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    try:
        data = request.json or {}
        email = data.get('email', '').strip().lower()
        points = int(data.get('points', 0))
        reason = data.get('reason', '').strip()
        
        if not email or points == 0 or not reason:
            return jsonify({'error': 'Dados incompletos'}), 400
            
        conn = get_db_connection()
        
        # Buscar ou criar cliente
        row = conn.execute('SELECT points FROM client_points WHERE email = ?', (email,)).fetchone()
        if row:
            new_pts = max(0, row['points'] + points)
            conn.execute('UPDATE client_points SET points = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?', (new_pts, email))
        else:
            if points < 0:
                conn.close()
                return jsonify({'error': 'Cliente não possui pontos para debitar.'}), 400
            conn.execute('INSERT INTO client_points (email, points) VALUES (?, ?)', (email, points))
            
        # Gravar histórico
        conn.execute('''
            INSERT INTO points_history (email, points_changed, action_type, description)
            VALUES (?, ?, 'admin_adjust', ?)
        ''', (email, points, reason))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pontos ajustados com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/api/loyalty/coupons/list', methods=['GET'])
def admin_points_coupons_list():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    try:
        coupons = conn.execute('SELECT * FROM points_coupons ORDER BY created_at DESC').fetchall()
        return jsonify({'coupons': [dict(c) for c in coupons]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/api/loyalty/coupons/add', methods=['POST'])
def admin_points_coupons_add():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    try:
        data = request.json or {}
        code = data.get('code', '').strip().upper()
        points = int(data.get('points_value', 0))
        max_uses_global = int(data.get('max_uses_global', 1))
        max_uses_per_client = int(data.get('max_uses_per_client', 1))
        valid_until = data.get('valid_until', '').strip() or None

        if not code or points <= 0:
            return jsonify({'error': 'Código do cupom e valor de pontos são obrigatórios.'}), 400

        conn = get_db_connection()
        
        # Verificar duplicados
        dup = conn.execute('SELECT 1 FROM points_coupons WHERE code = ?', (code,)).fetchone()
        if dup:
            conn.close()
            return jsonify({'error': 'Já existe um cupom cadastrado com este código.'}), 400

        conn.execute(
            '''INSERT INTO points_coupons (code, points_value, max_uses_global, max_uses_per_client, valid_until)
               VALUES (?, ?, ?, ?, ?)''',
            (code, points, max_uses_global, max_uses_per_client, valid_until)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Cupom de pontos criado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/api/loyalty/coupons/delete/<int:cid>', methods=['POST'])
def admin_points_coupons_delete(cid):
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM points_coupons WHERE id = ?', (cid,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Cupom excluído com sucesso!'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/api/clients/search', methods=['GET'])
def admin_clients_search():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'clients': []})
        
    conn = get_db_connection()
    try:
        clients = conn.execute(
            '''SELECT id, client_id, name, email, phone 
               FROM clients 
               WHERE client_id LIKE ? OR name LIKE ? OR email LIKE ?
               LIMIT 10''',
            (f'%{query}%', f'%{query}%', f'%{query}%')
        ).fetchall()
        return jsonify({'clients': [dict(c) for c in clients]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/admin/pdv')
def admin_pdv():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    
    conn = get_db_connection()
    try:
        # Pega os produtos ativos e catalogo=0 que possuem chaves disponiveis
        # Conta chaves em estoque para cada produto
        products = conn.execute('''
            SELECT p.*, COUNT(k.id) as stock
            FROM products p
            LEFT JOIN product_keys k ON k.product_id = p.id AND k.is_used = 0
            WHERE p.is_active = 1 AND p.is_catalog = 0
            GROUP BY p.id
            HAVING stock > 0
            ORDER BY p.sort_order ASC, p.id ASC
        ''').fetchall()
        
        products_list = [dict(p) for p in products]
        categories = sorted(list(set(p.get('category') for p in products_list if p.get('category'))))
        
        # Obter links para o autocomplete
        links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
        
        # Obter configurações de suporte/WhatsApp
        config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
        
        # Estatísticas de feedbacks pendentes (para passar ao base_admin)
        pending_feedbacks_count = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE status = 'pending'").fetchone()[0]
    except Exception as e:
        print(f"Erro ao carregar PDV: {e}")
        products_list = []
        categories = []
        links = []
        config = None
        pending_feedbacks_count = 0
    finally:
        conn.close()

    from routes.admin.helpers import get_dolar_hoje
    dolar_rate = get_dolar_hoje()
    
    return render_template('admin/pdv.html', 
                           products=products_list, 
                           categories=categories,
                           config=config, 
                           links=[dict(l) for l in links],
                           financeiro={'dolar_hoje': round(dolar_rate, 4)},
                           pending_feedbacks_count=pending_feedbacks_count)


@admin_bp.route('/admin/api/pdv/clients/search', methods=['GET'])
def admin_pdv_clients_search():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
        
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'clients': []})
        
    conn = get_db_connection()
    try:
        # 1. Buscar na tabela clients
        clients = conn.execute(
            '''SELECT client_id, name, email, phone 
               FROM clients 
               WHERE name LIKE ? OR email LIKE ? OR client_id LIKE ? OR phone LIKE ?
               LIMIT 10''',
            (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
        ).fetchall()
        
        results = []
        emails_seen = set()
        names_seen = set()
        
        for c in clients:
            item = {
                'name': c['name'],
                'email': c['email'] or '',
                'phone': c['phone'] or '',
                'client_id': c['client_id'] or '',
                'source': 'cadastro'
            }
            results.append(item)
            if c['email']:
                emails_seen.add(c['email'].lower().strip())
            names_seen.add(c['name'].lower().strip())
            
        # 2. Buscar na tabela manual_sales (nomes/emails distintos)
        manual = conn.execute(
            '''SELECT DISTINCT client_name, client_email 
               FROM manual_sales 
               WHERE (client_name LIKE ? OR client_email LIKE ?) 
                 AND client_name IS NOT NULL AND client_name != ''
               LIMIT 10''',
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        
        for m in manual:
            name = m['client_name'].strip()
            email = (m['client_email'] or '').strip()
            
            # Se já vimos o e-mail ou o nome exato, pula
            if email and email.lower() in emails_seen:
                continue
            if name.lower() in names_seen:
                continue
                
            item = {
                'name': name,
                'email': email,
                'phone': '',
                'client_id': 'Manual',
                'source': 'histórico'
            }
            results.append(item)
            if email:
                emails_seen.add(email.lower())
            names_seen.add(name.lower())
            
        return jsonify({'clients': results[:15]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
