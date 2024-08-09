import sqlite3

def insert_document(filename, content):
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()
    c.execute('INSERT INTO documents (filename, content) VALUES (?, ?)', (filename, content))
    conn.commit()
    conn.close()

def get_documents():
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()
    c.execute('SELECT * FROM documents')
    documents = c.fetchall()
    conn.close()
    return documents

def insert_query_history(user_id, query, result):
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()
    c.execute('INSERT INTO query_history (user_id, query, result) VALUES (?, ?, ?)', (user_id, query, result))
    conn.commit()
    conn.close()

def get_query_history(user_id):
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()
    c.execute('SELECT * FROM query_history WHERE user_id = ?', (user_id,))
    history = c.fetchall()
    conn.close()
    return history

def add_user(username, password_hash):
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect('document_query.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user
