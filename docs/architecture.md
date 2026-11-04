# ResolveFlow AI: Architecture

## Data flow

1. Staff member signs in using `POST /auth/login` from the browser.
2. FastAPI checks the Argon2 password hash and issues a random session cookie.
3. SQLite stores only a hash of the session token, plus the user and expiration time.
4. The dashboard requests a CSRF token from `GET /auth/csrf`, tied to the active session.
5. The dashboard submits a customer request with `POST /tickets` and the CSRF header.
6. FastAPI sends the complaint to local Ollama Qwen3 with a JSON classification schema.
7. An additional deterministic override elevates certain account-security incidents.
8. SQLite stores the classified ticket, its status, and associated notes.
9. Support staff search and filter tickets, change status with PATCH, and save internal notes through POST. All mutations require authentication, a matching request origin, and a valid session-bound CSRF token.

## Key interfaces

| Component | Responsibility |
|---|---|
| FastAPI | HTTP API, request validation, authentication and authorization |
| SQLite | Tickets, notes, users and hashed session tokens |
| Argon2 | One-way password hashing |
| Ollama Qwen3 | Local automated classification and priority assessment |
| Vanilla JS frontend | Authentication flow, dashboard, ticket interactions |
| pytest / TestClient | Automated isolated API behavior checks |

## Security scope

User roles are `admin` and `agent`. Both can work with tickets, but `/admin/users` is admin-only. Users must use a valid login session to access API data. Status changes, notes, classifications, ticket creation, and logout require the session CSRF header and same-origin validation. This demonstration is designed for localhost only, not production hosting.
