import os

import mysql.connector
from mysql.connector import Error


def obter_conexao():
    """Cria uma conexão MySQL usando exclusivamente variáveis de ambiente."""
    campos = {
        "MYSQL_HOST": os.getenv("MYSQL_HOST"),
        "MYSQL_USER": os.getenv("MYSQL_USER"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
    }
    ausentes = [nome for nome, valor in campos.items() if not valor]
    if ausentes:
        print(
            "Configuração de banco incompleta. Variáveis ausentes: "
            + ", ".join(ausentes)
        )
        return None

    try:
        return mysql.connector.connect(
            host=campos["MYSQL_HOST"],
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=campos["MYSQL_USER"],
            password=campos["MYSQL_PASSWORD"],
            database=campos["MYSQL_DATABASE"],
            charset="utf8mb4",
            use_unicode=True,
            raise_on_warnings=True,
        )
    except (Error, ValueError) as erro:
        print(f"Erro ao conectar ao banco de dados: {erro}")
        return None
