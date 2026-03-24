import sys
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path para conseguir importar 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.connection import get_db_path

def send_recovery_email(order, config):
    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    smtp_user = config['smtp_user']
    smtp_password = config['smtp_password']

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        print(f"[{datetime.now()}] Configuração SMTP incompleta. Abortando email para {order['customer_email']}.")
        return False

    msg = MIMEMultipart("alternative")
    msg['Subject'] = "Você esqueceu seu produto no carrinho! 🛒"
    msg['From'] = f"RAIO MODS <{smtp_user}>"
    msg['To'] = order['customer_email']

    # URL de continuação da compra
    # Se for PIX ou Cartão, a página /pedido/ORD-... consegue renderizar se estiver pending
    checkout_url = f"https://raiomodsgames.pythonanywhere.com/pedido/{order['external_reference']}"

    product_name = order['product_name'] or "Produto"
    
    html = f"""\
    <html>
      <body style="background-color: #050505; color: #fff; font-family: Arial, sans-serif; padding: 20px;">
        <div style="background-color: #111; border: 1px solid #333; border-radius: 8px; max-width: 600px; margin: 0 auto; padding: 30px; text-align: center;">
            <h1 style="color: #06b6d4;">RAIO MODS</h1>
            <h2 style="color: #fff;">Esqueceu algo no carrinho? 🤔</h2>
            <p style="color: #ccc; font-size: 16px; line-height: 1.5;">
                Olá, notamos que você tentou comprar <strong>{product_name}</strong> mas não finalizou o pagamento.
            </p>
            <p style="color: #ccc; font-size: 16px; line-height: 1.5;">
                Não se preocupe, salvamos seu pedido e ele ainda está disponível.
            </p>
            <div style="margin: 30px 0;">
                <a href="{checkout_url}" style="background-color: #06b6d4; color: #000; text-decoration: none; padding: 15px 30px; border-radius: 5px; font-weight: bold; font-size: 16px;">
                    FINALIZAR COMPRA
                </a>
            </div>
            <p style="color: #666; font-size: 12px;">Se você já pagou ou desistiu, basta ignorar este e-mail.</p>
        </div>
      </body>
    </html>
    """

    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, order['customer_email'], msg.as_string())
        server.quit()
        print(f"[{datetime.now()}] Email de recuperação enviado para {order['customer_email']}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Erro ao enviar email para {order['customer_email']}: {e}")
        return False

def run_recovery_job():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Busca a configuração SMTP
    config = cursor.execute('SELECT * FROM config WHERE id = 1').fetchone()
    if not config or not config['smtp_server']:
        print(f"[{datetime.now()}] Recuperação de carrinho desativada (SMTP não configurado).")
        conn.close()
        return

    # Busca pedidos pendentes criados entre 30 minutos e 24 horas atrás
    time_limit_upper = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
    time_limit_lower = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

    query = '''
        SELECT o.*, p.name as product_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.status = 'pending' 
          AND o.recovery_email_sent = 0
          AND o.created_at <= ?
          AND o.created_at >= ?
    '''
    
    abandoned_orders = cursor.execute(query, (time_limit_upper, time_limit_lower)).fetchall()
    
    print(f"[{datetime.now()}] Iniciando job de recuperação de carrinho. {len(abandoned_orders)} encontrados.")

    success_count = 0
    for order in abandoned_orders:
        if send_recovery_email(order, config):
            try:
                # Marca como enviado para não spammar o cliente
                cursor.execute('UPDATE orders SET recovery_email_sent = 1 WHERE id = ?', (order['id'],))
                conn.commit()
                success_count += 1
            except Exception as e:
                print(f"Erro ao atualizar bd para {order['id']}: {e}")

    print(f"[{datetime.now()}] Job finalizado. {success_count} emails enviados.")
    conn.close()

if __name__ == "__main__":
    run_recovery_job()
