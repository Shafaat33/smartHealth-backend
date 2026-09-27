# Architecture

Healthcare Management System backend (FastAPI).

## Domains

- **User / Auth** — signup, login, tokens, and access control
- **Patient** — patient profiles and related records
- **Provider** — doctors / clinicians and their profiles
- **Appointment** — booking, scheduling, and appointment status

## Directory responsibilities

| Directory | Responsibility |
| --- | --- |
| `app/api` | HTTP route / endpoint files. Thin layer: parse request, call a service, return a response. |
| `app/models` | Database models (tables, columns, relationships). |
| `app/schemas` | Request and response shapes (Pydantic). Validates input and controls what the API returns. |
| `app/services` | Business logic for each domain (auth, patients, providers, appointments). |
| `app/repositories` | Database access only: queries, inserts, updates. No HTTP or business rules. |
| `app/core` | Shared app setup: config, security, DB session, and common dependencies. |
| `app/main.py` | FastAPI app entry point. Registers routers and global middleware. |
| `migrations` | Database schema change scripts (create / alter tables over time). |
| `tests` | Automated tests for APIs, services, and other app behavior. |
| `docs` | Project documentation, including this architecture note. |

Request flow: `api` → `services` → `repositories` → `models`
