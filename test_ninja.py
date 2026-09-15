import os
import sys
from dotenv import load_dotenv

# Carrega as variáveis do .env (onde o NINJA_API_TOKEN deve estar)
load_dotenv()

# Adiciona o diretório atual ao path para poder importar services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ninja_api import NinjaSellerApi, NinjaApiError

def test_ninja_api():
    print("Iniciando teste da API Ninja Engine...")
    
    token = os.environ.get("NINJA_API_TOKEN")
    if not token:
        print("[ERRO] NINJA_API_TOKEN nao encontrado no arquivo .env!")
        print("Adicione a linha NINJA_API_TOKEN=nj_sk_... no seu arquivo .env antes de rodar.")
        return

    api = NinjaSellerApi()
    
    # Vamos usar um jogo que (provavelmente) nao existe para testar a comunicacao
    # sem gastar o seu saldo (balance) real.
    import random
    import string
    
    # Criando um usuario unico para evitar conflitos na API
    test_user = "c_test_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    test_game = "8ball-pool"
    
    print(f"Token encontrado: {token[:8]}...{token[-4:]}")
    print(f"Tentando criar um acesso REAL para o jogo: '{test_game}'...")
    
    try:
        response = api.create_customer(
            username=test_user,
            password="TestPassword123Aa",
            game=test_game,
            mode="global",
            duration_seconds=259200  # 3 dias = 3 * 24 * 60 * 60
        )
        print("[SUCESSO] A API conectou e a chave/acesso foi CRIADA COM SUCESSO!")
        print(f"Resposta: {response}")
        
    except NinjaApiError as e:
        # Aqui analisamos o erro para saber se a comunicação está OK
        if e.status == 401:
            print("[ERRO] O token da API esta invalido ou incorreto (Erro 401).")
        elif e.status == 422:
            print("[OK] A API conectou e reconheceu o token.")
            print(f"O servidor recusou criar o acesso (o que era esperado por usarmos um jogo teste), retornando erro de validacao.")
            print(f"Mensagem da API: {e.message}")
        elif e.status == 404:
            print("[OK] A API conectou e reconheceu o token.")
            print(f"Mensagem da API (404): {e.message}")
        elif e.status == 403:
            print(f"[ERRO DE PERMISSAO]: {e.message}")
        else:
            print("[AVISO] RESPOSTA INESPERADA DA API. Status:", e.status)
            print("Detalhes:", e.message)
            print("Erros:", e.errors)
            
    except Exception as e:
        print(f"[ERRO DESCONHECIDO DE CONEXAO]: {e}")

if __name__ == "__main__":
    test_ninja_api()
