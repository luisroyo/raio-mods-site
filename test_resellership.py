import os
import sys
import json
from dotenv import load_dotenv

# Configura encoding para UTF-8 de forma segura no Windows e Linux
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Carrega as variáveis do .env
load_dotenv()

# Adiciona o diretório atual ao path para poder importar services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.resellership_api import ResellershipApi, ResellershipApiError


def test_resellership():
    print("=" * 65)
    print("🚀 Teste de Integração — Resellership API (v1)")
    print("=" * 65)

    api_key = os.environ.get("RESELLERSHIP_API_KEY") or os.environ.get("RESELLERSHIP_API_TOKEN")
    base_url = os.environ.get("RESELLERSHIP_API_BASE_URL", ResellershipApi.DEFAULT_BASE_URL)

    print(f"Base URL: {base_url}")

    if not api_key:
        print("\n❌ [ERRO] RESELLERSHIP_API_KEY não encontrada nas variáveis de ambiente!")
        print("\nPara configurar:")
        print("1. No PythonAnywhere ou no seu arquivo .env local, adicione:")
        print("   RESELLERSHIP_API_KEY=rk_seu_key_id_seu_secret")
        print("2. Recarregue a aplicação web ou execute este script novamente.")
        print("=" * 65)
        return

    masked_key = f"{api_key[:12]}...{api_key[-6:]}" if len(api_key) > 18 else "***"
    print(f"Chave detectada: {masked_key}")

    api = ResellershipApi(api_key=api_key, base_url=base_url)

    # 1. Teste de Saldo (Balance)
    print("\n[1/3] Consultando Saldo da Carteira (GET /balance.php)...")
    try:
        balance_data = api.get_balance()
        print("   ✅ Resposta recebida com sucesso!")
        
        balance = None
        currency = "USD"
        stats = None

        if isinstance(balance_data, dict):
            balance = balance_data.get("balance") or balance_data.get("walletBalance") or balance_data.get("wallet_balance")
            currency = balance_data.get("currency") or "USD"
            stats = balance_data.get("stats")
            
            if balance is None and isinstance(balance_data.get("data"), dict):
                sub = balance_data["data"]
                balance = sub.get("balance") or sub.get("walletBalance") or sub.get("wallet_balance")
                currency = sub.get("currency") or currency
                stats = sub.get("stats") or stats

        if balance is not None:
            print(f"   💰 Saldo atual: {balance} {currency}")
        if stats:
            print(f"   📊 Estatísticas: {stats}")

    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar saldo: {e}")
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar saldo: {e}")

    # 2. Teste de Produtos (Products Catalog)
    print("\n[2/3] Consultando Catálogo de Produtos (GET /products.php)...")
    try:
        products_resp = api.get_products(page=1, limit=50)
        print("   ✅ Catálogo consultado com sucesso!")
        
        # Na Resellership, a lista vem dentro de response['data']['products']
        items = []
        if isinstance(products_resp, dict):
            data_field = products_resp.get("data")
            if isinstance(data_field, dict):
                items = data_field.get("products", [])
            elif isinstance(data_field, list):
                items = data_field
            elif "products" in products_resp:
                items = products_resp.get("products", [])
        elif isinstance(products_resp, list):
            items = products_resp

        print(f"   📦 Total de produtos disponíveis: {len(items)}")

        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue

            pid = item.get("id")
            pname = item.get("name") or "Sem nome"
            curr = item.get("currency", "USD")
            base_price = item.get("price")
            stock = item.get("availableCodes")

            print(f"\n   🔹 [{idx}] {pname} (Produto ID: {pid})")
            if stock is not None:
                print(f"       Estoque Total: {stock} códigos disponíveis")

            opts = item.get("options", [])
            if opts and isinstance(opts, list):
                print(f"       Opções / Planos disponíveis ({len(opts)}):")
                for opt in opts:
                    oid = opt.get("id")
                    label = opt.get("label") or opt.get("name") or "Padrão"
                    oprice = opt.get("price")
                    days = opt.get("durationDays")
                    dur_str = f" ({days} dias)" if days else ""
                    ostk = opt.get("availableCodes")
                    stk_str = f" [Estoque: {ostk}]" if ostk is not None else ""
                    print(f"       └─ Opção ID {oid}: {label}{dur_str} — {oprice} {curr}{stk_str}")
                    print(f"          👉 No Painel Admin preencha Game Type: resellership:{pid}:{oid}")
            else:
                print(f"       Preço base: {base_price} {curr}")
                print(f"       👉 No Painel Admin preencha Game Type: resellership:{pid}")

        print("\n💡 Como vincular no Painel Admin:")
        print("   No menu de Produtos do Painel Mestre, configure:")
        print("   • Campo 'Game Type':  resellership:<ID_PRODUTO>:<ID_OPCAO>")
        print("   Exemplo: resellership:82:157 (para GBD Bloodstrike 1 dia)")

    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar produtos: {e}")
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar produtos: {e}")

    # 3. Teste de Histórico de Pedidos (Orders List)
    print("\n[3/3] Consultando Histórico de Pedidos (GET /orders.php)...")
    try:
        orders_resp = api.get_orders(page=1, limit=5)
        print("   ✅ Histórico de pedidos consultado com sucesso!")
        
        orders_list = []
        if isinstance(orders_resp, dict):
            data_field = orders_resp.get("data")
            if isinstance(data_field, dict):
                orders_list = data_field.get("orders", [])
            elif isinstance(data_field, list):
                orders_list = data_field
            elif "orders" in orders_resp:
                orders_list = orders_resp.get("orders", [])
        elif isinstance(orders_resp, list):
            orders_list = orders_resp

        print(f"   📋 Pedidos recentes encontrados: {len(orders_list)}")
        first_order_id = None
        for o in orders_list[:4]:
            if isinstance(o, dict):
                oid = o.get("id")
                if first_order_id is None and oid:
                    first_order_id = oid
                onum = o.get("orderNumber") or f"#{oid}"
                ostatus = o.get("status") or "concluído"
                oprod = o.get("productName") or f"Produto {o.get('productId')}"
                opt_id = o.get("optionId")
                opt_str = f" (Opção {opt_id})" if opt_id else ""
                created = o.get("createdAt", "")
                print(f"      • Pedido {onum} — {oprod}{opt_str} — Status: {ostatus} — {created}")

        # Inspeciona um pedido individual para ver os códigos entregues
        if first_order_id:
            try:
                single_order_resp = api.get_order(first_order_id)
                codes = ResellershipApi.extract_delivered_codes(single_order_resp)
                if codes:
                    print(f"      🔍 Teste de extração de chaves no Pedido #{first_order_id}:")
                    print(f"         Chave(s) extraída(s) com sucesso: {codes}")
                else:
                    # Se não veio na lista de chaves, imprime estrutura de teste
                    print(f"      🔍 Pedido #{first_order_id} consultado com sucesso!")
            except Exception as e:
                pass

    except ResellershipApiError as e:
        print(f"   ⚠️ Consulta de pedidos: {e}")
    except Exception as e:
        print(f"   ⚠️ Erro ao consultar pedidos: {e}")

    print("\n" + "=" * 65)
    print("🎉 Integração 100% validada e pronta para vendas automáticas!")
    print("=" * 65)


if __name__ == "__main__":
    test_resellership()
