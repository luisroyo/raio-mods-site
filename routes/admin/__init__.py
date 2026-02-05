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
from . import products as products_module
from . import keys as keys_module
from . import links as links_module
from . import sales as sales_module
from . import recharges as recharges_module
from . import config as config_module

admin_bp = Blueprint('admin', __name__)


# --- ROTA PRINCIPAL ---

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and session.get('admin_logged_in'):
        try:
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
                return redirect(url_for('admin.admin'))

            # Cálculos financeiros
            dolar_hoje = get_dolar_hoje()
            
            try:
                approved_orders = conn.execute('''
                    SELECT o.*, p.cost_usd, p.price, p.apply_iof
                    FROM orders o
                    JOIN products p ON o.product_id = p.id
                    WHERE o.status = 'approved'
                ''').fetchall()
            except sqlite3.OperationalError:
                approved_orders = conn.execute('''
                    SELECT o.*, p.cost_usd, p.price, 1 as apply_iof
                    FROM orders o
                    JOIN products p ON o.product_id = p.id
                    WHERE o.status = 'approved'
                ''').fetchall()
            
            faturamento_total = 0.0
            custo_vendas_total = 0.0
            
            for order in approved_orders:
                try:
                    amount = float(str(order['amount']).replace('R$', '').replace(',', '.').strip())
                    faturamento_total += amount
                except:
                    pass
                
                try:
                    cost_usd = float(order['cost_usd'] or 0)
                    if cost_usd > 0:
                        apply_iof = 1
                        try:
                            apply_iof = int(order['apply_iof']) if 'apply_iof' in order.keys() else 1
                        except:
                            apply_iof = 1

                        if apply_iof == 1:
                            custo_vendas_total += (cost_usd * dolar_hoje * IOF)
                        else:
                            custo_vendas_total += (cost_usd * dolar_hoje)
                except:
                    pass
            
            custo_fixo_painel_brl = CUSTO_FIXO_PAINEL_USD * dolar_hoje * IOF
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

            try:
                cached = _read_cache()
                if cached and 'ts' in cached:
                    financeiro['dolar_updated'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cached['ts']))
                else:
                    financeiro['dolar_updated'] = '---'
            except Exception:
                financeiro['dolar_updated'] = '---'
            
            catalogs, simple_products, subproducts_by_parent, subproducts_by_category, parent_products = [], [], {}, {}, []
            
            for p in all_products:
                p_dict = dict(p)
                p_dict['stock'] = stock_map.get(p['id'], 0)
                
                keys = p.keys()
                pid = p['parent_id'] if 'parent_id' in keys else None
                is_cat = p['is_catalog'] if 'is_catalog' in keys else 0

                if pid is None and (is_cat == 1 or p['id'] in legacy_catalog_ids):
                    parent_products.append(p_dict)

                if pid is None:
                    if is_cat == 1 or p['id'] in legacy_catalog_ids:
                        catalogs.append(p_dict)
                        if p['id'] not in subproducts_by_parent:
                            subproducts_by_parent[p['id']] = []
                        if p['id'] not in subproducts_by_category:
                            subproducts_by_category[p['id']] = {}
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


@admin_bp.route('/admin/debug/dolar', methods=['GET'])
def debug_dolar():
    if not session.get('admin_logged_in'):
        return jsonify({'error': '401'}), 401
    rate = get_dolar_hoje()
    cached = _read_cache()
    ts = cached.get('ts') if cached else time.time()
    return jsonify({'dolar_rate': round(rate, 4), 'timestamp': ts})


# --- ROTAS DE PRODUTOS ---
@admin_bp.route('/admin/add', methods=['POST'])
def add_product():
    return products_module.add_product()

@admin_bp.route('/admin/delete/<int:pid>', methods=['POST'])
def delete_product(pid):
    return products_module.delete_product(pid)

@admin_bp.route('/admin/edit/<int:pid>', methods=['POST'])
def edit_product(pid):
    return products_module.edit_product(pid)

@admin_bp.route('/admin/product/info/<int:pid>', methods=['GET'])
def product_info(pid):
    return products_module.product_info(pid)


# --- ROTA DE CONFIGURAÇÃO ---
@admin_bp.route('/admin/config', methods=['POST'])
def update_config():
    return config_module.update_config()


# --- ROTAS DE CHAVES ---
@admin_bp.route('/admin/keys/add', methods=['POST'])
def add_keys():
    return keys_module.add_keys()

@admin_bp.route('/admin/keys/list/<int:product_id>', methods=['GET'])
def list_keys(product_id):
    return keys_module.list_keys(product_id)

@admin_bp.route('/admin/keys/delete/<int:key_id>', methods=['POST'])
def delete_key(key_id):
    return keys_module.delete_key(key_id)


# --- ROTAS DE LINKS ---
@admin_bp.route('/admin/links/add', methods=['POST'])
def add_link():
    return links_module.add_link()

@admin_bp.route('/admin/links/delete/<int:lid>', methods=['POST'])
def delete_link(lid):
    return links_module.delete_link(lid)

@admin_bp.route('/admin/links/edit/<int:lid>', methods=['POST'])
def edit_link(lid):
    return links_module.edit_link(lid)


# --- ROTAS DE VENDAS MANUAIS ---
@admin_bp.route('/admin/sales/manual/add', methods=['POST'])
def add_manual_sale():
    return sales_module.add_manual_sale()

@admin_bp.route('/admin/sales/manual/list', methods=['GET'])
def list_manual_sales():
    return sales_module.list_manual_sales()

@admin_bp.route('/admin/sales/manual/edit/<int:sale_id>', methods=['POST'])
def edit_manual_sale(sale_id):
    return sales_module.edit_manual_sale(sale_id)

@admin_bp.route('/admin/sales/manual/delete/<int:sale_id>', methods=['POST'])
def delete_manual_sale(sale_id):
    return sales_module.delete_manual_sale(sale_id)

@admin_bp.route('/admin/sales/report', methods=['GET'])
def sales_report():
    return sales_module.sales_report()


# --- ROTAS DE RECARGAS ---
@admin_bp.route('/admin/panel/recharge', methods=['POST'])
def add_panel_recharge():
    return recharges_module.add_panel_recharge()

@admin_bp.route('/admin/panel/recharge/list', methods=['GET'])
def list_panel_recharges():
    return recharges_module.list_panel_recharges()

@admin_bp.route('/admin/panel/recharge/delete/<int:recharge_id>', methods=['POST'])
def delete_panel_recharge(recharge_id):
    return recharges_module.delete_panel_recharge(recharge_id)
