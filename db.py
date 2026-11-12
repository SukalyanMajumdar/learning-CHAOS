
import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

load_dotenv()


def get_connection():
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    register_vector(conn)

    return conn


if __name__ == "__main__":
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print("Database:", cur.fetchone()[0])

            cur.execute(
                "SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector;"
            )
            print("Vector distance:", cur.fetchone()[0])

    print("Oracle database connection successful!")
