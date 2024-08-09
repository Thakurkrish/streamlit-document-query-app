
import streamlit as st
import sqlite3
import os
import bcrypt
from PyPDF2 import PdfReader
import docx
import io

# Function to initialize the database connection
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # Create user history table
    c.execute('''CREATE TABLE IF NOT EXISTS user_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, query TEXT, response TEXT)''')
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)''')
    
    # Create documents table
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT UNIQUE, content TEXT)''')

    conn.commit()
    return conn

# Password Hashing Functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# Function to add a new user to the database
def add_user(username, password):
    password_hash = hash_password(password)
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()

# Function to verify user login
def login_user(username, password):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and verify_password(user[0], password):
        return True
    return False

# Function to parse documents
def parse_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def parse_docx(file):
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def parse_txt(file):
    try:
        text = file.read().decode("utf-8")
    except UnicodeDecodeError as e:
        st.error(f"Error reading the file: {e}")
        text = ""
    return text

def parse_document(file):
    if file.type == "application/pdf":
        return parse_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(file)
    elif file.type == "text/plain":
        return parse_txt(file)
    else:
        st.error("Unsupported file type.")
        return None

# Function to insert or update parsed document content into the database
def insert_or_update_document(filename, content):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('REPLACE INTO documents (filename, content) VALUES (?, ?)', (filename, content))
    conn.commit()
    conn.close()

# Function to fetch the latest document from the database
def get_latest_document():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT filename, content FROM documents ORDER BY id DESC LIMIT 1')
    document = c.fetchone()
    conn.close()
    return document

def search_documents(query):
    latest_document = get_latest_document()
    if latest_document:
        filename, content = latest_document
        query_lower = query.lower()
        content_lower = content.lower()
        if "document name" in query_lower:
            # Return the document name
            return [f"Document Name: {filename}"]
        if "document overview" in query_lower:
            # Return the document overview
            sentences = content.split(". ")
            overview_sentences = [sentence for sentence in sentences if "overview" in sentence.lower() or "summary" in sentence.lower()]
            return [f"Found in {filename}: {'. '.join(overview_sentences)}"]
        elif "document objective" in query_lower:
            # Return the document objective
            sentences = content.split(". ")
            objective_sentences = [sentence for sentence in sentences if "objective" in sentence.lower() or "goal" in sentence.lower()]
            return [f"Found in {filename}: {'. '.join(objective_sentences)}"]
        else:
            # Check for partial matches
            words = query_lower.split()
            for word in words:
                if word in content_lower:
                    # Return a relevant snippet of the content
                    sentences = content.split(". ")
                    relevant_sentences = [sentence for sentence in sentences if word in sentence.lower()]
                    return [f"Found in {filename}: {'. '.join(relevant_sentences)}"]
    return []
# Function to download chat history
def download_chat_history(user):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT query, response FROM user_history WHERE user = ?', (user,))
    history = c.fetchall()
    conn.close()

    if not history:
        return "No chat history found."

    output = io.StringIO()
    output.write(f"Chat History for {user}:\n\n")
    for entry in history:
        output.write(f"Q: {entry[0]}\nA: {entry[1]}\n\n")

    return output.getvalue()

# Initialize the database
conn = init_db()
c = conn.cursor()

# User Registration and Login Section
st.sidebar.title("User Login / Registration")

# Tabs for login and registration
login_tab, register_tab = st.sidebar.tabs(["Login", "Register"])

with register_tab:
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    if st.button("Register"):
        if new_username and new_password:
            try:
                add_user(new_username, new_password)
                st.success("User registered successfully!")
            except sqlite3.IntegrityError:
                st.error("Username already exists. Please choose another one.")
        else:
            st.error("Please enter both username and password.")

with login_tab:
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        if login_user(login_username, login_password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = login_username
            st.success(f"Welcome {login_username}!")
        else:
            st.error("Invalid username or password.")

# Main Application Logic (Protected by login)
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.title("Document Query Application")
    st.write(f"Logged in as {st.session_state['username']}")

    # Sidebar - File Upload
    st.sidebar.title("Upload Documents")
    uploaded_files = st.sidebar.file_uploader("Choose a file", accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            document_content = parse_document(file)
            if document_content:
                insert_or_update_document(file.name, document_content)
                st.sidebar.success(f"{file.name} uploaded and parsed successfully!")

    # Main area - User Query
    user_input = st.text_input("Ask a question about the documents:")

    if st.button("Submit"):
        # Perform the document search
        search_results = search_documents(user_input)
        if search_results:
            response = "\n".join(search_results)
        else:
            response = "No relevant information found in the documents."
        
        st.write(f"Query: {user_input}")
        st.write(f"Response: {response}")
        
        # Store the query and response in the database
        c.execute("INSERT INTO user_history (user, query, response) VALUES (?, ?, ?)", 
                  (st.session_state['username'], user_input, response))
        conn.commit()

    # Sidebar - Download chat history
    if st.sidebar.button("Download Chat History"):
        chat_history = download_chat_history(st.session_state['username'])
        st.sidebar.download_button(
            label="Download Chat History",
            data=chat_history,
            file_name="chat_history.txt",
            mime="text/plain"
        )

# Close the connection to the database
conn.close()


