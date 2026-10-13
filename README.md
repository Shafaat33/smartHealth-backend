# smartHealth-backend

Backend for a clinic scheduling system. Patients book appointments, providers and front-desk staff move those appointments through a hold-and-confirm workflow, and an assistant answers clinic questions from uploaded documents plus the signed-in user's own schedule.

The HTTP API is FastAPI. Postgres stores the operational data and the assistant's document embeddings. Temporal owns the booking hold. Kafka carries appointment events. Celery, backed by Redis, delivers notifications, records analytics, and ingests knowledge documents.

## Stack

| Piece | Used for |
| --- | --- |
| FastAPI, Uvicorn, Pydantic | HTTP API, validation, and OpenAPI docs |
| SQLAlchemy, Alembic, psycopg2 | Models, queries, and schema migrations |
| PostgreSQL + pgvector | Application data and embedding search |
| PyJWT, bcrypt | Access tokens and password hashing |
| Temporal | Durable booking hold: wait, accept signals, release the slot on timeout |
| Apache Kafka | Appointment event log |
| Celery, Redis | Notification delivery, analytics writes, PDF ingestion |
| OpenAI, LangGraph, LangChain | Assistant chat, routing, and embeddings |
| pypdf | Reading clinic PDFs in `data/knowledge` |
| OpenTelemetry, Jaeger | Request and assistant traces |
| Prometheus, Grafana | API and Celery metrics |

## How a booking moves

1. A patient calls `POST /appointments`. The API inserts the row as `pending` and commits.
2. The API starts a Temporal workflow whose id is `booking-{appointment_id}`. The workflow waits `BOOKING_HOLD_SECONDS` (default 60).
3. The API publishes an `appointment.booked` event to Kafka and writes the notification.
4. A provider or front-desk user confirms, completes, or cancels with `PATCH /appointments/{id}`. That call signals the same workflow.
5. If nobody confirms before the hold expires, the Temporal worker cancels the still-pending row and frees the slot.
6. The Kafka consumer turns each event into two Celery tasks: `send_notification` and `record_analytics`.

Confirm does not finish the workflow. After confirm, the same workflow stays open until the visit is completed or canceled. The hold timer applies only to the unconfirmed window.

If Temporal cannot start the hold, the API cancels the pending row and returns 503, so a slot is not left reserved without a timer.

Reschedule updates the appointment time in Postgres. It does not reset the Temporal hold.

## Processes

`docker-compose.yml` runs one application image and the infrastructure around it. The API, Temporal worker, Kafka consumer, and Celery worker share that image and differ only by command.

| Service | Command / image | Port | Role |
| --- | --- | --- | --- |
| `api` | `scripts/entrypoint.sh` (migrate, then Uvicorn) | 8000 | HTTP API. Temporal client. |
| `worker` | `python -m app.worker` | — | Temporal worker on `smarthealth-task-queue` |
| `kafka-consumer` | `python -m app.consumers.appointments` | — | Reads the `appointments` topic and enqueues Celery tasks |
| `celery` | `celery -A app.celery_app worker` | 9000 | Background jobs. Prometheus metrics on this port. |
| `db` | `pgvector/pgvector:pg16` | 5433 | App database. Temporal uses the same Postgres server for its own databases. |
| `temporal` | Temporal auto-setup | 7233 | Workflow server |
| `temporal-ui` | Temporal Web UI | 8088 | Inspect workflow history |
| `kafka` | Apache Kafka (KRaft) | 9094 | Broker. In-cluster clients use `kafka:9092`. |
| `redis` | Redis 7 | 6379 | Celery broker and result backend |
| `jaeger` | Jaeger all-in-one | 16686 | Trace UI. OTLP receiver on 4317. |
| `prometheus` | Prometheus | 9090 | Scrapes `api:8000` and `celery:9000` |
| `grafana` | Grafana | 3000 | Dashboard provisioned from `observability/grafana` |

The API container runs `alembic upgrade head` before it starts serving.

## Repository layout

Request handling follows `api` → `services` → `repositories` → `models`.

