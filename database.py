import sqlite3
import pandas as pd

DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              name TEXT,
              email TEXT UNIQUE,   -- Added email, unique for invites
              password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  creator_id INTEGER,
                  invite_code TEXT UNIQUE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS group_members
                 (group_id INTEGER,
                  user_id INTEGER,
                  PRIMARY KEY (group_id, user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER,
                  description TEXT,
                  amount REAL,
                  payer_id INTEGER,
                  date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS splits
                 (expense_id INTEGER,
                  user_id INTEGER,
                  owed REAL,
                  PRIMARY KEY (expense_id, user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settlements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER,
                  payer_id INTEGER,
                  receiver_id INTEGER,
                  amount REAL,
                  date TEXT)''')
    
    conn.commit()
    conn.close()

init_db()  # Run every time

def get_user_groups(user_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("""
        SELECT g.id, g.name 
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
    """, conn, params=(user_id,))
    conn.close()
    return df

def get_group_members(group_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("""
        SELECT u.id, u.name 
        FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ?
    """, conn, params=(group_id,))
    conn.close()
    return df

def get_group_expenses(group_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("""
        SELECT e.*, s.user_id, s.owed
        FROM expenses e
        LEFT JOIN splits s ON e.id = s.expense_id
        WHERE e.group_id = ?
    """, conn, params=(group_id,))
    conn.close()
    return df

def get_group_settlements(group_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM settlements WHERE group_id = ?", conn, params=(group_id,))
    conn.close()
    return df