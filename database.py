import sqlite3

def initialize_db():
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()

    # Create table for storing documents
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        content TEXT
    )''')

    # Create table for storing user queries and results
    c.execute('''CREATE TABLE IF NOT EXISTS query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query TEXT,
        result TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Create table for storing user data (Optional)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