| Path | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI app: CORS, request ids, tracing, metrics, routers |
| `app/api` | Route handlers. They validate auth, call a service, and map errors to HTTP. |
| `app/services` | Business rules |
| `app/repositories` | Queries and writes |
| `app/models` | SQLAlchemy tables |
| `app/schemas` | Pydantic request and response models |
| `app/core` | Config, JWT, database sessions, Kafka producer, Temporal client, tracing, metrics |
| `app/workflows` | Temporal workflows (`BookingWorkflow`, `PingWorkflow`) |
| `app/activities` | Temporal activities. These are the only workflow steps that touch the database. |
| `app/worker.py` | Temporal worker process |
| `app/tasks` | Celery tasks |
| `app/consumers` | Kafka consumer |
| `app/ai` | Assistant graph, prompts, tools, retrieval helpers |
| `alembic` | Migrations |
| `data/knowledge` | Clinic PDFs the assistant searches |
| `observability` | Prometheus scrape config and Grafana dashboard |
| `scripts/entrypoint.sh` | API container startup |

`main.py` at the repository root is the project scaffold. Uvicorn loads `app.main:app`.

## Roles

Registration always creates a `patient` user and a patient profile.

| Role | What they can do |
| --- | --- |
| `patient` | Book, list, and reschedule their own appointments. Use the assistant. Read their notifications. |
| `provider` | Created by front desk. Confirm, complete, or cancel their own appointments. Reschedule them. Read the provider directory. |
| `front_desk` | Create providers. List every patient and every appointment. Update any appointment. Read analytics. Queue knowledge ingestion. |

Confirm, complete, and cancel are provider or front-desk actions. A patient cannot move an appointment out of `pending`.

Appointment status transitions:

- `pending` → `confirmed`, `complete`, or `canceled`
- `confirmed` → `complete` or `canceled`
- `complete` and `canceled` do not change again

## Run

