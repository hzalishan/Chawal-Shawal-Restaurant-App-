import sqlite3
import time
from typing import List, Tuple, Any

# --- CONFIGURATION ---
DB_NAME = 'chawal_shawal.db'

def init_db() -> None:
    """
    Initializes the database. Creates the 'orders' table if it doesn't exist.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_no TEXT,
                items TEXT,
                total_price TEXT,
                status TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
        print(f"[DB INFO] Database '{DB_NAME}' checked/initialized.")
    except Exception as e:
        print(f"[DB ERROR] Init failed: {e}")

def add_order(table_no: str, items: str, total_price: str) -> Tuple[int, str]:
    """
    Saves a new order. Returns (Order ID, Timestamp).
    """
    timestamp = time.strftime('%H:%M:%S')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (table_no, items, total_price, status, timestamp) VALUES (?, ?, ?, 'PENDING', ?)", 
                   (table_no, items, total_price, timestamp))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id, timestamp

def get_ready_tables() -> List[str]:
    """
    Returns a list of tables that have READY status.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT table_no FROM orders WHERE status='READY'")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def mark_status_done(table_no: str) -> None:
    """
    Updates status from READY to DONE (Delivered).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='DONE' WHERE table_no=? AND status='READY'", (table_no,))
    conn.commit()
    conn.close()

def mark_status_ready(order_id: int) -> None:
    """
    Updates status from PENDING to READY (Chef finished cooking).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='READY' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

def get_all_orders() -> List[Tuple[Any]]:
    """
    Fetches all history for Admin Dashboard.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return rows

def clear_history() -> None:
    """
    Deletes ALL data. (Dangerous Action)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'") # Reset IDs
    conn.commit()
    conn.close()

# --- FIXED FUNCTION (Moved Outside) ---
def cancel_pending_order(table_no: str) -> List[int]:
    """
    Deletes only PENDING orders for a specific table.
    Returns list of deleted IDs to update the Server GUI.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Find IDs first (to tell Server what to remove)
    cursor.execute("SELECT id FROM orders WHERE table_no=? AND status='PENDING'", (table_no,))
    rows = cursor.fetchall()
    deleted_ids = [row[0] for row in rows]
    
    # 2. Delete them
    if deleted_ids:
        cursor.execute("DELETE FROM orders WHERE table_no=? AND status='PENDING'", (table_no,))
        conn.commit()
    
    conn.close()
    return deleted_ids