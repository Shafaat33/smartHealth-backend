# smartHealth-backend
# SmartHealth Backend

SmartHealth is the backend for a clinic's appointment desk. Patients sign up and book time with a provider. Providers and front-desk staff confirm, complete, or cancel those bookings. A built-in assistant answers everyday questions such as "how do I prepare for a lab test?" or "when is my next appointment?", using the clinic's own documents and the signed-in user's schedule.

The goal is booking that stays correct when something goes wrong. If a patient grabs a slot and nobody confirms it, the slot frees itself. If a service restarts mid-booking, the booking picks up where it left off. Every change leaves a trail of notifications, analytics, logs, traces, and metrics.

## Contents

- [What's inside](#whats-inside)
- [Quick start](#quick-start)
- [Your first booking](#your-first-booking)
- [How a booking works](#how-a-booking-works)
- [Who can do what](#who-can-do-what)
- [Project layout](#project-layout)
- [Services in Docker Compose](#services-in-docker-compose)
- [Running without Docker](#running-without-docker)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Temporal in depth](#temporal-in-depth)
- [Events and background jobs](#events-and-background-jobs)
- [The assistant](#the-assistant)
- [Observability](#observability)
- [Known gaps](#known-gaps)

## What's inside

Each tool here has one job:

| Tool | Its job |
| --- | --- |
| FastAPI, Pydantic, Uvicorn | The HTTP API, request validation, and interactive docs |
| PostgreSQL + pgvector | All application data, plus vector search for the assistant |
| SQLAlchemy, Alembic | Database models and migrations |
| PyJWT, bcrypt | Login tokens and password hashing |
| Temporal | Holding a booking open, waiting for a decision, and releasing the slot if none arrives |
| Kafka | A log of everything that happens to an appointment |
| Celery + Redis | Short background jobs: notifications, analytics, document ingestion |
| OpenAI, LangGraph, LangChain | The assistant's reasoning, routing, and embeddings |
| pypdf | Reading the clinic PDFs in `data/knowledge` |
| OpenTelemetry + Jaeger | Following one request across the system |
| Prometheus + Grafana | Counting and graphing what the system is doing |

Temporal and Celery do different work here. Temporal handles processes that have to wait, sometimes for minutes or days, and must survive restarts. Celery handles small tasks that should run soon and then finish.

## Quick start

You need [Docker](https://docs.docker.com/get-docker/) with Docker Compose. An OpenAI API key is only needed for the assistant and document ingestion.

**1. Create a `.env` file** in the project root:

```bash
POSTGRES_USER=smarthealth
POSTGRES_PASSWORD=change-me
POSTGRES_DB=smarthealth
SECRET_KEY=paste-a-long-random-string-here
OPENAI_API_KEY=your-openai-key
```

To generate a good `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` is gitignored. Keep it that way, and never commit real keys.

**2. Start everything:**

```bash
docker compose up --build
```

The first run takes a few minutes while images download and Temporal sets up its database. The API runs migrations on startup, so you don't need to create tables by hand.

**3. Check that it's alive:**

```bash
curl http://localhost:8000/health
# {"health":"ok"}

curl -X POST http://localhost:8000/temporal/ping
# {"result":"ok"}
```

If the ping returns `ok`, the API, Temporal server, and Temporal worker are all connected.

**4. Open the dashboards:**

| What | Where |
| --- | --- |
| Interactive API docs | http://localhost:8000/docs |
| Temporal UI (see every booking workflow) | http://localhost:8088 |
| Jaeger (request traces) | http://localhost:16686 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

Grafana opens without a login in this local setup.

## Your first booking

Here's the full flow end to end with `curl`. The interactive docs at `/docs` work too.

**Sign up as a patient.** Public registration always creates a patient account:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Ayesha Khan", "email": "ayesha@example.com", "password": "a-strong-password"}'
```

**Log in and keep the token:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ayesha@example.com", "password": "a-strong-password"}'
# {"access_token": "eyJ...", "token_type": "bearer"}
```

Send that token on every later request as `Authorization: Bearer <token>`.

**Create a front-desk user.** Nothing creates the first front-desk user for you. Register a normal account, then promote it in the database:

```bash
docker compose exec db psql -U smarthealth -d smarthealth \
  -c "UPDATE users SET role = 'front_desk' WHERE email = 'desk@example.com';"
```

Log in again after the change so the new role is in the token.

**Add a provider.** Front desk creates providers with `POST /providers`. The provider gets their own login.

**Book.** As the patient, call `POST /appointments` with a `provider_id` and a future `appointment_time`. The appointment starts as `pending`, and a 60-second hold begins. You can watch that hold in the Temporal UI as a workflow named `booking-<appointment id>`.

**Confirm it.** As that provider or as front desk, call:

```bash
curl -X PATCH http://localhost:8000/appointments/<appointment-id> \
  -H "Authorization: Bearer <provider-or-desk-token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "confirm"}'
```

If you wait longer than 60 seconds instead, the slot is released and the appointment becomes `canceled`. Confirming after that returns 409, "Booking hold expired".

## How a booking works

```mermaid
sequenceDiagram
    participant P as Patient
    participant API as FastAPI
    participant DB as Postgres
    participant T as Temporal
    participant W as Temporal worker
    participant K as Kafka
    participant C as Celery

    P->>API: POST /appointments
    API->>DB: Save appointment as pending
    API->>T: Start booking-{id} workflow (60s hold)
    API->>K: appointment.booked event
    K->>C: Notification and analytics tasks
    alt Confirmed within the hold
        API->>T: Signal "confirm"
        API->>DB: Mark confirmed
    else Nobody confirms in time
        T->>W: Hold expired
        W->>DB: Cancel the pending appointment
    end
```

In words:

1. A patient books. The appointment is saved as `pending`.
2. The API starts a Temporal workflow for that one appointment. The workflow waits up to `BOOKING_HOLD_SECONDS` (60 by default).
3. An `appointment.booked` event goes to Kafka, and the patient and provider get a notification.
4. A provider or front-desk user confirms, completes, or cancels. The API passes that decision to the waiting workflow as a signal.
5. If nobody confirms in time, the Temporal worker cancels the appointment and frees the slot.

The design also covers a few failure cases:

- **Temporal is down when someone books.** The API cancels the new appointment and returns 503. A slot is never left reserved with no timer to release it.
- **The API restarts during a hold.** The hold lives in Temporal, not in the API process, so the timer keeps running.
- **Two people grab the same slot.** A database constraint allows only one active appointment per provider per time. The second booking gets 409.
- **Confirm is clicked twice.** The second click sees the appointment is already confirmed and returns without signaling again.

After confirmation, the same workflow stays open until the visit is completed or canceled. The 60-second timer only covers the unconfirmed window.

Rescheduling changes the time in Postgres. It does not restart the hold.

## Who can do what

There are three roles.

**Patients** sign up themselves. They can book, view, and reschedule their own appointments, read their notifications, and chat with the assistant.

**Providers** are created by front desk. They can confirm, complete, cancel, and reschedule their own appointments, and browse the provider directory.

**Front desk** can do almost everything. They create providers, see every patient and appointment, update any appointment, view analytics, and load clinic documents into the assistant.

Patients can't confirm or cancel through `PATCH /appointments/{id}`. That stays with providers and front desk.

An appointment moves through these statuses:

```mermaid
stateDiagram-v2
    [*] --> pending: booked
    pending --> confirmed
    pending --> complete
    pending --> canceled: canceled or hold expired
    confirmed --> complete
    confirmed --> canceled
    complete --> [*]
    canceled --> [*]
```

`complete` and `canceled` are final.

## Project layout

Code follows the same path for every request: **route → service → repository → model**. Routes deal with HTTP, services hold the business rules, repositories run the queries, and models describe the tables.

```text
smartHealth-backend/
├── app/
│   ├── main.py           # The FastAPI app: middleware, metrics, routes
│   ├── api/              # HTTP routes, one file per area
│   ├── services/         # Business rules (booking, auth, notifications, ...)
│   ├── repositories/     # Database queries
│   ├── models/           # SQLAlchemy tables
│   ├── schemas/          # Request and response shapes
│   ├── core/             # Config, auth, Kafka, Temporal client, tracing, metrics
│   ├── workflows/        # Temporal workflows
│   ├── activities/       # Temporal steps that touch the database
│   ├── worker.py         # Starts the Temporal worker
│   ├── tasks/            # Celery tasks
│   ├── consumers/        # Kafka consumer
│   └── ai/               # Assistant: graph, prompts, tools, safety checks
├── alembic/              # Database migrations
├── data/knowledge/       # Clinic PDFs the assistant reads
├── observability/        # Prometheus and Grafana config
├── scripts/              # Container entrypoint, PDF generator
├── docs/                 # Architecture notes
└── prds/                 # Original product requirements
```

`main.py` at the repository root is leftover project scaffolding. The real app is `app/main.py`.

## Services in Docker Compose

The four application processes are built from the same image. Only their start command differs.

| Service | What it does | Port |
| --- | --- | --- |
| `api` | Runs migrations, then serves the HTTP API | 8000 |
| `worker` | Runs Temporal workflows and activities | — |
| `kafka-consumer` | Reads appointment events and queues Celery jobs | — |
| `celery` | Runs background jobs and exposes their metrics | 9000 |
| `db` | Postgres 16 with pgvector | 5433 |
| `temporal` | The Temporal server | 7233 |
| `temporal-ui` | Browse workflows | 8088 |
| `kafka` | Event broker. Containers use `kafka:9092`. | 9094 |
| `redis` | Celery's queue and result store | 6379 |
| `jaeger` | Trace viewer and collector | 16686, 4317 |
| `prometheus` | Collects metrics from the API and Celery | 9090 |
| `grafana` | Dashboards | 3000 |

Postgres listens on 5433 on your machine to avoid clashing with a local Postgres on 5432. Temporal stores its own data on the same Postgres server, in separate databases.

## Running without Docker

You can run the API on your machine with Python 3.13 and [uv](https://docs.astral.sh/uv/). You still need Postgres with pgvector. Temporal, Kafka, and Redis are only needed for the features that use them. An easy middle ground is to run just the infrastructure in Docker:

```bash
docker compose up db temporal redis kafka
```

Then start the API locally:

```bash
uv sync
export DATABASE_URL=postgresql+psycopg2://smarthealth:change-me@localhost:5433/smarthealth
export SECRET_KEY=paste-a-long-random-string-here
export KAFKA_BOOTSTRAP_SERVERS=localhost:9094
export REDIS_URL=redis://localhost:6379/0
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Start the background processes in separate terminals, with the same environment:

```bash
uv run python -m app.worker                        # Temporal worker
uv run python -m app.consumers.appointments        # Kafka consumer
uv run celery -A app.celery_app worker --loglevel=INFO --pool=solo
```

Without the Temporal worker, bookings can be created, but their holds never resolve.

## Configuration

Everything is configured through environment variables. A `.env` file in the project root is loaded automatically. Only two variables are required; the rest have defaults that work locally.

**Required**

| Variable | What it's for |
| --- | --- |
| `DATABASE_URL` | Where the database lives. Compose sets this for you. |
| `SECRET_KEY` | Signs login tokens. Use a long random value. |

**Auth**

| Variable | Default | What it's for |
| --- | --- | --- |
| `JWT_ALGORITHM` | `HS256` | Token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | How long a login lasts |

**Booking and Temporal**

| Variable | Default | What it's for |
| --- | --- | --- |
| `BOOKING_HOLD_SECONDS` | `60` | How long an unconfirmed booking holds its slot |
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal server address |
| `TEMPORAL_TASK_QUEUE` | `smarthealth-task-queue` | Queue shared by the API and worker |

**Events and jobs**

| Variable | Default | What it's for |
| --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | empty | Kafka address. If empty, events are not published. |
| `KAFKA_APPOINTMENTS_TOPIC` | `appointments` | Topic for appointment events |
| `KAFKA_CONSUMER_GROUP` | `smarthealth-appointments-logger` | Consumer group name |
| `REDIS_URL` | empty | Celery's broker. Celery falls back to `redis://localhost:6379/0`. |
| `CELERY_METRICS_PORT` | `9000` | Where Celery exposes metrics |

**Assistant**

| Variable | Default | What it's for |
| --- | --- | --- |
| `OPENAI_API_KEY` | empty | Needed for chat and ingestion |
| `CHAT_MODEL` | `gpt-4o-mini` | Model that writes answers |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Model that embeds documents |
| `EMBEDDING_DIM` | `1536` | Embedding size. Must match the model. |
| `KNOWLEDGE_DIR` | `data/knowledge` | Folder of PDFs to ingest |
| `KNOWLEDGE_CHUNK_SIZE` | `800` | Characters per document chunk |
| `KNOWLEDGE_CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `4` | Chunks pulled in per question |

**Clinic hours** (used when the assistant suggests open slots)

| Variable | Default | What it's for |
| --- | --- | --- |
| `CLINIC_TIMEZONE` | `Asia/Karachi` | The clinic's local time |
| `CLINIC_OPEN`, `CLINIC_CLOSE` | `09:00`, `17:00` | Opening hours |
| `CLINIC_DAYS` | `0,1,2,3,4` | Open days, Monday is 0 |
| `SLOT_MINUTES` | `30` | Length of a slot |

**Tracing**

| Variable | Default | What it's for |
| --- | --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | empty | Where to send traces. If empty, tracing is off. |
| `OTEL_SERVICE_NAME` | `smarthealth-api` | Name shown in Jaeger |

## API reference

The interactive docs at http://localhost:8000/docs list every field. This section is a map.

Every route needs `Authorization: Bearer <token>` except register, login, `/health`, `/metrics`, and `/temporal/ping`.

### Accounts

| Endpoint | Who | What it does |
| --- | --- | --- |
| `POST /auth/register` | Anyone | Creates a patient account |
| `POST /auth/login` | Anyone | Returns an access token |
| `GET /auth/me` | Signed in | Your account |

### Patients and providers

| Endpoint | Who | What it does |
| --- | --- | --- |
| `GET /patients/me` | Patient | Your patient profile |
| `GET /patients` | Front desk | All patients |
| `GET /patients/{id}` | That patient, or front desk | One patient |
| `POST /providers` | Front desk | Create a provider and their login |
| `GET /providers/me` | Provider | Your provider profile |
| `GET /providers` | Signed in | Provider directory |
| `GET /providers/{id}` | Signed in | One provider |

### Appointments

| Endpoint | Who | What it does |
| --- | --- | --- |
| `POST /appointments` | Patient | Book a slot and start the hold |
| `GET /appointments` | Signed in | Front desk sees all. Everyone else sees their own. |
| `GET /appointments/{id}` | Owner, or front desk | One appointment |
| `PATCH /appointments/{id}` | The provider, or front desk | `{"action": "confirm"}`, `"complete"`, or `"canceled"` |
| `POST /appointments/{id}/reschedule` | Patient, provider, or front desk | Move a pending or confirmed appointment |

Common errors:

| Status | Meaning |
| --- | --- |
| 400 | The time is in the past |
| 403 | It's not your appointment |
| 404 | The patient, provider, or appointment doesn't exist |
| 409 | The slot is taken, the status change isn't allowed, or the booking hold already expired |
| 503 | Temporal is unreachable, so scheduling is paused |

### Notifications, analytics, and documents

| Endpoint | Who | What it does |
| --- | --- | --- |
| `GET /notifications` | Signed in | Your notifications |
| `GET /analytics` | Front desk | Total patients, completed visits, cancellation rate, bookings per day |
| `POST /knowledge/ingest` | Front desk | Queue the clinic PDFs for the assistant. Returns 202 and a `task_id`. |

### Assistant

| Endpoint | Who | What it does |
| --- | --- | --- |
| `POST /assistant/chat` | Signed in | Ask a question. The answer streams back as server-sent events. |
| `GET /assistant/conversations` | Signed in | Your past conversations |
| `GET /assistant/conversations/{id}/messages` | Signed in | Messages in one of your conversations |

### Health and operations

| Endpoint | What it does |
| --- | --- |
| `GET /health` | Confirms the API process is running. It does not check the database or other services. |
| `GET /metrics` | Prometheus metrics |
| `POST /temporal/ping` | Runs a tiny workflow to confirm Temporal and the worker are connected |

## Temporal in depth

A booking hold needs three things: to wait for a while, to react when someone confirms, and to keep its place if a process restarts. A Celery job or an in-memory timer can't do all three, so the hold is a Temporal workflow.

Each appointment gets exactly one workflow, with the id `booking-{appointment_id}`. Tying the id to the appointment means the same booking can't start two timers. This project uses a single workflow per booking. There are no child workflows, queries, schedules, or `continue_as_new`.

### The booking workflow

`BookingWorkflow` lives in `app/workflows/booking.py`.

1. It starts when a patient books and waits for a signal, up to the hold time.
2. If nobody signals in time, it runs `release_slot_if_pending`. That activity cancels the appointment only if it is still `pending`, so an appointment confirmed at the last second is never undone.
3. If `confirm` arrives, the workflow keeps waiting, with no time limit, for the visit to be completed or canceled.
4. When `complete` or `canceled` arrives, it runs `apply_appointment_status` to save the final status, then ends.

All database work happens in **activities** (`app/activities/booking.py`). The workflow itself only waits and decides. That keeps the workflow deterministic, which is what lets Temporal replay it safely after a crash.

Each activity has 30 seconds to finish. If a status change isn't allowed, for example completing a canceled visit, the activity fails without retrying, since retrying wouldn't help. Other failures use Temporal's default retries.

### How the API talks to it

`app/core/temporal.py` has the two helpers the API uses:

- `start_booking_hold` starts the workflow and returns immediately. The patient doesn't wait 60 seconds for a response.
- `signal_booking` checks that the workflow is still running, sends the decision, and for complete or cancel waits until the workflow has saved it. If the workflow already finished, the API returns 409.

For `confirm`, the API saves the new status itself, since confirming doesn't end the workflow. For complete and cancel, the workflow saves it first. The API's follow-up write sees the status already matches and does nothing.

### The worker

`app/worker.py` connects to Temporal, retrying every 2 seconds until the server is up. It then runs both workflows (`BookingWorkflow` and the `PingWorkflow` health check) and their three activities on the `smarthealth-task-queue` queue.

## Events and background jobs

Whenever an appointment changes, the API:

1. Publishes an event such as `appointment.booked` or `appointment.canceled` to Kafka.
2. Saves the notification and analytics record right away.

If Kafka is down, the failure is logged and the request still succeeds.

The Kafka consumer (`app/consumers/appointments.py`) reads each event and hands it to two Celery jobs:

- `send_notification` saves the notification, skipping it if that exact one already exists, so replays don't create duplicates
- `record_analytics` saves the analytics record

The consumer only marks a Kafka message as handled after both jobs are queued. If it crashes in between, the message is read again rather than lost.

A third Celery job, `ingest_knowledge`, loads the clinic PDFs. It reads each file in `data/knowledge`, splits it into chunks, turns the chunks into embeddings with OpenAI, and stores them in Postgres for the assistant to search. Front desk triggers it with `POST /knowledge/ingest`.

## The assistant

The assistant is a LangGraph graph in `app/ai/graph.py`. Each question goes through these steps:

1. **Safety check.** Messages mentioning things like chest pain, trouble breathing, or self-harm get an immediate reply telling the user to call emergency services or go to the nearest emergency department. Nothing else runs.
2. **Classify.** The model sorts the question into one of four kinds: a general clinic question, a question about the user's own appointments, a request to find a provider and open slots, or something out of scope. If the question is too vague to sort, the assistant asks a follow-up instead of guessing.
3. **Gather context.** Clinic questions search the ingested PDFs. Appointment questions read only the signed-in user's own appointments. Find-care requests look up providers by specialty and open slots within the configured clinic hours.
4. **Answer.** The model writes a reply from that context, and the reply streams back while it's being written. Document answers include their sources.

Conversations are saved, so follow-up questions keep their context. Each user only sees their own conversations.

Run the ingestion once (`POST /knowledge/ingest`) before asking document questions. Until then, the assistant has no clinic material to search.

## Observability

**Logs.** Every request gets an `X-Request-ID` header, or keeps one you send, and a log line with method, path, status, and time taken. Send your own request id to trace a request from your frontend through the logs.

**Traces.** With `OTEL_EXPORTER_OTLP_ENDPOINT` set, which Compose does, each request shows up in Jaeger. Assistant steps have their own spans, so you can see where time goes.

**Metrics.** Prometheus collects request metrics from the API and job metrics from Celery every 10 seconds. These include bookings, notifications delivered and failed, assistant questions, and assistant errors. Grafana loads a ready-made dashboard from `observability/grafana/dashboards/smarthealth.json`.

`/health` and `/metrics` are left out of logs, traces, and metrics so health checks don't drown out real traffic.

## Known gaps

- There are no automated tests yet.
- The first front-desk user has to be promoted by hand in the database (see [Your first booking](#your-first-booking)).
- `/health` only says the API process is up. It doesn't check Postgres, Temporal, Kafka, or Redis.
- CORS only allows a frontend at `http://localhost:5173` or `http://127.0.0.1:5173`.
- The requirements in `prds/` mention billing and reminders. Neither exists in the code yet.

For the reasoning behind the layering, see [`docs/archetecture.md`](docs/archetecture.md).
