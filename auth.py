import sqlite3
import streamlit as st
from database import DB_FILE

def register(username, name, email, password):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)",
                     (username, name, email, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username or email already taken
    finally:
        conn.close()

def login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return (user[0], user[1])  # Return (id, name)
    else:
        return None