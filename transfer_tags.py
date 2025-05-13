import sqlite3

def update_tagId():
    try:
        # Conecte-se ao banco de dados Cronos.db
        connection = sqlite3.connect('Cronos.db')
        cursor = connection.cursor()

        # Selecione todas as linhas da tabela Atletas
        cursor.execute("SELECT rowid FROM Atletas")
        rows = cursor.fetchall()

        # Atualize a coluna tagId com valores sequenciais
        for index, row in enumerate(rows, start=1):
            cursor.execute("UPDATE Atletas SET tagId = ? WHERE rowid = ?", (index, row[0]))

        # Salve as alterações no banco de dados
        connection.commit()
        print("Atualização concluída com sucesso!")

    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")

    finally:
        # Feche a conexão com o banco de dados
        if connection:
            connection.close()

# Execute o script
if __name__ == "__main__":
    update_tagId()