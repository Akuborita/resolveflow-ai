# ResolveFlow AI: Three-minute demonstration script

**0:00–0:20 | Problem**
Support teams receive unstructured complaints and need to categorize, prioritize, and track each issue. ResolveFlow AI reduces manual triage work while keeping a human in control of ticket resolution.

**0:20–0:50 | Stack and flow**
Show the login screen and dashboard. Explain that FastAPI runs the API, Qwen3 runs locally through Ollama, and SQLite stores tickets and internal notes.

**0:50–1:35 | AI intake**
Create a fictional ticket: “I was charged twice for my subscription and need urgent assistance.” Show the AI-generated category and priority.

**1:35–2:15 | Ticket workflow**
Find the ticket, change its status to In Progress, add an internal note, reopen it, and demonstrate that the note persisted.

**2:15–2:45 | Authentication and security**
Log out and attempt to reopen the dashboard. Explain the local Admin/Agent permissions, session-based authentication, and the offline test suite without claiming the system is production hardened.

**2:45–3:00 | Result**
Summarize how the app integrates local LLM classification with a usable operations dashboard and persistent workflow data.

**Recording safety:** Use fictional tickets and no visible real passwords, cookies, API keys, or private customer information. Do not publish the local database.
