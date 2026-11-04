
import sqlite3
import secrets
import hashlib
import time
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from database import DB_PATH

hasher = PasswordHasher()

SESSION_DURATION = 8 * 60 * 60


# Verify username and password
def authenticate_user(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = ? AND is_active = 1
            """,
            (username.strip(),)
        ).fetchone()

    if user is None:
        return None

    try:
        hasher.verify(user["password_hash"], password)
    except (VerificationError, InvalidHashError):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }


# Create a secure login session
def create_session(user_id):
    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    now = int(time.time())

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO user_sessions
            (token_hash, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                token_hash,
                user_id,
                now,
                now + SESSION_DURATION
            )
        )

    return token

# Generate a CSRF token bound to the login session
def create_csrf_token(session_token):
    return hmac.new(
        session_token.encode("utf-8"),
        b"resolveflow-csrf-v1",
        hashlib.sha256
    ).hexdigest()


# Look up an authenticated user
def get_session_user(token):
    if not token:
        return None

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            """
            SELECT users.id, users.username, users.role
            FROM user_sessions
            JOIN users ON users.id = user_sessions.user_id
            WHERE user_sessions.token_hash = ?
              AND user_sessions.expires_at > ?
              AND users.is_active = 1
            """,
            (token_hash, int(time.time()))
        ).fetchone()

    return dict(user) if user else None


# End a login session
def delete_session(token):
    if not token:
        return

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM user_sessions WHERE token_hash = ?",
            (token_hash,)
        )
