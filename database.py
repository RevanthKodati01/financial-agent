import sqlite3
from datetime import datetime

def get_connection():
    conn = sqlite3.connect("financial_agent.db")
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            transaction_limit REAL NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # Countries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            country_name TEXT PRIMARY KEY,
            risk_level TEXT NOT NULL,
            max_amount REAL
        )
    """)
    
    # Transaction history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_history (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            country_to TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Seed customer data
    customers = [
        ("C-1042", "John Smith", 10000, "active"),
        ("C-2077", "Sarah Johnson", 50000, "active"),
        ("C-3099", "Mike Davis", 5000, "active"),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO customers 
        (customer_id, name, transaction_limit, status) 
        VALUES (?, ?, ?, ?)
    """, customers)
    
    # Seed country data
    countries = [
        ("Iran", "restricted", None),
        ("North Korea", "restricted", None),
        ("Cuba", "restricted", None),
        ("Syria", "restricted", None),
        ("Russia", "high_risk", 10000),
        ("Venezuela", "high_risk", 10000),
        ("Myanmar", "high_risk", 10000),
        ("Mexico", "allowed", None),
        ("Poland", "allowed", None),
        ("Germany", "allowed", None),
        ("Canada", "allowed", None),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO countries 
        (country_name, risk_level, max_amount) 
        VALUES (?, ?, ?)
    """, countries)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def log_transaction(customer_id, amount, country_to, decision, reason):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transaction_history 
        (customer_id, amount, country_to, decision, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_id, amount, country_to, decision, reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()