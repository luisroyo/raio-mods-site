"""
Importar vendas manuais históricas de um CSV para a tabela `manual_sales`.

Colunas do CSV (primeira linha = cabeçalho, obrigatório):
  - product_name: nome do produto (ex: "HACK KOS PREMIUM 7 DIAS")
      OU
    product_id: ID numérico do produto
  - quantity: quantidade vendida (ex: 1, 2)
  - unit_price: preço de venda unitário em R$ (ex: 39.90)
  - cost_per_unit_brl: custo unitário em R$ (ex: 25.00) — opcional
  - notes: observações (ex: "Venda antiga do cliente") — opcional
  - created_at: data/hora no formato YYYY-MM-DD HH:MM:SS (ex: 2026-01-15 14:30:00) — opcional

Exemplo de CSV:
product_name,quantity,unit_price,cost_per_unit_brl,notes,created_at
HACK KOS PREMIUM 7 DIAS,2,39.90,25.00,"Cliente João",2026-02-03 14:30:00
FREE FIRE,1,17.90,10.50,"Venda loja",2026-01-15 10:00:00

Uso:
  python import_manual_sales.py path/to/vendas.csv

Segurança:
  - Sempre faça backup de `database.db` antes de executar!
  - Você pode executar em produção; o script apenas insere dados.
"""
import csv
import sys
import time
import requests
from database.models import get_db_connection

IOF = 1.0638

AWESOME_API = 'https://economia.awesomeapi.com.br/last/USD-BRL'


def fetch_dolar_rate():
    try:
        r = requests.get(AWESOME_API, timeout=6)
        if r.status_code == 200:
            jd = r.json()
            if 'USDBRL' in jd:
                return float(jd['USDBRL']['bid'])
    except Exception as e:
        print('Warning: failed to fetch dolar rate:', e)
    return None


def find_product_by_name(conn, name):
    row = conn.execute('SELECT id FROM products WHERE name = ?', (name,)).fetchone()
    return row['id'] if row else None


def main(csv_path):
    print('Abrindo banco de dados...')
    conn = get_db_connection()
    cur = conn.cursor()

    rate = fetch_dolar_rate()
    if rate:
        print(f'Usando cotação USD-BRL: {rate:.4f}')
    else:
        print('Cotação não disponível; custo será usado como informado ou 0 se vazio')

    inserted = 0
    skipped = 0
    
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # Tentar obter product_id
            product_id = None
            
            # Tentar coluna product_id primeiro
            pid_str = (row.get('product_id') or '').strip()
            if pid_str != '':
                try:
                    product_id = int(pid_str)
                except:
                    print(f"Linha {i}: product_id '{pid_str}' inválido (esperava número). Tentando buscar por nome...")
            
            # Se não conseguiu, tentar buscar por product_name
            if product_id is None:
                pname = (row.get('product_name') or '').strip()
                if pname:
                    product_id = find_product_by_name(conn, pname)
                    if product_id is None:
                        print(f"Linha {i}: produto '{pname}' não encontrado no banco. Pulando.")
                        skipped += 1
                        continue
                else:
                    print(f"Linha {i}: nenhum product_id ou product_name fornecido. Pulando.")
                    skipped += 1
                    continue

            # Validar dados obrigatórios
            try:
                quantity = int(row.get('quantity', '1') or 1)
                if quantity <= 0:
                    raise ValueError("quantity deve ser > 0")
            except Exception as e:
                print(f"Linha {i}: quantidade inválida ({row.get('quantity')}). {e}. Pulando.")
                skipped += 1
                continue

            try:
                unit_price = float(str(row.get('unit_price', '0') or 0).replace(',', '.'))
                if unit_price <= 0:
                    raise ValueError("unit_price deve ser > 0")
            except Exception as e:
                print(f"Linha {i}: preço inválido ({row.get('unit_price')}). {e}. Pulando.")
                skipped += 1
                continue

            # cost_per_unit_brl (opcional)
            raw_cost = (row.get('cost_per_unit_brl') or '').strip()
            cost_per_unit_brl = 0.0
            if raw_cost != '':
                try:
                    cost_per_unit_brl = float(str(raw_cost).replace(',', '.'))
                    if cost_per_unit_brl < 0:
                        cost_per_unit_brl = 0.0
                except Exception as e:
                    print(f"Linha {i}: custo inválido ({raw_cost}). Usando 0.0. {e}")
                    cost_per_unit_brl = 0.0
            
            notes = (row.get('notes') or '').strip()
            created_at = (row.get('created_at') or '').strip() or None
            total_price = round(quantity * unit_price, 2)

            try:
                cur.execute(
                    'INSERT INTO manual_sales (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes, created_at) VALUES (?,?,?,?,?,?,?)',
                    (product_id, quantity, unit_price, cost_per_unit_brl, total_price, notes, created_at)
                )
                inserted += 1
                print(f"Linha {i}: OK - {quantity}x {row.get('product_name', f'ID:{product_id}')} = R$ {total_price:.2f}")
            except Exception as e:
                print(f"Linha {i}: erro ao inserir. {e}. Pulando.")
                skipped += 1
                continue

    conn.commit()
    conn.close()
    print(f'\n✅ Importação concluída: {inserted} inseridas, {skipped} puladas.')



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python import_manual_sales.py path/to/sales.csv')
        sys.exit(1)
    main(sys.argv[1])
