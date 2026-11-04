# Portfolio Description: ResolveFlow AI

**Title:** ResolveFlow AI: Local AI-Powered Customer Support Management System

**Summary:** Built an AI-assisted customer support web application with Python, FastAPI, SQLite, vanilla JavaScript, and Ollama Qwen3. The system turns unstructured complaint messages into categorized support tickets, assigns priority, and provides a dashboard for handling tickets through resolution.

**Technical contributions:** Implemented structured local LLM responses using JSON schemas, deterministic escalation rules for account-security issues, persistent support notes, interactive status management, customer ticket search/filtering, Argon2 credential verification, hashed database-backed sessions, HTTP-only cookies, origin checks, session-derived CSRF validation, and role-based administrative access.

**Validation:** Added an offline integration test suite covering authentication, access restrictions, ticket lifecycle, note persistence, CSRF behavior, and mocked AI classification. Live Qwen3 operation is verified separately in a local demo.

**Suggested demonstration:** Show a fictional double-charge complaint entered through the dashboard, the resulting AI category and priority, updating the ticket to In Progress, saving an internal note, and confirming the note persists after reopening. Finish by logging out and demonstrating that the dashboard requires authentication.

**Technology:** Python, FastAPI, Pydantic, SQLite, Ollama, Qwen3, JavaScript, HTML/CSS, Argon2, pytest.

**Status:** Local functional MVP. Not advertised as a public production service or a deployed cloud application.
