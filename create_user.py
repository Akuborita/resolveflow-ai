"""Create a staff account without writing passwords into source code."""
import argparse
import getpass
import sqlite3

from auth import hasher
from database import (
    DB_PATH, initialize_database, initialize_ticket_notes_table,
    initialize_users_table, initialize_sessions_table,
)


def main():
    parser = argparse.ArgumentParser(description="Create a local ResolveFlow AI user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=("admin", "agent"), default="agent")
    args = parser.parse_args()
    username = args.username.strip()
    if not username or len(username) > 50:
        parser.error("Username must be 1 to 50 characters")
    password = getpass.getpass("Password: ")
    if len(password) < 12:
        parser.error("Use a password of at least 12 characters")
    if password != getpass.getpass("Confirm password: "):
        parser.error("Passwords do not match")

    for init in (initialize_database, initialize_ticket_notes_table,
                 initialize_users_table, initialize_sessions_table):
        init()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hasher.hash(password), args.role),
            )
    except sqlite3.IntegrityError:
        parser.error("Username already exists. No account was changed")
    print(f"User '{username}' created with role '{args.role}'.")


if __name__ == "__main__":
    main()
