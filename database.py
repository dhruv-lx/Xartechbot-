import sqlite3
import hashlib
from datetime import datetime
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.strip().encode()).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table (Admin & Agents)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'agent', -- 'admin' or 'agent'
            telegram_chat_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Visits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            shop_name TEXT NOT NULL,
            owner_name TEXT,
            phone_number TEXT NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            shop_photo_path TEXT NOT NULL,
            card_photo_path TEXT,
            remarks TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Active user sessions (chat_id -> user_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            logged_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Create default Admin if no admin exists
    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    if not cursor.fetchone():
        default_admin_user = "admin"
        default_admin_pass = "xartech@123"
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, 'admin')
        """, (default_admin_user, hash_password(default_admin_pass), "Super Admin"))
        print(f"[*] Default Admin created: Username: {default_admin_user}, Password: {default_admin_pass}")
        
    conn.commit()
    conn.close()

# User Management Functions
def create_user(username, password, full_name, role='agent'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        """, (username.strip().lower(), hash_password(password), full_name.strip(), role))
        conn.commit()
        user_id = cursor.lastrowid
        return True, user_id, "User created successfully."
    except sqlite3.IntegrityError:
        return False, None, f"Username '{username}' already exists!"
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE username = ?
    """, (username.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE username = ? AND password_hash = ? AND is_active = 1
    """, (username.strip().lower(), hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def set_session(chat_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO sessions (chat_id, user_id, logged_in_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (chat_id, user_id))
    # Also update telegram_chat_id on user record
    cursor.execute("UPDATE users SET telegram_chat_id = ? WHERE id = ?", (chat_id, user_id))
    conn.commit()
    conn.close()

def get_session_user(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.* FROM users u
        JOIN sessions s ON u.id = s.user_id
        WHERE s.chat_id = ? AND u.is_active = 1
    """, (chat_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def clear_session(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def update_user_password(user_id, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET password_hash = ? 
        WHERE id = ?
    """, (hash_password(new_password), user_id))
    conn.commit()
    conn.close()
    return True

def get_active_admins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE role = 'admin' AND is_active = 1 AND telegram_chat_id IS NOT NULL
    """)
    admins = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return admins

def get_all_agents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id ASC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def toggle_user_status(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_status = 0 if row['is_active'] == 1 else 1
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
        conn.close()
        return True, new_status
    conn.close()
    return False, None

# Visit Data Functions
def save_visit(user_id, shop_name, owner_name, phone_number, address, latitude, longitude, shop_photo_path, card_photo_path, remarks):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO visits (
            user_id, shop_name, owner_name, phone_number, address, 
            latitude, longitude, shop_photo_path, card_photo_path, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, shop_name.strip(), owner_name.strip() if owner_name else None,
        phone_number.strip(), address.strip() if address else None,
        latitude, longitude, shop_photo_path, card_photo_path,
        remarks.strip() if remarks else None
    ))
    conn.commit()
    visit_id = cursor.lastrowid
    conn.close()
    return visit_id

def get_visits(user_id=None, date_filter=None):
    """
    date_filter can be: 'today', 'week', 'month', or None (all time)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT v.*, u.full_name as agent_name, u.username as agent_username
        FROM visits v
        JOIN users u ON v.user_id = u.id
        WHERE 1=1
    """
    params = []
    
    if user_id:
        query += " AND v.user_id = ?"
        params.append(user_id)
        
    if date_filter == 'today':
        query += " AND DATE(v.created_at) = DATE('now', 'localtime')"
    elif date_filter == 'week':
        query += " AND DATE(v.created_at) >= DATE('now', '-7 days', 'localtime')"
    elif date_filter == 'month':
        query += " AND DATE(v.created_at) >= DATE('now', '-30 days', 'localtime')"
        
    query += " ORDER BY v.created_at DESC"
    
    cursor.execute(query, params)
    visits = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return visits

def get_visit_stats(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    if user_id:
        cursor.execute("SELECT COUNT(*) as count FROM visits WHERE user_id = ?", (user_id,))
        stats['total'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM visits WHERE user_id = ? AND DATE(created_at) = DATE('now', 'localtime')", (user_id,))
        stats['today'] = cursor.fetchone()['count']
    else:
        cursor.execute("SELECT COUNT(*) as count FROM visits")
        stats['total'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM visits WHERE DATE(created_at) = DATE('now', 'localtime')")
        stats['today'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'agent' AND is_active = 1")
        stats['active_agents'] = cursor.fetchone()['count']
        
    conn.close()
    return stats
