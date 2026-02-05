from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from werkzeug.utils import secure_filename
from database.models import get_db_connection
from database.connection import init_db
from utils.image_utils import process_upload_image, get_base_filename
import os
import sqlite3
import time
import requests
import logging

# Configure logging to file
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), '..', 'dolar.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_dolar_hoje():
    """
    Consulta a cotação atual do dólar em tempo real via API AwesomeAPI.
    Retorna o valor 'bid' (compra) como float.
    Em caso de erro, tenta APIs alternativas.
    Valor padrão de segurança: 5.50
    """
    apis = [
        ('https://economia.awesomeapi.com.br/last/USD-BRL', 'USDBRL', 'bid'),
        ('https://api.exchangerate-api.com/v4/latest/USD', 'rates', 'BRL'),
    ]
    
    for api_url, key1, key2 in apis:
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if key1 in data:
                    if isinstance(data[key1], dict) and key2 in data[key1]:
                        bid = float(data[key1][key2])
                        msg = f"[OK] Dolar atualizado via {api_url}: R$ {bid:.2f}"
                        print(msg)
                        logger.info(msg)
                        return bid
        except Exception as e:
            msg = f"[ERRO] Falha ao consultar dolar em {api_url}: {e}"
            print(msg)
            logger.error(msg)
            continue
    
    # Se todas as APIs falharem, usar valor padrão
    msg = f"[AVISO] Todas as APIs falharam. Usando valor padrao: R$ 5.50"
    print(msg)
    logger.warning(msg)
    return 5.50

