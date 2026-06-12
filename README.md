# BillFlow API

A production-grade multi-tenant invoice and billing REST (Representational State Transfer) API built with FastAPI, async SQLAlchemy, and PostgreSQL. Built as a Day 8 implementation project covering **Async Architecture** and **Dependency Injection (DI)**.

---

## Why This Project

Every real SaaS (Software as a Service) handles billing logic. This project was chosen deliberately:

- Async shines here — DB calls, invoice generation, and aggregations are all I/O (Input/Output) heavy
- DI earns its place — sessions, tenant context, and auth all injected cleanly
- Multi-tenancy enforced at the data layer — the exact pattern needed for Data Softwares
- One aggregation endpoint that does real SQL work — not Python loops over lists

---

## Stack

| Tool | Purpose |
|------|---------|
| FastAPI | Async Python web framework |
| SQLAlchemy 2.0 | Async ORM (Object Relational Mapper) with connection pooling |
| asyncpg | Async PostgreSQL driver |
| PostgreSQL | Primary relational database |
| Pydantic v2 | Data validation and serialization |
| Uvicorn | ASGI (Asynchronous Server Gateway Interface) server |

---

## Project Structure

```
BillFlow_API/
├── app/
│   ├── main.py          # App entry point, router registration, lifespan
│   ├── database.py      # Async engine, session factory, Base, lifespan
│   ├── models.py        # SQLAlchemy table definitions
│   ├── schemas.py       # Pydantic input/output schemas
│   ├── dependencies.py  # get_db() and get_current_tenant() DI functions
│   └── routers/
│       ├── tenants.py   # Tenant CRUD (Create Read Update Delete) routes
│       ├── clients.py   # Client CRUD routes
│       └── invoices.py  # Invoice CRUD + billing summary aggregation
└── requirements.txt
```

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install email-validator

# Create the database in PostgreSQL
psql -U postgres -c "CREATE DATABASE billflow;"

# Run the server
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

## Environment

Update the `DATABASE_URL` in `app/database.py`:

```python
DATABASE_URL = "postgresql+asyncpg://postgres:yourpassword@localhost:5432/billflow"
```

---

## API Endpoints

All client and invoice routes require the `x-tenant-id` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tenants/` | Create a new tenant |
| GET | `/tenants/` | List all tenants |
| POST | `/clients/` | Create a client |
| GET | `/clients/` | List all clients for tenant |
| GET | `/clients/{id}` | Get a single client |
| DELETE | `/clients/{id}` | Delete a client |
| POST | `/invoices/` | Create an invoice |
| GET | `/invoices/` | List all invoices for tenant |
| GET | `/invoices/summary` | Billing summary aggregation |
| PATCH | `/invoices/{id}` | Update invoice status |
| DELETE | `/invoices/{id}` | Delete an invoice |

---

## Core Concepts

### Async/Await — The Real Mechanism

Python by default is synchronous — one thing runs, finishes, then the next starts. If a route hits the database and the DB takes 200ms, the entire thread sits idle for 200ms doing nothing.

Async fixes this:

> Async does not make things faster. It makes your program **useful while waiting**.

When you write `await db.execute(query)`, you tell Python: go start this DB call, and while it is waiting — go handle another request. Come back when the result is ready. This is the **event loop** — a single thread that juggles many tasks by switching between them at `await` points.

Key distinctions:
- `async def` + `await` = cooperative multitasking — ideal for I/O like DB and HTTP calls
- Regular `def` in FastAPI = runs in a threadpool — fine, but cannot yield control
- CPU-heavy work like ML inference = async will not help here

---

### Dependency Injection — The Real Reason

`Depends()` is not just a way to pass things into routes. It is a **contract system**.

The full resolution chain on every request:

```
Request comes in
  → FastAPI calls get_db()                          (opens session)
  → FastAPI calls get_current_tenant(db=<session>)  (validates tenant)
  → FastAPI calls your route(tenant=<tenant>, db=<session>)
  → Route finishes
  → get_db() closes session automatically
```

You never write session management inside a route. You never manually fetch the tenant. You declare what you need and FastAPI delivers it.

---

### Why `yield` and not `return` in `get_db()`

`yield` turns `get_db` into a context manager. Everything before `yield` runs before the route. Everything after runs after — guaranteed, even if the route crashes. This is how the session always gets closed and rolled back on errors.

---

### Multi-Tenancy at the Data Layer

Every query filters by `tenant_id`:

```python
select(Client).where(
    Client.id == client_id,
    Client.tenant_id == tenant.id   # isolation enforced here
)
```

A tenant can never reach another tenant's data — not because of business logic in the route, but because the query itself is scoped. This is the pattern required at scale.

---

### Aggregation Query — One DB Round Trip

The billing summary computes everything inside PostgreSQL:

```python
select(
    func.count(Invoice.id).label("total_invoices"),
    func.coalesce(func.sum(Invoice.amount), 0).label("total_amount"),
    func.coalesce(
        func.sum(Invoice.amount).filter(Invoice.status == InvoiceStatus.paid), 0
    ).label("paid_amount"),
)
```

`func.sum().filter()` is a conditional aggregation — PostgreSQL evaluates the filter per row inside the aggregation. One DB round trip regardless of invoice count. No Python loops.

---

## Understanding SQLAlchemy Scalar Methods

When you run `await db.execute(select(...))` you get a result object — not your data. Scalar methods extract the actual data:

| Method | When to use | Behavior |
|--------|-------------|---------|
| `scalar_one_or_none()` | Fetching one specific record | Returns object or None. Raises error if 2+ rows |
| `scalars().all()` | Fetching many records | Returns a list of model objects |
| `.one()` | Aggregation queries | Returns exactly one row. Raises error if 0 or 2+ |

**Why "scalar" at all:** A raw SQL result is a grid of rows and columns. "Scalar" collapses that grid down to just the mapped Python objects, stripping the row/column wrapper. Without `.scalars()` you get `Row` objects. With it you get your actual `Client`, `Invoice`, or `Tenant` objects directly.

---

## Errors Encountered and How They Were Fixed

### Error 1 — AttributeError: type object 'Client' has no attribute '_sa_instance_state'

**Cause:** `db.add(Client)` was called with the class instead of an instance.

```python
# Wrong
db.add(Client)

# Correct
client = Client(tenant_id=tenant.id, name=payload.name, email=payload.email)
db.add(client)
```

**Lesson:** Always pass the lowercase instance variable to `db.add()` and `db.delete()` — never the uppercase class name.

---

### Error 2 — UnmappedInstanceError: Class is not mapped

**Cause:** Same root issue. The error message confirmed it: `was a class (app.models.Client) supplied where an instance was required`.

**Fix:** Reviewed all `db.add()` and `db.delete()` calls across both routers and confirmed each received the instantiated object, not the class.

---

### Error 3 — DBAPIError: Can't subtract offset-naive and offset-aware datetimes

**Cause:** The `due_date` coming in from the API was timezone-aware (UTC info attached), but the `DateTime` database columns were timezone-naive (no timezone info). PostgreSQL rejected the mismatch.

**Fix:** Updated all `DateTime` columns in `models.py` to use `timezone=True`:

```python
due_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

**Why `timezone=True` is the production-correct approach:** Storing naive datetimes causes bugs when users span multiple timezones — which any global SaaS will encounter.

---