Install [Docker](https://docs.docker.com/get-docker/) and Docker Compose. From the repository root, create a `.env` file:

```bash
POSTGRES_USER=smarthealth
POSTGRES_PASSWORD=smarthealth
POSTGRES_DB=smarthealth
SECRET_KEY=replace-with-a-long-random-string
OPENAI_API_KEY=sk-...
```

`DATABASE_URL` and `SECRET_KEY` are required by the app. Compose builds `DATABASE_URL` for the containers. `OPENAI_API_KEY` is required for knowledge ingestion and the assistant.

```bash
docker compose up --build
```

When the API is up:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Temporal UI: http://localhost:8088
- Jaeger: http://localhost:16686
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (anonymous admin is enabled in Compose)

The browser frontend is expected at `http://localhost:5173` or `http://127.0.0.1:5173`. Other origins are rejected by CORS.

### Local API without Compose

Python 3.13 and [uv](https://docs.astral.sh/uv/) match the Docker image. You still need Postgres (with pgvector), Temporal, Redis, and Kafka if you want those paths.

```bash
uv sync
export DATABASE_URL=postgresql+psycopg2://smarthealth:smarthealth@localhost:5433/smarthealth
export SECRET_KEY=replace-with-a-long-random-string
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Run the workers in other terminals when you need them:

```bash
uv run python -m app.worker
uv run python -m app.consumers.appointments
uv run celery -A app.celery_app worker --loglevel=INFO --pool=solo
```

## Configuration

Values come from the environment. `app/core/config.py` loads a `.env` file when one is present. Compose sets the in-cluster addresses.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | required | SQLAlchemy URL |
| `SECRET_KEY` | required | JWT signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime |
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal frontend |
| `TEMPORAL_TASK_QUEUE` | `smarthealth-task-queue` | Queue the API and worker share |
| `BOOKING_HOLD_SECONDS` | `60` | How long a pending booking waits for confirm |
| `KAFKA_BOOTSTRAP_SERVERS` | empty | When empty, the API skips publishing |
| `KAFKA_APPOINTMENTS_TOPIC` | `appointments` | Appointment event topic |
| `KAFKA_CONSUMER_GROUP` | `smarthealth-appointments-logger` | Consumer group id |
| `REDIS_URL` | empty | Celery broker. Falls back to `redis://localhost:6379/0` inside Celery. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | empty | When empty, tracing stays off |
| `OTEL_SERVICE_NAME` | `smarthealth-api` | Service name in Jaeger |
| `CELERY_METRICS_PORT` | `9000` | Celery worker metrics |
| `OPENAI_API_KEY` | empty | Chat and embeddings |
| `CHAT_MODEL` | `gpt-4o-mini` | Assistant model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Ingestion embeddings |
| `EMBEDDING_DIM` | `1536` | Vector size stored in pgvector |
| `KNOWLEDGE_DIR` | `data/knowledge` | PDF directory |
| `KNOWLEDGE_CHUNK_SIZE` | `800` | Characters per chunk |
| `KNOWLEDGE_CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `4` | Chunks retrieved per question |
| `CLINIC_TIMEZONE` | `Asia/Karachi` | Clinic clock for slot tools |
| `CLINIC_OPEN` / `CLINIC_CLOSE` | `09:00` / `17:00` | Clinic hours |
| `CLINIC_DAYS` | `0,1,2,3,4` | Open weekdays, Monday = 0 |
| `SLOT_MINUTES` | `30` | Slot length |

## API

Send `Authorization: Bearer <access_token>` on every route except register, login, health, metrics, and the Temporal ping. Interactive schemas are at `/docs`.

### Auth

| Method | Path | Who |
| --- | --- | --- |
| `POST` | `/auth/register` | Public. Creates a patient. |
| `POST` | `/auth/login` | Public. Returns `{ "access_token", "token_type": "bearer" }`. |
| `GET` | `/auth/me` | Any signed-in user |

### Patients and providers

| Method | Path | Who |
| --- | --- | --- |
| `GET` | `/patients/me` | The signed-in user's patient profile |
| `GET` | `/patients` | Front desk |
| `GET` | `/patients/{id}` | Signed-in user, subject to service checks |
| `POST` | `/providers` | Front desk |
| `GET` | `/providers/me` | The signed-in provider |
| `GET` | `/providers` | Any signed-in user |
| `GET` | `/providers/{id}` | Any signed-in user |

### Appointments

| Method | Path | Who |
| --- | --- | --- |
| `POST` | `/appointments` | Patient. Body includes `provider_id` and `appointment_time`. Starts the Temporal hold. |
| `GET` | `/appointments` | Front desk sees all. Patients and providers see their own. |
| `GET` | `/appointments/{id}` | Owner, or front desk |
| `PATCH` | `/appointments/{id}` | Owning provider or front desk. Body: `{ "action": "confirm" \| "complete" \| "canceled" }`. |
| `POST` | `/appointments/{id}/reschedule` | Patient, owning provider, or front desk, while the appointment is `pending` or `confirmed` |

A slot conflict returns 409. A hold that has already finished returns 409 with "Booking hold expired". Temporal being unreachable returns 503.

### Notifications, analytics, knowledge

| Method | Path | Who |
| --- | --- | --- |
| `GET` | `/notifications` | The signed-in user's notifications |
| `GET` | `/analytics` | Front desk. Totals, cancellation rate, bookings by day. |
| `POST` | `/knowledge/ingest` | Front desk. Queues the Celery ingestion task and returns 202 with a `task_id`. |

### Assistant

| Method | Path | Who |
| --- | --- | --- |
| `POST` | `/assistant/chat` | Any signed-in user. Streams server-sent events. |
| `GET` | `/assistant/conversations` | The caller's conversations |
| `GET` | `/assistant/conversations/{id}/messages` | The caller's messages in that conversation |

### Operations

| Method | Path | Who |
| --- | --- | --- |
| `GET` | `/health` | Public. Process liveness only. It does not check Postgres, Temporal, Kafka, or Redis. |
| `GET` | `/metrics` | Prometheus scrape. Hidden from the OpenAPI schema. |
| `POST` | `/temporal/ping` | Public smoke test. Runs `PingWorkflow` and returns `{"result": "ok"}` when the worker is connected. |

## Temporal

Temporal is used for the booking hold because that flow has to wait, accept a later signal, and keep going if the API process restarts. Celery is not used for this. Celery jobs are short tasks that do not stay open waiting for the next user action.

There is one workflow per appointment. There are no child workflows, workflow queries, cron schedules, or `continue_as_new`.

### `BookingWorkflow`

Defined in `app/workflows/booking.py`. Started from `app/core/temporal.py` by `start_booking_hold`. Signaled by `signal_booking`.

The workflow keeps two in-memory flags, `_confirmed` and `_terminal`. The `resolve` signal sets them:

- `confirm` sets `_confirmed` and leaves the workflow running.
- `complete` or `canceled` sets `_terminal` and ends the workflow.

`run` waits until one of those signals arrives or `hold_seconds` elapses.

- On timeout it runs `release_slot_if_pending`, which cancels the row only if it is still `pending`.
- On confirm it waits again, with no timeout, for `complete` or `canceled`.
- On a terminal signal it runs `apply_appointment_status`.

Workflow code does not open a database session. Activities do, in the worker process, so the workflow stays deterministic and Temporal can replay it. Activity imports sit inside `workflow.unsafe.imports_passed_through()`.

`apply_appointment_status` marks an illegal status transition as a non-retryable application error. Other activity failures use the SDK default retry. Each booking activity has a 30-second start-to-close timeout.

The API writes `confirmed` itself after the confirm signal, because that signal does not finish the workflow. For complete and cancel, the API waits for the workflow result, then calls the same status update again. The second write is a no-op when the status already matches.

Workflow id `booking-{appointment_id}` is the idempotency key. A second start for the same appointment targets the same execution.

### `PingWorkflow`

`POST /temporal/ping` uses `execute_workflow`, so the HTTP call waits until the `ping` activity returns `"ok"`. Each call uses a new id, `ping-{uuid}`.

The worker in `app/worker.py` registers both workflows and the three activities (`ping`, `release_slot_if_pending`, `apply_appointment_status`) on one task queue. It retries the Temporal connection every 2 seconds at startup.

## Events and background jobs

Appointment changes call `NotificationService.record`. That publishes an `AppointmentEvent` to Kafka and also writes the notification and analytics row in the request. Publishing is skipped when `KAFKA_BOOTSTRAP_SERVERS` is empty. A publish failure is logged and does not fail the HTTP request.

The consumer (`app/consumers/appointments.py`) reads the topic, commits the offset only after it enqueues work, and calls:

- `send_notification` — writes the in-app notification if that user, appointment, and event type do not already have one
- `record_analytics` — stores the analytics fact for the event

`ingest_knowledge` reads the PDFs in `data/knowledge`, splits them, embeds the chunks with OpenAI, and stores them in pgvector. Front desk triggers it with `POST /knowledge/ingest`. The Celery service mounts that directory read-only at `/app/data/knowledge`.

## Assistant

`POST /assistant/chat` runs a LangGraph graph in `app/ai/graph.py`. The graph checks for emergency wording, classifies the question, and then either retrieves clinic-document chunks, calls schedule tools, or answers that the question is out of scope. Answers stream back as server-sent events. Conversations and messages are stored per user.

Retrieval uses pgvector. Ingest documents before expecting answers grounded in the clinic PDFs.

The assistant tools are limited to the signed-in user's appointments and to clinic hours configured by `CLINIC_*` and `SLOT_MINUTES`.

## Observability

Each API request gets an `X-Request-ID` (or keeps the one the client sent) and a log line with method, path, status, and duration. `/health` and `/metrics` are not logged and are excluded from Prometheus HTTP metrics and from tracing.

When `OTEL_EXPORTER_OTLP_ENDPOINT` is set, spans go to Jaeger. Compose points the API at `http://jaeger:4317`. Grafana loads the dashboard in `observability/grafana/dashboards/smarthealth.json`.

## Tests and further reading

`docs/archetecture.md` describes the layering. `prds/` holds the original requirement notes, including parts of the domain (billing, reminders) that this codebase does not implement.