@admin_bp.route('/admin/debug/dolar', methods=['GET'])
def debug_dolar():
    """Endpoint para debugar a cotação do dólar em tempo real"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    
    dolar = get_dolar_hoje()
    return jsonify({
        'dolar_rate': round(dolar, 4),
        'timestamp': time.time(),
        'note': 'Se o valor for 5.50, a API pode estar falhando. Verifique os logs do servidor.'
    })

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and session.get('admin_logged_in'):
        try:
            conn = get_db_connection()
            try:
                # Busca produtos
                all_products = conn.execute('SELECT * FROM products ORDER BY sort_order ASC, id ASC').fetchall()
                all_links = conn.execute('SELECT * FROM links ORDER BY created_at DESC').fetchall()
                config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
                
                # --- CONTAGEM DE ESTOQUE ---
                # Conta quantas chaves livres (is_used=0) cada produto tem
                stock_query = conn.execute('SELECT product_id, COUNT(*) as total FROM product_keys WHERE is_used = 0 GROUP BY product_id').fetchall()
                stock_map = {row['product_id']: row['total'] for row in stock_query}
                
            except sqlite3.OperationalError:
                conn.close()
                init_db()
                return redirect(url_for('admin.admin'))

            # --- CÁLCULOS FINANCEIROS ---
            dolar_hoje = get_dolar_hoje()
            IOF = 1.0638  # 6.38%
            CUSTO_FIXO_PAINEL_USD = 50.0
            
            # Busca todas as vendas aprovadas com join para pegar cost_usd e flag apply_iof
            # Backwards compatible: tenta usar apply_iof, cai de volta para 1 se coluna não existe
            try:
                approved_orders = conn.execute('''
                    SELECT o.*, p.cost_usd, p.price, p.apply_iof
                    FROM orders o
                    JOIN products p ON o.product_id = p.id
                    WHERE o.status = 'approved'
                ''').fetchall()
            except sqlite3.OperationalError:
                # Coluna apply_iof ainda não existe; usar 1 como padrão
                approved_orders = conn.execute('''
                    SELECT o.*, p.cost_usd, p.price, 1 as apply_iof
                    FROM orders o
                    JOIN products p ON o.product_id = p.id
                    WHERE o.status = 'approved'
                ''').fetchall()
            
            faturamento_total = 0.0
            custo_vendas_total = 0.0
            
            for order in approved_orders:
                # Faturamento em BRL
                try:
                    amount = float(str(order['amount']).replace('R$', '').replace(',', '.').strip())
                    faturamento_total += amount
                except:
                    pass
                
                # Custo das vendas em BRL (USD * cotação) e aplica IOF somente quando configurado
                try:
                    cost_usd = float(order['cost_usd'] or 0)
                    if cost_usd > 0:
                        apply_iof = 1
                        try:
                            # Alguns registros antigos podem não ter a coluna; usar 1 por padrão
                            apply_iof = int(order['apply_iof']) if 'apply_iof' in order.keys() else 1
                        except:
                            apply_iof = 1

                        if apply_iof == 1:
                            custo_vendas_total += (cost_usd * dolar_hoje * IOF)
                        else:
                            custo_vendas_total += (cost_usd * dolar_hoje)
                except:
                    pass
            
            # Custo fixo do painel (50 USD * cotação * IOF)
            custo_fixo_painel_brl = CUSTO_FIXO_PAINEL_USD * dolar_hoje * IOF
            
            # Lucro líquido final
            lucro_liquido = faturamento_total - custo_vendas_total - custo_fixo_painel_brl
            
            financeiro = {
                'dolar_hoje': round(dolar_hoje, 2),
                'faturamento_total': round(faturamento_total, 2),
                'custo_vendas_total': round(custo_vendas_total, 2),
                'custo_fixo_painel_brl': round(custo_fixo_painel_brl, 2),
                'lucro_liquido': round(lucro_liquido, 2),
                'total_vendas': len(approved_orders),
                'iof': IOF,
            }

            # Lógica de Catálogos vs Produtos Simples
            legacy_rows = conn.execute('SELECT parent_id FROM products WHERE parent_id IS NOT NULL').fetchall()
            legacy_catalog_ids = set(r[0] for r in legacy_rows)
            
            catalogs, simple_products, subproducts_by_parent, subproducts_by_category, parent_products = [], [], {}, {}, []
            
            for p in all_products:
                # Adiciona a contagem de estoque ao objeto do produto
                p_dict = dict(p)
                p_dict['stock'] = stock_map.get(p['id'], 0) # Se não tiver chave, é 0
                
                keys = p.keys()
                pid = p['parent_id'] if 'parent_id' in keys else None
                is_cat = p['is_catalog'] if 'is_catalog' in keys else 0

                if pid is None and (is_cat == 1 or p['id'] in legacy_catalog_ids): parent_products.append(p_dict)

                if pid is None:
                    if is_cat == 1 or p['id'] in legacy_catalog_ids:
                        catalogs.append(p_dict)
                        if p['id'] not in subproducts_by_parent: subproducts_by_parent[p['id']] = []
                        if p['id'] not in subproducts_by_category: subproducts_by_category[p['id']] = {}
                    else:
                        simple_products.append(p_dict) 
                else:
                    if pid not in subproducts_by_parent: subproducts_by_parent[pid] = []
                    subproducts_by_parent[pid].append(p_dict)
                    
                    # Agrupa por categoria dentro da capa (com segurança)
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
                        print(f"Erro ao agrupar produto {p['id']} por categoria: {e}")
                        # Fallback: adicionar em categoria genérica
                        if 'Sem categoria' not in subproducts_by_category[pid]: 
                            subproducts_by_category[pid]['Sem categoria'] = []
                        subproducts_by_category[pid]['Sem categoria'].append(p_dict)
            
            stats = {
                'total_products': len(all_products),
                'total_catalogs': len(catalogs),
                'total_links': len(all_links),
                'total_simple': len(simple_products),
            }
            conn.close()
            return render_template('admin.html', catalogs=catalogs, simple_products=simple_products, 
                                 subproducts_by_parent=subproducts_by_parent, subproducts_by_category=subproducts_by_category,
                                 parent_products=parent_products, links=all_links, config=config, stats=stats, financeiro=financeiro)
        except Exception as e:
            print(f"Erro ao carregar página admin: {e}")
            return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    
    if request.method == 'POST':
        if request.form.get('password') == current_app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin'))
        return render_template('admin_login.html', error='Senha incorreta!')
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.admin'))

# --- ROTAS DE PRODUTOS ---

@admin_bp.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    name = request.form.get('name')
    desc = request.form.get('description')
    price = request.form.get('price')
    cat = request.form.get('category')
    tagline = (request.form.get('tagline') or '').strip()
    payment_url = (request.form.get('payment_url') or '').strip()
    promo_price = (request.form.get('promo_price') or '').strip()
    promo_label = (request.form.get('promo_label') or '').strip()
    
    # Novo: Recebe cost_usd
    try:
        cost_usd = float(request.form.get('cost_usd', 0) or 0)
    except:
        cost_usd = 0.0
    # Novo: Recebe flag apply_iof (checkbox). Pode vir como lista; tomar último valor se houver.
    try:
        vals = request.form.getlist('apply_iof')
        if vals:
            apply_iof = int(vals[-1])
        else:
            apply_iof = int(request.form.get('apply_iof', 1) or 1)
    except:
        try:
            apply_iof = int(request.form.get('apply_iof', 1) or 1)
        except:
            apply_iof = 1
    
    try: is_catalog = int(request.form.get('is_catalog', 0))
    except: is_catalog = 0
    try: sort_order = int(request.form.get('sort_order') or 0)
    except: sort_order = 0
    
    parent_id = request.form.get('parent_id')
    if not parent_id or str(parent_id).strip() == '':
        parent_id = None
    
    image = request.form.get('image_url', '')
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    
    if not all([name, desc, price, image, cat]): return jsonify({'error': 'Faltam dados'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO products (name, description, price, image, category, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label, cost_usd, apply_iof) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                 (name, desc, price, image, cat, tagline, sort_order, parent_id, is_catalog, payment_url, promo_price, promo_label, cost_usd, apply_iof))
        conn.commit()
    except sqlite3.OperationalError as e:
        conn.close()
        return jsonify({'error': 'Erro no banco de dados: ' + str(e)}), 500
        
    conn.close()
    return jsonify({'success': True, 'message': 'Adicionado!'})

@admin_bp.route('/admin/delete/<int:pid>', methods=['POST'])
def delete_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    conn.execute('UPDATE products SET parent_id = NULL WHERE parent_id = ?', (pid,))
    conn.execute('DELETE FROM products WHERE id = ?', (pid,)); conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Removido!'})

@admin_bp.route('/admin/edit/<int:pid>', methods=['POST'])
def edit_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
        if not row: conn.close(); return jsonify({'error': '404'}), 404
        
        existing = dict(row)
        name = request.form.get('name') or existing.get('name', '')
        desc = request.form.get('description') or existing.get('description', '')
        price = request.form.get('price') or existing.get('price', '')
        cat = request.form.get('category') or existing.get('category', '')
        tagline = request.form.get('tagline', existing.get('tagline', '')).strip()
        payment_url = request.form.get('payment_url', existing.get('payment_url', '')).strip()
        promo_price = (request.form.get('promo_price') or existing.get('promo_price') or '').strip()
        promo_label = (request.form.get('promo_label') or existing.get('promo_label') or '').strip()
        
        # Novo: Recebe cost_usd
        try:
            cost_usd = float(request.form.get('cost_usd') or existing.get('cost_usd', 0) or 0)
        except:
            cost_usd = float(existing.get('cost_usd', 0) or 0)
        # Novo: Recebe flag apply_iof (checkbox). Pode vir como lista; tomar último valor se houver.
        try:
            vals = request.form.getlist('apply_iof')
            if vals:
                apply_iof = int(vals[-1])
            else:
                apply_iof = int(request.form.get('apply_iof', existing.get('apply_iof', 1)) or existing.get('apply_iof', 1))
        except:
            try:
                apply_iof = int(request.form.get('apply_iof', existing.get('apply_iof', 1)) or existing.get('apply_iof', 1))
            except:
                apply_iof = int(existing.get('apply_iof', 1) or 1)
        
        try: is_catalog = int(request.form.get('is_catalog', existing.get('is_catalog', 0)))
        except: is_catalog = 0
        try: sort = int(request.form.get('sort_order') or existing.get('sort_order', 0))
        except: sort = 0
        
        pid_val = request.form.get('parent_id')
        
        # --- CORREÇÃO DE LÓGICA DO PAI/CATÁLOGO ---
        # Se for marcado como catálogo, NÃO pode ter pai.
        if is_catalog == 1:
            pid_val = None
        # Se o pai for ele mesmo ou string vazia, anula
        elif pid_val == str(pid) or not pid_val or str(pid_val).strip() == '':
            pid_val = None
        
        img = request.form.get('image_url') or ''
        if not img: img = existing.get('image', '')
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                base_name = get_base_filename(secure_filename(file.filename))
                uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
                if ok: img = img_path
                else:
                    fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                    file.seek(0); file.save(os.path.join(uploads_dir, fname))
                    img = f"/static/uploads/{fname}"

        conn.execute('UPDATE products SET name=?, description=?, price=?, image=?, category=?, tagline=?, sort_order=?, parent_id=?, is_catalog=?, payment_url=?, promo_price=?, promo_label=?, cost_usd=?, apply_iof=? WHERE id=?',
                 (name, desc, price, img, cat, tagline, sort, pid_val, is_catalog, payment_url, promo_price, promo_label, cost_usd, apply_iof, pid))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Atualizado!'})
        
    except sqlite3.OperationalError as e:
        conn.close() if 'conn' in locals() else None
        return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500
    except Exception as e:
        conn.close() if 'conn' in locals() else None
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# --- ROTA DE CONFIGURAÇÃO ---

@admin_bp.route('/admin/config', methods=['POST'])
def update_config():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    pix_key = request.form.get('pix_key') or ''
    pix_copia_cola = request.form.get('pix_copia_cola') or ''
    contact_whatsapp = request.form.get('contact_whatsapp') or ''
    mercado_pago_token = (request.form.get('mercado_pago_token') or '').strip()

    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config WHERE id = 1').fetchone()
    try:
        if not config:
            conn.execute('INSERT INTO config (id, pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token) VALUES (1, ?, ?, ?, ?)',
                         (pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token or ''))
        else:
            # Não sobrescrever o token se o campo foi enviado vazio (manter o valor atual)
            if not mercado_pago_token and 'mercado_pago_token' in config.keys():
                mercado_pago_token = config['mercado_pago_token'] or ''
            conn.execute('UPDATE config SET pix_key = ?, pix_copia_cola = ?, contact_whatsapp = ?, mercado_pago_token = ? WHERE id = 1',
                         (pix_key, pix_copia_cola, contact_whatsapp, mercado_pago_token))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()
    return jsonify({'success': True})

# --- ROTAS DE CHAVES (ESTOQUE) ---

@admin_bp.route('/admin/keys/add', methods=['POST'])
def add_keys():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    product_id = request.form.get('product_id')
    keys_text = request.form.get('keys_list') # Texto com várias chaves
    
    if not product_id or not keys_text:
        return jsonify({'error': 'Dados inválidos'}), 400
        
    # Separa por quebra de linha
    key_list = [k.strip() for k in keys_text.splitlines() if k.strip()]
    
    if not key_list:
        return jsonify({'error': 'Nenhuma chave válida encontrada'}), 400
        
    conn = get_db_connection()
    count = 0
    for key in key_list:
        # Verifica duplicidade simples antes de inserir
        exists = conn.execute('SELECT id FROM product_keys WHERE key_value = ?', (key,)).fetchone()
        if not exists:
            conn.execute('INSERT INTO product_keys (product_id, key_value, is_used) VALUES (?, ?, 0)', (product_id, key))
            count += 1
            
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'{count} chaves adicionadas com sucesso!'})

# --- ROTAS DE LINKS ---

@admin_bp.route('/admin/links/add', methods=['POST'])
def add_link():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    download_link = (request.form.get('download_link') or '').strip()
    video_link = (request.form.get('video_link') or '').strip()
    game = (request.form.get('game') or '').strip()
    image_url = (request.form.get('image_url') or '').strip()
    
    if not title: return jsonify({'error': 'Título obrigatório'}), 400
    if not download_link and not video_link: return jsonify({'error': 'Pelo menos um link necessário'}), 400
    
    image = image_url
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    
    conn = get_db_connection()
    conn.execute('INSERT INTO links (title, description, image, download_link, video_link, game) VALUES (?,?,?,?,?,?)',
                 (title, description, image, download_link, video_link, game))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@admin_bp.route('/admin/links/delete/<int:lid>', methods=['POST'])
def delete_link(lid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection(); conn.execute('DELETE FROM links WHERE id = ?', (lid,)); conn.commit(); conn.close()
    return jsonify({'success': True})

@admin_bp.route('/admin/links/edit/<int:lid>', methods=['POST'])
def edit_link(lid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM links WHERE id = ?', (lid,)).fetchone()
    if not existing: conn.close(); return jsonify({'error': '404'}), 404
    
    existing = dict(existing)
    title = (request.form.get('title') or existing.get('title', '')).strip()
    description = (request.form.get('description') or '').strip()
    download_link = (request.form.get('download_link') or '').strip()
    video_link = (request.form.get('video_link') or '').strip()
    game = (request.form.get('game') or '').strip()
    image_url = (request.form.get('image_url') or '').strip()
    
    if not download_link and not video_link: conn.close(); return jsonify({'error': 'Pelo menos um link'}), 400
    
    image = existing.get('image')
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            base_name = get_base_filename(secure_filename(file.filename))
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            img_path, ok = process_upload_image(file.stream, uploads_dir, base_name)
            if ok: image = img_path
            else:
                fname = f"{int(time.time())}_{secure_filename(file.filename)}"
                file.seek(0); file.save(os.path.join(uploads_dir, fname))
                image = f"/static/uploads/{fname}"
    elif image_url: image = image_url
    
    conn.execute('UPDATE links SET title=?, description=?, image=?, download_link=?, video_link=?, game=? WHERE id=?',
                 (title, description, image, download_link, video_link, game, lid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# --- ROTAS DE GERENCIAMENTO DE CHAVES ---

@admin_bp.route('/admin/keys/list/<int:product_id>', methods=['GET'])
def list_keys(product_id):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    # Pega chaves não usadas primeiro, depois as usadas
    keys = conn.execute('SELECT * FROM product_keys WHERE product_id = ? ORDER BY is_used ASC, id DESC', (product_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(k) for k in keys])

@admin_bp.route('/admin/keys/delete/<int:key_id>', methods=['POST'])
def delete_key(key_id):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM product_keys WHERE id = ?', (key_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# --- VENDAS MANUAIS (OFFLINE) ---

@admin_bp.route('/admin/sales/manual/add', methods=['POST'])
def add_manual_sale():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        unit_price = float(str(request.form.get('unit_price', 0)).replace('R$', '').replace(',', '.'))
        # cost_per_unit_brl can be provided by admin, but if not, calculate from product.cost_usd
        raw_cost = request.form.get('cost_per_unit_brl', '')
        if raw_cost is None or str(raw_cost).strip() == '':
            cost_per_unit_brl = 0.0
        else:
            cost_per_unit_brl = float(str(raw_cost).replace('R$', '').replace(',', '.'))
        notes = request.form.get('notes', '').strip()
        
        if not product_id or quantity <= 0 or unit_price <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        total_price = quantity * unit_price

        # If cost wasn't provided, compute from product.cost_usd and current dolar rate
        if not cost_per_unit_brl or cost_per_unit_brl <= 0:
            try:
                conn = get_db_connection()
                prod = conn.execute('SELECT cost_usd, apply_iof FROM products WHERE id = ?', (product_id,)).fetchone()
                conn.close()
                dolar_rate = get_dolar_hoje()
                IOF = 1.0638
                if prod:
                    cost_usd = float(prod['cost_usd'] or 0)
                    apply_iof = int(prod['apply_iof']) if 'apply_iof' in prod.keys() and prod['apply_iof'] is not None else 1
                    if cost_usd > 0:
                        if apply_iof == 1:
                            cost_per_unit_brl = round(cost_usd * dolar_rate * IOF, 2)
                        else:
                            cost_per_unit_brl = round(cost_usd * dolar_rate, 2)
            except Exception as e:
                # fallback: keep cost_per_unit_brl as 0
                print(f"Erro ao calcular custo automático: {e}")
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO manual_sales (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes) VALUES (?,?,?,?,?,?)',
            (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Venda manual registrada!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/sales/manual/list', methods=['GET'])
def list_manual_sales():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    # Pega vendas manuais com info do produto
    sales = conn.execute('''
        SELECT ms.*, p.name as product_name
        FROM manual_sales ms
        JOIN products p ON ms.product_id = p.id
        ORDER BY ms.created_at DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(s) for s in sales])


@admin_bp.route('/admin/product/info/<int:pid>', methods=['GET'])
def product_info(pid):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT id, cost_usd, apply_iof FROM products WHERE id = ?', (pid,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'error': '404'}), 404

        dolar_rate = get_dolar_hoje()
        IOF = 1.0638

        cost_usd = float(row['cost_usd'] or 0)
        apply_iof = int(row['apply_iof']) if 'apply_iof' in row.keys() and row['apply_iof'] is not None else 1

        calculated_cost_brl = 0.0
        if cost_usd > 0:
            if apply_iof == 1:
                calculated_cost_brl = round(cost_usd * dolar_rate * IOF, 2)
            else:
                calculated_cost_brl = round(cost_usd * dolar_rate, 2)

        return jsonify({
            'id': row['id'],
            'cost_usd': round(cost_usd, 2),
            'apply_iof': apply_iof,
            'dolar_rate': round(dolar_rate, 4),
            'calculated_cost_brl': calculated_cost_brl
        })
    except Exception as e:
        print(f"Erro product_info: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/sales/manual/delete/<int:sale_id>', methods=['POST'])
def delete_manual_sale(sale_id):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM manual_sales WHERE id = ?', (sale_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# --- RECARGAS DE PAINEL ---

@admin_bp.route('/admin/panel/recharge', methods=['POST'])
def add_panel_recharge():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    try:
        quantity = int(request.form.get('quantity', 0))
        cost_per_unit_usd = float(request.form.get('cost_per_unit_usd', 0))
        dolar_rate = float(request.form.get('dolar_rate', get_dolar_hoje()))
        notes = request.form.get('notes', '').strip()
        
        if quantity <= 0 or cost_per_unit_usd <= 0:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        total_cost_usd = quantity * cost_per_unit_usd
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO panel_recharges (quantity, cost_per_unit_usd, total_cost_usd, dolar_rate, notes) VALUES (?,?,?,?,?)',
            (quantity, cost_per_unit_usd, total_cost_usd, dolar_rate, notes)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Recarga de painel registrada!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/panel/recharge/list', methods=['GET'])
def list_panel_recharges():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    recharges = conn.execute('SELECT * FROM panel_recharges ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return jsonify([dict(r) for r in recharges])

@admin_bp.route('/admin/panel/recharge/delete/<int:recharge_id>', methods=['POST'])
def delete_panel_recharge(recharge_id):
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM panel_recharges WHERE id = ?', (recharge_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# --- RELATÓRIO DE VENDAS & LUCROS ---

@admin_bp.route('/admin/sales/report', methods=['GET'])
def sales_report():
    if not session.get('admin_logged_in'): return jsonify({'error': '401'}), 401
    
    dolar_hoje = get_dolar_hoje()
    IOF = 1.0638
    
    conn = get_db_connection()
    
    # Vendas Online (Mercado Pago)
    approved_orders = conn.execute('''
        SELECT SUM(CAST(REPLACE(REPLACE(amount, 'R$', ''), ',', '.') AS REAL)) as total,
               COUNT(*) as count
        FROM orders WHERE status = 'approved'
    ''').fetchone()
    
    online_revenue = float(approved_orders['total'] or 0) if approved_orders['total'] else 0
    online_count = approved_orders['count'] or 0
    
    # Vendas Manuais
    manual_sales = conn.execute('''
        SELECT SUM(total_price) as total, COUNT(*) as count
        FROM manual_sales
    ''').fetchone()
    
    manual_revenue = float(manual_sales['total'] or 0) if manual_sales['total'] else 0
    manual_count = manual_sales['count'] or 0
    
    # Custo de vendas online (produtos) - separar itens com/s/IOF
    online_costs = conn.execute('''
        SELECT 
            SUM(CASE WHEN p.apply_iof = 1 THEN p.cost_usd ELSE 0 END) as total_usd_iof,
            SUM(CASE WHEN p.apply_iof = 0 THEN p.cost_usd ELSE 0 END) as total_usd_noiof
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.status = 'approved'
    ''').fetchone()

    total_usd_iof = float(online_costs['total_usd_iof'] or 0) if online_costs['total_usd_iof'] else 0
    total_usd_noiof = float(online_costs['total_usd_noiof'] or 0) if online_costs['total_usd_noiof'] else 0

    online_cost_brl = (total_usd_iof * dolar_hoje * IOF) + (total_usd_noiof * dolar_hoje)
    
    # Custo de vendas manuais
    manual_costs = conn.execute('''
        SELECT SUM(cost_per_unit_brl * quantity) as total
        FROM manual_sales
    ''').fetchone()
    
    manual_cost_brl = float(manual_costs['total'] or 0) if manual_costs['total'] else 0
    
    # Custo de recargas de painel
    recharges = conn.execute('''
        SELECT SUM(total_cost_usd) as total_usd
        FROM panel_recharges
    ''').fetchone()
    
    total_recharged_usd = float(recharges['total_usd'] or 0) if recharges['total_usd'] else 0
    total_recharged_brl = total_recharged_usd * dolar_hoje * IOF
    
    conn.close()
    
    # Totais
    total_revenue = online_revenue + manual_revenue
    total_costs = online_cost_brl + manual_cost_brl + total_recharged_brl
    total_profit = total_revenue - total_costs
    
    return jsonify({
        'online': {
                'revenue': round(online_revenue, 2),
                'count': online_count,
                'cost_brl': round(online_cost_brl, 2),
                'cost_usd_with_iof': round(total_usd_iof, 2),
                'cost_usd_no_iof': round(total_usd_noiof, 2)
            },
        'manual': {
            'revenue': round(manual_revenue, 2),
            'count': manual_count,
            'cost_brl': round(manual_cost_brl, 2)
        },
        'panel': {
            'total_cost_usd': round(total_recharged_usd, 2),
            'total_cost_brl': round(total_recharged_brl, 2)
        },
        'summary': {
            'dolar_rate': round(dolar_hoje, 2),
            'total_revenue': round(total_revenue, 2),
            'total_costs': round(total_costs, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
        }
    })