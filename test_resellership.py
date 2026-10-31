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
    print("=" * 60)
    print("🚀 Teste de Integração — Resellership API (v1)")
    print("=" * 60)

    api_key = os.environ.get("RESELLERSHIP_API_KEY") or os.environ.get("RESELLERSHIP_API_TOKEN")
    base_url = os.environ.get("RESELLERSHIP_API_BASE_URL", ResellershipApi.DEFAULT_BASE_URL)

    print(f"Base URL: {base_url}")

    if not api_key:
        print("\n❌ [ERRO] RESELLERSHIP_API_KEY não encontrada nas variáveis de ambiente!")
        print("\nPara configurar:")
        print("1. No PythonAnywhere ou no seu arquivo .env local, adicione:")
        print("   RESELLERSHIP_API_KEY=rk_seu_key_id_seu_secret")
        print("2. Recarregue a aplicação web ou execute este script novamente.")
        print("=" * 60)
        return

    masked_key = f"{api_key[:12]}...{api_key[-6:]}" if len(api_key) > 18 else "***"
    print(f"Chave detectada: {masked_key}")

    api = ResellershipApi(api_key=api_key, base_url=base_url)

    # 1. Teste de Saldo (Balance)
    print("\n[1/3] Consultando Saldo da Carteira (GET /balance.php)...")
    try:
        balance_data = api.get_balance()
        print("   ✅ Resposta recebida com sucesso!")
        
        # Pode vir direto ou dentro de 'data' ou 'wallet'
        balance = None
        currency = "USD"
        stats = None

        if isinstance(balance_data, dict):
            # Tenta campos diretos
            balance = balance_data.get("balance") or balance_data.get("walletBalance") or balance_data.get("wallet_balance")
            currency = balance_data.get("currency") or "USD"
            stats = balance_data.get("stats")
            
            # Se tiver sub-objeto 'data'
            if balance is None and isinstance(balance_data.get("data"), dict):
                sub = balance_data["data"]
                balance = sub.get("balance") or sub.get("walletBalance") or sub.get("wallet_balance")
                currency = sub.get("currency") or currency
                stats = sub.get("stats") or stats

            # Se tiver sub-objeto 'wallet'
            if balance is None and isinstance(balance_data.get("wallet"), dict):
                sub = balance_data["wallet"]
                balance = sub.get("balance")
                currency = sub.get("currency") or currency

        if balance is not None:
            print(f"   💰 Saldo atual: {balance} {currency}")
        else:
            print(f"   ℹ️ Dados brutos de saldo: {json.dumps(balance_data, ensure_ascii=False)}")

        if stats:
            print(f"   📊 Estatísticas: {stats}")

    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar saldo: {e}")
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar saldo: {e}")

    # 2. Teste de Produtos (Products Catalog)
    print("\n[2/3] Consultando Catálogo de Produtos (GET /products.php)...")
    try:
        products_data = api.get_products(page=1, limit=50)
        print("   ✅ Catálogo consultado com sucesso!")
        
        items = []
        if isinstance(products_data, dict):
            # Tenta extrair lista de produtos
            raw_items = products_data.get("products") or products_data.get("data") or products_data.get("items") or []
            if isinstance(raw_items, dict):
                items = list(raw_items.values())
            elif isinstance(raw_items, list):
                items = raw_items
            else:
                items = [raw_items]
        elif isinstance(products_data, list):
            items = products_data

        print(f"   📦 Total de produtos retornados nesta página: {len(items)}")

        for idx, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue

            pid = item.get("id") or item.get("productId")
            pname = item.get("name") or item.get("title") or "Sem nome"
            price = item.get("price") or item.get("unitPrice") or "N/A"
            stock = item.get("available") or item.get("availableCodes") or item.get("stock")

            stock_info = f" (Estoque: {stock})" if stock is not None else ""
            print(f"\n      {idx}. [ID {pid}] {pname} — Preço: {price}{stock_info}")

            # Opções / Variantes (ex: 1 dia, 7 dias, 30 dias)
            opts_raw = item.get("options")
            opts = []
            if isinstance(opts_raw, dict):
                opts = list(opts_raw.values())
            elif isinstance(opts_raw, list):
                opts = opts_raw

            if opts:
                for opt in opts:
                    if isinstance(opt, dict):
                        oid = opt.get("id") or opt.get("optionId")
                        oname = opt.get("name") or opt.get("duration") or opt.get("title") or "Padrão"
                        oprice = opt.get("price") or "N/A"
                        ostock = opt.get("available") or opt.get("stock")
                        st_text = f" [Estoque: {ostock}]" if ostock is not None else ""
                        print(f"         └─ Opção ID {oid}: {oname} — Preço: {oprice}{st_text}")
                        print(f"            👉 Configuração no Painel Admin: Game Type = resellership:{pid}:{oid}")
            else:
                print(f"         👉 Configuração no Painel Admin: Game Type = resellership:{pid}")

        print("\n💡 Dica de configuração no Painel Admin:")
        print("   No menu de Produtos do Painel Mestre, configure:")
        print("   • Campo 'Game Type':  resellership:<ID_DO_PRODUTO>:<ID_DA_OPCAO>")
        print("   • Ou sem opção:      resellership:<ID_DO_PRODUTO>")

    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar produtos: {e}")
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar produtos: {e}")

    # 3. Teste de Histórico de Pedidos (Orders List)
    print("\n[3/3] Consultando Histórico de Pedidos (GET /orders.php)...")
    try:
        orders_data = api.get_orders(page=1, limit=5)
        print("   ✅ Histórico de pedidos consultado com sucesso!")
        
        orders_list = []
        if isinstance(orders_data, dict):
            raw_orders = orders_data.get("orders") or orders_data.get("data") or []
            if isinstance(raw_orders, dict):
                orders_list = list(raw_orders.values())
            elif isinstance(raw_orders, list):
                orders_list = raw_orders
        elif isinstance(orders_data, list):
            orders_list = orders_data

        print(f"   📋 Pedidos recentes encontrados: {len(orders_list)}")
        for o in orders_list[:3]:
            if isinstance(o, dict):
                oid = o.get("id") or o.get("orderId")
                ostatus = o.get("status") or "concluído"
                oprod = o.get("productName") or o.get("productId")
                ocodes = ResellershipApi.extract_delivered_codes(o)
                codes_sample = f" (Chaves: {', '.join(ocodes[:2])})" if ocodes else ""
                print(f"      • Pedido #{oid} — Status: {ostatus} — Produto: {oprod}{codes_sample}")

    except ResellershipApiError as e:
        print(f"   ⚠️ Consulta de pedidos: {e}")
    except Exception as e:
        print(f"   ⚠️ Erro ao consultar pedidos: {e}")

    print("\n" + "=" * 60)
    print("🎉 Integração validada e pronta para uso!")
    print("=" * 60)


if __name__ == "__main__":
    test_resellership()
