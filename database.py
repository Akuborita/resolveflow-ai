
import sqlite3
from pathlib import Path

# Location of our database file
DB_PATH = Path(__file__).resolve().parent / "resolveflow.db"


def initialize_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                assigned_department TEXT NOT NULL,
                status TEXT NOT NULL,
                classification_method TEXT NOT NULL,
                created_at TEXT NOT NULL
                DEFAULT (CURRENT_TIMESTAMP)
            )
        """)
        conn.commit()

def save_ticket(
    customer_name: str,
    message: str,
    category: str,
    priority: str,
    assigned_department: str,
    classification_method: str,
    status: str = "Awaiting Human Review"
):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO tickets (
                customer_name,
                message,
                category,
                priority,
                assigned_department,
                status,
                classification_method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            message,
            category,
            priority,
            assigned_department,
            status,
            classification_method
        ))

        conn.commit()
        return cursor.lastrowid


if __name__ == "__main__":
    initialize_database()
    print("ResolveFlow AI database created successfully!")



# Retrieve the most recent support tickets
def list_tickets(limit: int = 50):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT *
            FROM tickets
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        tickets = cursor.fetchall()

        return [dict(ticket) for ticket in tickets]


    
# Retrieve a support ticket using its unique ID
def get_ticket(ticket_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,)
        )

        ticket = cursor.fetchone()

        if ticket is None:
            return None

        return dict(ticket)




# Update the status of an existing support ticket
def update_ticket_status(ticket_id: int, new_status: str):
    allowed_statuses = [
        "Awaiting Human Review",
        "In Progress",
        "Resolved"
    ]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid ticket status")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            UPDATE tickets
            SET status = ?
            WHERE id = ?
            """,
            (new_status, ticket_id)
        )

        conn.commit()

        return cursor.rowcount > 0



# Create a table for internal ticket notes
def initialize_ticket_notes_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)

        conn.commit()



# Save an internal note for a support ticket
def save_ticket_note(ticket_id: int, note: str):
    note = note.strip()

    if not note:
        raise ValueError("Note cannot be empty")

    with sqlite3.connect(DB_PATH) as conn:
        ticket = conn.execute(
            "SELECT id FROM tickets WHERE id = ?",
            (ticket_id,)
        ).fetchone()

        if ticket is None:
            raise ValueError("Ticket not found")

        cursor = conn.execute(
            """
            INSERT INTO ticket_notes (ticket_id, note)
            VALUES (?, ?)
            """,
            (ticket_id, note)
        )

        conn.commit()
        return cursor.lastrowid


# Retrieve all notes belonging to a ticket
def get_ticket_notes(ticket_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT id, ticket_id, note, created_at
            FROM ticket_notes
            WHERE ticket_id = ?
            ORDER BY id DESC
            """,
            (ticket_id,)
        )

        return [dict(row) for row in cursor.fetchall()]



# Create the users table for authentication
def initialize_users_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'agent'
                    CHECK(role IN ('admin', 'agent')),
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()



# Create database table for secure login sessions
def initialize_sessions_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_sessions_expiry
            ON user_sessions(expires_at)
        """)

        conn.commit()



# No password hashes or session tokens are exposed here.
def list_users():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]
