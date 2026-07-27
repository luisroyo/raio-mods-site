"""
Repositório Mock de Produtos.
Será substituído futuramente por consultas ao banco de dados.
"""

PRODUCTS = {
    "kos_virtual": {
        "id": "kos_virtual",
        "name": "KOS Virtual Premium",
        "description": "Acesso premium ao KOS Virtual com todos os recursos liberados.",
        "url": "https://raiomodsgames.pythonanywhere.com/catalogo/46",
        "image": "kos_virtual.jpg", # Placeholder para envio futuro
        "plans": [
            {"duration": "1 Dia", "price": 10.00},
            {"duration": "7 Dias", "price": 25.00},
            {"duration": "15 Dias", "price": 40.00},
            {"duration": "30 Dias", "price": 60.00}
        ]
    },
    "kos_apk": {
        "id": "kos_apk",
        "name": "KOS APK Mod",
        "description": "Modificação exclusiva em formato APK. Mais seguro e direto.",
        "url": "https://raiomodsgames.pythonanywhere.com/catalogo",
        "image": "kos_apk.jpg",
        "plans": [
            {"duration": "7 Dias", "price": 30.00},
            {"duration": "30 Dias", "price": 70.00}
        ]
    },
    "ninja": {
        "id": "ninja",
        "name": "Ninja",
        "description": "Funções avançadas e camuflagem para garantir máxima diversão.",
        "url": "https://raiomodsgames.pythonanywhere.com/catalogo",
        "image": "ninja.jpg",
        "plans": [
            {"duration": "30 Dias", "price": 50.00}
        ]
    },
    "aim_king": {
        "id": "aim_king",
        "name": "Aim King",
        "description": "O rei da precisão. Precisão absoluta em todas as partidas.",
        "url": "https://raiomodsgames.pythonanywhere.com/catalogo",
        "image": "aim_king.jpg",
        "plans": [
            {"duration": "15 Dias", "price": 35.00},
            {"duration": "30 Dias", "price": 55.00}
        ]
    }
}
