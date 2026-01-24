import os

import psycopg2
from dotenv import load_dotenv


def init_db():
    """
    Inicializa a tabela no PostgreSQL.
    É idempotente (CREATE TABLE IF NOT EXISTS), então não quebra em reinícios.
    """
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL não configurada. Defina no .env (Neon PostgreSQL).")

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price TEXT NOT NULL,
                    image TEXT NOT NULL,
                    category TEXT NOT NULL
                );
                """
            )

            # Exemplo de inserção para teste (não duplica ao reiniciar)
            cursor.execute(
                """
                INSERT INTO products (id, name, description, price, image, category)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (1, "8 Ball Pool VIP", "Linhas longas e antecipação de jogada.", "R$ 49,90", "8ball.jpg", "Mod"),
            )

        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()