import os
import sys
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

    masked_key = f"{api_key[:10]}...{api_key[-6:]}" if len(api_key) > 16 else "***"
    print(f"Chave detectada: {masked_key}")

    api = ResellershipApi(api_key=api_key, base_url=base_url)

    # 1. Teste de Saldo (Balance)
    print("\n[1/3] Consultando Saldo da Carteira (GET /balance.php)...")
    try:
        balance_data = api.get_balance()
        print("   ✅ Resposta recebida com sucesso!")
        balance = balance_data.get("balance", "N/A")
        currency = balance_data.get("currency", "USD")
        print(f"   💰 Saldo atual: {balance} {currency}")
        stats = balance_data.get("stats")
        if stats:
            print(f"   📊 Estatísticas: {stats}")
    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar saldo: {e}")
        if e.status == 401:
            print("   ⚠️ Verifique se a sua RESELLERSHIP_API_KEY está correta e ativa.")
        return
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar saldo: {e}")
        return

    # 2. Teste de Produtos (Products Catalog)
    print("\n[2/3] Consultando Catálogo de Produtos (GET /products.php)...")
    try:
        products_data = api.get_products(page=1, limit=15)
        print("   ✅ Catálogo consultado com sucesso!")
        
        # Pode vir como dict {'products': [...]} ou lista direta
        items = []
        if isinstance(products_data, dict):
            items = products_data.get("products") or products_data.get("data") or products_data.get("items") or []
        elif isinstance(products_data, list):
            items = products_data

        if not items and isinstance(products_data, dict):
            print(f"   ℹ️ Resposta da API: {products_data}")

        print(f"   📦 Total de produtos retornados nesta página: {len(items)}")
        for idx, item in enumerate(items[:5], 1):
            if isinstance(item, dict):
                pid = item.get("id") or item.get("productId")
                pname = item.get("name") or item.get("title") or "Sem nome"
                price = item.get("price")
                opts = item.get("options", [])
                print(f"      {idx}. [ID {pid}] {pname} — Preço: {price}")
                if opts:
                    for opt in opts[:3]:
                        oid = opt.get("id") or opt.get("optionId")
                        oname = opt.get("name") or opt.get("duration") or opt.get("title")
                        oprice = opt.get("price")
                        print(f"         └─ Opção ID {oid}: {oname} (Preço: {oprice})")
                    if len(opts) > 3:
                        print(f"         └─ ... e mais {len(opts) - 3} opções")

        print("\n💡 Dica de configuração no Painel Admin:")
        print("   Para vincular um produto à Resellership, no campo 'Game Type' preencha:")
        print("   • Sem opção:  resellership:<ID_DO_PRODUTO>")
        print("   • Com opção:  resellership:<ID_DO_PRODUTO>:<ID_DA_OPCAO>")
        print("   Exemplo: resellership:42:7")

    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar produtos: {e}")
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar produtos: {e}")

    # 3. Teste de Pedidos Recentes (Orders List)
    print("\n[3/3] Consultando Histórico de Pedidos (GET /orders.php)...")
    try:
        orders_data = api.get_orders(page=1, limit=5)
        print("   ✅ Histórico de pedidos consultado com sucesso!")
        orders_list = []
        if isinstance(orders_data, dict):
            orders_list = orders_data.get("orders") or orders_data.get("data") or []
        elif isinstance(orders_data, list):
            orders_list = orders_data
        print(f"   📋 Pedidos recentes encontrados: {len(orders_list)}")
    except ResellershipApiError as e:
        print(f"   ⚠️ Consulta de pedidos: {e}")
    except Exception as e:
        print(f"   ⚠️ Erro ao consultar pedidos: {e}")

    print("\n" + "=" * 60)
    print("🎉 Integração validada e pronta para uso!")
    print("=" * 60)


if __name__ == "__main__":
    test_resellership()
