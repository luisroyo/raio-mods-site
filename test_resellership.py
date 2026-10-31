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
        products_data = api.get_products(page=1, limit=50)
        print("   ✅ Catálogo consultado com sucesso!")
        
        # Mostra o formato real retornado pela API
        print("\n--- [JSON BRUTO DOS PRODUTOS] ---")
        print(json.dumps(products_data, indent=2, ensure_ascii=False)[:3000])
        print("--- [FIM DO JSON] ---\n")

    except ResellershipApiError as e:
        print(f"   ❌ Erro ao consultar produtos: {e}")
    except Exception as e:
        print(f"   ❌ Falha inesperada ao consultar produtos: {e}")

    # 3. Teste de Histórico de Pedidos (Orders List)
    print("\n[3/3] Consultando Histórico de Pedidos (GET /orders.php)...")
    try:
        orders_data = api.get_orders(page=1, limit=5)
        print("   ✅ Histórico de pedidos consultado com sucesso!")
        
        print("\n--- [JSON BRUTO DOS PEDIDOS] ---")
        print(json.dumps(orders_data, indent=2, ensure_ascii=False)[:2000])
        print("--- [FIM DO JSON PEDIDOS] ---\n")

    except ResellershipApiError as e:
        print(f"   ⚠️ Consulta de pedidos: {e}")
    except Exception as e:
        print(f"   ⚠️ Erro ao consultar pedidos: {e}")

    print("=" * 60)
    print("🎉 Integração validada e pronta para uso!")
    print("=" * 60)


if __name__ == "__main__":
    test_resellership()
