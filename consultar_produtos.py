import os
import sys
import json
from dotenv import load_dotenv

# Configura UTF-8 seguro
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.resellership_api import ResellershipApi, ResellershipApiError


def buscar_produtos():
    termo = " ".join(sys.argv[1:]).strip().lower() if len(sys.argv) > 1 else ""

    api_key = os.environ.get("RESELLERSHIP_API_KEY") or os.environ.get("RESELLERSHIP_API_TOKEN")
    if not api_key:
        print("❌ RESELLERSHIP_API_KEY não configurada no .env")
        return

    api = ResellershipApi()

    print("=" * 70)
    if termo:
        print(f"🔍 Buscando produtos na Resellership com o termo: '{termo}'...")
    else:
        print("📦 Listando todos os produtos disponíveis na Resellership...")
    print("=" * 70)

    # Coletar produtos de todas as páginas
    todos_produtos = []
    page = 1
    total_pages = 1

    try:
        while page <= total_pages:
            resp = api.get_products(page=page, limit=100)
            data = resp.get("data") if isinstance(resp.get("data"), dict) else resp

            prods = data.get("products", []) if isinstance(data, dict) else []
            if isinstance(prods, list):
                todos_produtos.extend(prods)

            pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
            total_pages = pagination.get("totalPages") or 1
            if not prods:
                break
            page += 1

    except ResellershipApiError as e:
        print(f"❌ Erro ao consultar a API: {e}")
        return
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return

    if not todos_produtos:
        print("Nenhum produto encontrado no catálogo do seu fornecedor.")
        return

    # Filtrar se houver termo de busca
    if termo:
        filtrados = [
            p for p in todos_produtos
            if termo in (p.get("name") or "").lower() or termo in str(p.get("id"))
        ]
    else:
        filtrados = todos_produtos

    if not filtrados:
        print(f"Nenhum produto encontrado contendo '{termo}'.")
        print("\nSugestões:")
        print("• Tente buscar uma palavra menor (ex: 'aim' ou 'blood').")
        print("• Execute sem parâmetros para listar todos: python consultar_produtos.py")
        return

    print(f"\nForam encontrados {len(filtrados)} produto(s):\n")

    for idx, prod in enumerate(filtrados, 1):
        pid = prod.get("id")
        pname = prod.get("name") or "Sem Nome"
        pcurr = prod.get("currency", "USD")
        ptotal_stock = prod.get("availableCodes")
        stk_str = f" | Estoque total: {ptotal_stock}" if ptotal_stock is not None else ""

        print(f"┌───────────────────────────────────────────────────────────────────")
        print(f"│ 🎮 [{idx}] {pname} (Produto ID: {pid}){stk_str}")
        print(f"├───────────────────────────────────────────────────────────────────")

        options = prod.get("options", [])
        if options and isinstance(options, list):
            print(f"│ Planos / Opções disponíveis:")
            for opt in options:
                oid = opt.get("id")
                label = opt.get("label") or opt.get("name") or "Padrão"
                price = opt.get("price")
                days = opt.get("durationDays")
                dur_str = f" ({days} dias)" if days else ""
                ostk = opt.get("availableCodes")
                ostk_str = f" | Estoque: {ostk}" if ostk is not None else ""

                print(f"│   └─ [{label}{dur_str}] Preço: {price} {pcurr}{ostk_str}")
                print(f"│      👉 Código para o Painel Admin: resellership:{pid}:{oid}")
        else:
            base_price = prod.get("price")
            print(f"│ Preço: {base_price} {pcurr}")
            print(f"│ 👉 Código para o Painel Admin: resellership:{pid}")

        print(f"└───────────────────────────────────────────────────────────────────\n")

    print("=" * 70)
    print("💡 Como usar no Painel Admin (Produtos -> Adicionar/Editar):")
    print("   Copie o código 'resellership:PRODUTO:OPCAO' e cole no campo 'Game Type'.")
    print("=" * 70)


if __name__ == "__main__":
    buscar_produtos()

