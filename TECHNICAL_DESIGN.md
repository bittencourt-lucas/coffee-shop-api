# Technical Design Document

## Table of Contents

- [1. Overview](#1-overview)
- [2. Architecture](#2-architecture)
  - [2.1 Clean Architecture](#21-clean-architecture)
  - [2.2 Dependency Flow](#22-dependency-flow)
  - [2.3 Project Structure](#23-project-structure)
- [3. Technology Stack and Trade-offs](#3-technology-stack-and-trade-offs)
  - [3.1 FastAPI](#31-fastapi)
  - [3.2 SQLite](#32-sqlite)
  - [3.3 Header-Based Authentication](#33-header-based-authentication)
  - [3.4 Other Dependencies](#34-other-dependencies)
- [4. API Endpoints](#4-api-endpoints)
  - [4.1 Health Check](#41-health-check)
  - [4.2 Get Menu](#42-get-menu)
  - [4.3 Create Order](#43-create-order)
  - [4.4 Get Order Detail](#44-get-order-detail)
  - [4.5 Update Order Status](#45-update-order-status)
- [5. Core Domain Model](#5-core-domain-model)
  - [5.1 Entities](#51-entities)
  - [5.2 Order Status State Machine](#52-order-status-state-machine)
  - [5.3 Roles](#53-roles)
- [6. Key Design Patterns](#6-key-design-patterns)
  - [6.1 Repository Pattern](#61-repository-pattern)
  - [6.2 Use Case Pattern](#62-use-case-pattern)
  - [6.3 Dependency Injection](#63-dependency-injection)
- [7. External Service Integrations](#7-external-service-integrations)
  - [7.1 Payment Service](#71-payment-service)
  - [7.2 Notification Service](#72-notification-service)
- [8. Security Measures](#8-security-measures)
  - [8.1 CORS Policy](#81-cors-policy)
  - [8.2 Rate Limiting](#82-rate-limiting)
  - [8.3 Input Validation](#83-input-validation)
  - [8.4 Error Sanitization](#84-error-sanitization)
  - [8.5 HTTP Timeouts](#85-http-timeouts)
  - [8.6 Role-Based Access Control](#86-role-based-access-control)
- [9. Database Design](#9-database-design)
  - [9.1 Schema](#91-schema)
  - [9.2 Migrations](#92-migrations)
  - [9.3 Seeding](#93-seeding)
- [10. Data Flow](#10-data-flow)
  - [10.1 Order Creation](#101-order-creation)
  - [10.2 Status Update](#102-status-update)
- [11. Caveats, Pitfalls, and Production Considerations](#11-caveats-pitfalls-and-production-considerations)
  - [11.1 Deliberate Simplifications](#111-deliberate-simplifications)
  - [11.2 Known Limitations](#112-known-limitations)
  - [11.3 Production Readiness Checklist](#113-production-readiness-checklist)

---

## 1. Overview

The Coffee Shop API is a REST API built with FastAPI that simulates a coffee shop order management system. It supports menu browsing, order creation with external payment processing, order tracking, and status management with role-based access control.

The API is designed as a demonstration project that showcases clean architecture principles, proper separation of concerns, and common backend patterns — while making deliberate trade-offs in areas like authentication and database choice for the sake of simplicity.

---

## 2. Architecture

### 2.1 Clean Architecture

The project follows Clean Architecture, organizing code into three concentric layers with strict dependency rules:

- **Core Layer** (`src/core/`): Pure Python with zero framework dependencies. Contains entities (dataclasses), enums, abstract repository interfaces (ABCs), abstract service interfaces, and domain exceptions. This layer defines *what* the application does without knowing *how*.

- **Use Cases Layer** (`src/use_cases/`): Application-specific business rules. Each use case is a single class with an `execute()` method that orchestrates core entities, repositories, and services. Depends only on the core layer.

- **Infrastructure Layer** (`src/infrastructure/`): All framework-specific code — FastAPI routes, Pydantic schemas, SQLAlchemy models, database repositories, HTTP service clients, middleware, and configuration. This is the only layer that depends on external libraries.

### 2.2 Dependency Flow

Dependencies flow strictly inward:

```
Infrastructure → Use Cases → Core
```

The infrastructure layer depends on use cases, which depend on core. The core layer never imports from use cases or infrastructure. This is enforced through abstract interfaces: core defines `AbstractPaymentService` and `AbstractProductRepository`, while infrastructure provides the concrete implementations.

### 2.3 Project Structure

```
src/
├── core/                          # Pure domain logic
│   ├── entities/                  # Product, Order, OrderDetail, OrderItem, MenuItem, MenuVariation
│   ├── enums/                     # OrderStatus, Role
│   ├── repositories/              # AbstractProductRepository, AbstractOrderRepository
│   ├── services/                  # AbstractPaymentService, AbstractNotificationService
│   └── exceptions.py              # InvalidProductError, InvalidStatusTransitionError, PaymentFailedError
│
├── use_cases/                     # Application business rules
│   ├── order/                     # CreateOrder, GetOrderDetail, UpdateOrderStatus
│   └── product/                   # GetMenu
│
├── infrastructure/                # Framework-specific implementations
│   ├── api/
│   │   ├── routes/                # FastAPI routers (healthcheck, product, order)
│   │   ├── schemas/               # Pydantic request/response models
│   │   ├── middleware/            # RoleMiddleware, rate_limit (slowapi)
│   │   └── dependencies.py       # DI wiring and role authorization
│   ├── database/
│   │   ├── models/                # SQLAlchemy table definitions
│   │   ├── repositories/          # Concrete repository implementations
│   │   ├── connection.py          # Database instance and metadata
│   │   └── seed.py                # Product catalog seeding
│   ├── services/                  # PaymentService (with retries), NotificationService (fire-and-forget)
│   └── settings.py                # pydantic-settings configuration
│
└── main.py                        # App entry point, lifespan, middleware registration
```

---

## 3. Technology Stack and Trade-offs

### 3.1 FastAPI

**Why FastAPI over alternatives:**

| Criterion | FastAPI | Flask | Django REST Framework |
|---|---|---|---|
| Async support | Native (built on Starlette/ASGI) | Requires extensions | Limited |
| Request validation | Automatic via Pydantic | Manual or with extensions | Serializers |
| API documentation | Auto-generated OpenAPI/Swagger | Manual or Flask-RESTx | Via DRF schema |
| Performance | High (async I/O, Uvicorn) | Moderate (sync by default) | Moderate |
| Learning curve | Low-medium | Low | Medium-high |
| Dependency injection | Built-in `Depends()` system | None built-in | None built-in |

FastAPI was chosen because it provides native async support (critical for non-blocking I/O with the database and external HTTP calls), automatic request/response validation through Pydantic, built-in dependency injection that maps cleanly to clean architecture, and auto-generated API documentation. The trade-off is a smaller ecosystem compared to Django, but for a focused API service this is not a concern.

### 3.2 SQLite

**This is a deliberate simplification.** SQLite was chosen because:

- Zero configuration — no database server to install or manage
- File-based storage makes the project trivially portable
- Perfect for development, demos, and small-scale usage
- Async access via `aiosqlite` integrates well with FastAPI's async model

**Why this would NOT be acceptable in production:**

- **No concurrent write support**: SQLite uses file-level locking. Under concurrent write load (multiple order creations), requests will serialize or fail.
- **No network access**: SQLite runs in-process. Multiple application instances cannot share the same database file safely.
- **No built-in replication or backup**: No point-in-time recovery, no read replicas, no streaming replication.
- **Limited data types**: No native UUID, JSON, or array types. UUIDs are stored as strings, which prevents database-level UUID validation.
- **No connection pooling**: Each connection is a file handle, not a pooled network socket.

**Production alternative**: PostgreSQL with `asyncpg` would be the natural choice. It supports concurrent connections, proper UUID columns, JSONB, row-level locking, replication, and integrates with the same `databases` library used here — making the migration straightforward since only the connection string and SQLAlchemy dialect would change.

### 3.3 Header-Based Authentication

**This is a deliberate simplification.** The API uses a plain `X-Role` header to determine user roles:

- The `RoleMiddleware` reads the `X-Role` header from every request
- If absent, the role defaults to `CUSTOMER`
- If present, it must be `CUSTOMER` or `MANAGER` (otherwise returns 400)
- The role is stored in `request.state.role` and checked by `require_roles()` in route dependencies

**Why this is fundamentally insecure:**

- **No authentication**: Any client can claim to be a `MANAGER` by setting `X-Role: MANAGER`. There is no identity verification whatsoever.
- **No authorization tokens**: No JWT, OAuth2, session cookies, or API keys. The header is trusted at face value.
- **No user identity**: There is no concept of "who" is making the request — only "what role" they claim to have.
- **Trivially bypassable**: A simple `curl -H "X-Role: MANAGER"` grants full manager access.

**What production would require:**

- **Authentication**: JWT tokens (via OAuth2/OpenID Connect) or session-based auth with a proper identity provider. FastAPI has built-in support for OAuth2 with `fastapi.security`.
- **Authorization**: Role claims should come from the token payload (signed by the auth server), not from a client-supplied header.
- **User identity**: Orders should be associated with authenticated user IDs, enabling order history, ownership checks, and audit trails.
- **Token validation**: Signature verification, expiration checks, audience validation, and token revocation.

### 3.4 Other Dependencies

| Dependency | Purpose | Why chosen |
|---|---|---|
| `databases[aiosqlite]` | Async database access | Lightweight async layer compatible with SQLAlchemy table definitions |
| `Alembic` | Database migrations | Industry standard for SQLAlchemy; version-controlled schema changes |
| `httpx` | Async HTTP client | Modern, async-native alternative to `requests`; used for payment and notification calls |
| `pydantic-settings` | Configuration management | Type-safe environment variable loading with the `COFFEE_SHOP_` prefix convention |
| `slowapi` | Rate limiting | Simple decorator-based rate limiting built on top of `limits` library |

---

## 4. API Endpoints

### 4.1 Health Check

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/healthcheck` |
| **Auth** | None |
| **Rate Limit** | None |
| **Response** | `{"status": "ok"}` |
| **Status Code** | `200 OK` |

Simple liveness probe. Returns a static response to confirm the service is running.

### 4.2 Get Menu

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/menu` |
| **Auth** | `CUSTOMER` or `MANAGER` |
| **Rate Limit** | None |

**Response** (`200 OK`):
```json
[
  {
    "name": "Latte",
    "base_price": 4.00,
    "variations": [
      { "id": "uuid", "variation": "Pumpkin Spice", "unit_price": 4.50 },
      { "id": "uuid", "variation": "Vanilla", "unit_price": 4.30 }
    ]
  }
]
```

Products are grouped by name and base price. Each variation's `unit_price` is calculated as `base_price + price_change`.

### 4.3 Create Order

| Property | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/orders/` |
| **Auth** | Any role |
| **Rate Limit** | 10 requests/minute per IP |

**Request**:
```json
{
  "product_ids": ["uuid-1", "uuid-2"]
}
```
- `product_ids`: 1 to 50 valid product UUIDs

**Response** (`201 Created`):
```json
{
  "id": "uuid",
  "status": "WAITING",
  "total_price": 8.50,
  "product_ids": ["uuid-1", "uuid-2"]
}
```

**Error Responses**:

| Status | Condition |
|---|---|
| `422` | Invalid/missing product IDs |
| `429` | Rate limit exceeded |
| `502` | Payment processing failed after retries |

**Flow**: Validate products exist, calculate total, process payment (3 retries), persist order atomically, return response.

### 4.4 Get Order Detail

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/orders/{order_id}` |
| **Auth** | Any role |
| **Rate Limit** | None |

**Response** (`200 OK`):
```json
{
  "id": "uuid",
  "status": "WAITING",
  "total_price": 8.50,
  "created_at": "2026-03-30T12:34:56",
  "items": [
    { "id": "uuid", "name": "Latte", "variation": "Pumpkin Spice", "unit_price": 4.50 }
  ]
}
```

**Error Responses**:

| Status | Condition |
|---|---|
| `404` | Order not found |

### 4.5 Update Order Status

| Property | Value |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/orders/{order_id}/status` |
| **Auth** | `MANAGER` only |
| **Rate Limit** | None |

**Request**:
```json
{
  "status": "PREPARATION"
}
```

**Response** (`200 OK`):
```json
{
  "id": "uuid",
  "status": "PREPARATION",
  "total_price": 8.50,
  "product_ids": ["uuid"]
}
```

**Error Responses**:

| Status | Condition |
|---|---|
| `403` | Caller is not a `MANAGER` |
| `404` | Order not found |
| `422` | Invalid status transition |

---

## 5. Core Domain Model

### 5.1 Entities

All entities are Python dataclasses defined in `src/core/entities/`. They have no framework dependencies.

- **Product**: `id`, `name`, `base_price`, `variation`, `price_change`
- **Order**: `id`, `status`, `total_price`, `product_ids`
- **OrderDetail**: `id`, `status`, `total_price`, `created_at`, `items` (list of `OrderItem`)
- **OrderItem**: `id`, `name`, `variation`, `unit_price`
- **MenuItem**: `name`, `base_price`, `variations` (list of `MenuVariation`)
- **MenuVariation**: `id`, `variation`, `unit_price`

### 5.2 Order Status State Machine

Orders follow a strictly linear status progression:

```
WAITING → PREPARATION → READY → DELIVERED
```

Transitions are enforced by a hardcoded map in the `UpdateOrderStatus` use case:

```python
_TRANSITIONS = {
    OrderStatus.WAITING: OrderStatus.PREPARATION,
    OrderStatus.PREPARATION: OrderStatus.READY,
    OrderStatus.READY: OrderStatus.DELIVERED,
}
```

Any out-of-sequence transition (e.g., `WAITING → READY` or `DELIVERED → WAITING`) raises `InvalidStatusTransitionError`, which the route handler converts to a `422` response. There is no way to skip steps or move backwards.

### 5.3 Roles

Two roles exist as a `str` enum:

- **CUSTOMER**: Can browse the menu, create orders, and view order details.
- **MANAGER**: Can do everything a customer can, plus update order statuses.

---

## 6. Key Design Patterns

### 6.1 Repository Pattern

Abstract interfaces are defined in `src/core/repositories/` using Python ABCs. Concrete implementations live in `src/infrastructure/database/repositories/`. This decouples the domain logic from the database:

- `AbstractProductRepository` defines `list_all()` and `get_by_ids()`
- `AbstractOrderRepository` defines `create()`, `get_by_id()`, `get_detail_by_id()`, and `update_status()`

The same approach applies to external services (`AbstractPaymentService`, `AbstractNotificationService`). This enables straightforward testing — tests inject mocks or stubs without touching the database or external APIs.

### 6.2 Use Case Pattern

Each use case is a single-responsibility class with an `execute()` method:

- `CreateOrder.execute(product_ids)` — validates, calculates, pays, persists
- `GetOrderDetail.execute(order_id)` — retrieves full order with item details
- `UpdateOrderStatus.execute(order_id, new_status)` — validates transition, updates, notifies
- `GetMenu.execute()` — fetches and groups products into menu items

Use cases receive their dependencies (repositories, services) through their constructor, making them easy to instantiate in route handlers via FastAPI's `Depends()`.

### 6.3 Dependency Injection

All wiring happens in `src/infrastructure/api/dependencies.py`. FastAPI's `Depends()` system provides:

- **Repositories**: `get_product_repository()`, `get_order_repository()` — instantiated with the database connection
- **Services**: `get_payment_service()`, `get_notification_service()` — instantiated as singletons per request
- **Authorization**: `require_roles(*allowed_roles)` — returns a dependency that checks `request.state.role` and raises `403` if unauthorized

Tests override these dependencies via `app.dependency_overrides` to inject mocks.

---

## 7. External Service Integrations

### 7.1 Payment Service

Processes payments before an order is persisted. This is a blocking call in the order creation flow — if payment fails, the order is never created.

| Property | Value |
|---|---|
| **URL** | Configurable via `COFFEE_SHOP_PAYMENT_URL` |
| **Default** | `https://challenge.trio.dev/api/v1/payment` |
| **Request** | `POST` with `{"value": <total_price>}` |
| **Timeout** | 10 seconds per attempt |
| **Retries** | 3 attempts with no backoff delay |
| **Failure** | Raises `PaymentFailedError` after all retries exhausted |

The retry strategy is intentionally simple (immediate retries, no exponential backoff). In production, this should use exponential backoff with jitter to avoid thundering herd problems, and potentially a circuit breaker to fail fast when the payment service is known to be down.

### 7.2 Notification Service

Sends status change notifications after an order's status is updated. This is a non-blocking, fire-and-forget call.

| Property | Value |
|---|---|
| **URL** | Configurable via `COFFEE_SHOP_NOTIFICATION_URL` |
| **Default** | `https://challenge.trio.dev/api/v1/notification` |
| **Request** | `POST` with `{"status": "<new_status>"}` |
| **Timeout** | 10 seconds |
| **Retries** | None |
| **Invocation** | `asyncio.create_task()` — non-blocking |

Failures are logged but never propagate to the client. The status update succeeds regardless of whether the notification was delivered. This means notifications can be silently lost — acceptable for a demo, but production would require a message queue (e.g., RabbitMQ, SQS) or an outbox pattern to guarantee delivery.

---

## 8. Security Measures

### 8.1 CORS Policy

Configured in `main.py`:

- **Allowed Origins**: `http://localhost:3000` only
- **Allowed Methods**: `GET`, `POST`, `PATCH`
- **Allowed Headers**: `X-Role`, `Content-Type`

This restricts browser-based cross-origin requests to a specific frontend origin. In production, the allowed origins list should be configurable via environment variables and match the actual frontend domain(s).

### 8.2 Rate Limiting

Applied via `slowapi` with the `@limiter.limit()` decorator:

- **Scope**: `POST /orders/` only
- **Limit**: 10 requests per minute per client IP
- **Key function**: `get_remote_address` (extracts IP from the request)
- **Exceeded response**: `429 Too Many Requests`

Rate limiting is disabled during tests (`limiter.enabled = False`). In production behind a reverse proxy, the key function should use `X-Forwarded-For` or a trusted proxy header to avoid rate limiting the proxy's IP instead of the actual client.

### 8.3 Input Validation

Pydantic models enforce:

- `product_ids` must be a list of valid UUIDs with 1-50 items
- `status` must be a valid `OrderStatus` enum value
- `order_id` path parameters must be valid UUIDs

Invalid payloads are automatically rejected with `422 Unprocessable Entity` before reaching route handler logic.

### 8.4 Error Sanitization

Internal error details are never exposed to clients:

- Payment failures return a generic `"Payment could not be processed"` message (502). The actual error reason is logged server-side.
- Notification failures are entirely invisible to clients.
- Database errors result in generic 500 responses, not stack traces.

This prevents information leakage that could help an attacker understand the system's internals.

### 8.5 HTTP Timeouts

All outbound HTTP calls (payment, notification) use a 10-second timeout. This prevents the application from hanging indefinitely if an external service becomes unresponsive.

### 8.6 Role-Based Access Control

The `require_roles()` dependency factory checks the role stored in `request.state.role` (set by `RoleMiddleware`) against the allowed roles for each endpoint:

- `GET /menu` — `CUSTOMER`, `MANAGER`
- `PATCH /orders/{id}/status` — `MANAGER` only
- All other endpoints — any role (including the default `CUSTOMER`)

Unauthorized access returns `403 Forbidden` with a message indicating the caller's role and the fact that it is not permitted.

---

## 9. Database Design

### 9.1 Schema

Three tables:

**`products`**

| Column | Type | Constraints |
|---|---|---|
| `id` | String (UUID) | Primary Key |
| `name` | String | NOT NULL |
| `base_price` | Float | NOT NULL |
| `variation` | String | NOT NULL |
| `price_change` | Float | NOT NULL |

**`orders`**

| Column | Type | Constraints |
|---|---|---|
| `id` | String (UUID) | Primary Key |
| `status` | String | NOT NULL |
| `total_price` | Float | NOT NULL |
| `created_at` | DateTime | NOT NULL, server default: now() |

**`order_products`** (junction table)

| Column | Type | Constraints |
|---|---|---|
| `order_id` | String (UUID) | Foreign Key → orders.id |
| `product_id` | String (UUID) | Foreign Key → products.id |

UUIDs are stored as strings because SQLite has no native UUID type. The repository layer handles conversion between `str` and `uuid.UUID`.

### 9.2 Migrations

Managed by Alembic. Migration history:

1. **Initial schema** — creates products, orders, and order_products tables
2. **Remove users table** — drops an earlier user-related table that was superseded by header-based role checks
3. **Add created_at** — adds the `created_at` timestamp column to orders

Run migrations with: `alembic upgrade head`

### 9.3 Seeding

On application startup, `seed_catalog()` checks if the `products` table is empty. If so, it inserts 13 products across 5 categories:

| Name | Base Price | Variations |
|---|---|---|
| Latte | $4.00 | Pumpkin Spice (+$0.50), Vanilla (+$0.30), Hazelnut (+$0.40) |
| Espresso | $2.50 | Single Shot (+$0.00), Double Shot (+$1.00) |
| Macchiato | $4.00 | Caramel (+$0.50), Vanilla (+$0.30) |
| Iced Coffee | $3.50 | Regular (+$0.00), Sweetened (+$0.30), Extra Ice (+$0.20) |
| Donuts | $2.00 | Glazed (+$0.00), Jelly (+$0.30), Boston Cream (+$0.50) |

Seeding is idempotent — if the table already has data, it is skipped entirely.

---

## 10. Data Flow

### 10.1 Order Creation

```
Client
  │
  ▼
POST /orders/ { product_ids: [...] }
  │
  ├─ RoleMiddleware: extract X-Role (default: CUSTOMER)
  ├─ Rate Limiter: check 10/min per IP
  │
  ▼
CreateOrder.execute(product_ids)
  │
  ├─ 1. ProductRepository.get_by_ids() ──► Validate all IDs exist
  │     └─ If missing → InvalidProductError → 422
  │
  ├─ 2. Calculate total_price = Σ(base_price + price_change)
  │
  ├─ 3. PaymentService.process(total_price) ──► External HTTP call
  │     ├─ Retry up to 3 times
  │     └─ If all fail → PaymentFailedError → 502
  │
  ├─ 4. OrderRepository.create(order) ──► Atomic DB transaction
  │     ├─ INSERT into orders
  │     └─ INSERT into order_products (one row per product)
  │
  ▼
201 Created { id, status: "WAITING", total_price, product_ids }
```

### 10.2 Status Update

```
Client (MANAGER)
  │
  ▼
PATCH /orders/{id}/status { status: "PREPARATION" }
  │
  ├─ RoleMiddleware: extract X-Role
  ├─ require_roles(MANAGER): verify role → 403 if not MANAGER
  │
  ▼
UpdateOrderStatus.execute(order_id, new_status)
  │
  ├─ 1. OrderRepository.get_by_id() ──► Fetch current order
  │     └─ If not found → 404
  │
  ├─ 2. Validate transition: _TRANSITIONS[current] == new_status
  │     └─ If invalid → InvalidStatusTransitionError → 422
  │
  ├─ 3. OrderRepository.update_status() ──► UPDATE orders SET status
  │
  ├─ 4. NotificationService.notify(status) ──► Fire-and-forget (asyncio.create_task)
  │     └─ Failures logged, never propagated
  │
  ▼
200 OK { id, status: "PREPARATION", total_price, product_ids }
```

---

## 11. Caveats, Pitfalls, and Production Considerations

### 11.1 Deliberate Simplifications

The following choices were made intentionally to keep the project simple and focused on demonstrating clean architecture patterns. They are **not** suitable for production.

**SQLite as the database**: Chosen for zero-configuration portability. See [Section 3.2](#32-sqlite) for the full discussion. A production deployment must use a proper RDBMS (PostgreSQL recommended) to support concurrent access, replication, and proper data types.

**Header-based role "authentication"**: The `X-Role` header is trusted at face value with no verification. See [Section 3.3](#33-header-based-authentication) for the full discussion. A production deployment must implement proper authentication (JWT/OAuth2) with cryptographically signed tokens and a real identity provider.

**No user identity or ownership**: Orders are not associated with any user. Anyone can view any order by ID. In production, orders must be tied to authenticated users, and access must be scoped — customers should only see their own orders.

### 11.2 Known Limitations

**Payment retry without backoff**: The payment service retries immediately 3 times with no delay between attempts. Under sustained payment service degradation, this amplifies load on the failing service. Production should use exponential backoff with jitter and consider a circuit breaker pattern.

**Notification delivery is not guaranteed**: Notifications are fire-and-forget via `asyncio.create_task()`. If the notification service is down or the application process crashes after updating the status but before the notification task completes, the notification is lost. Production should use a message queue or transactional outbox pattern.

**No idempotency on order creation**: If a client retries a `POST /orders/` request (e.g., due to a network timeout after the server processed it), a duplicate order will be created and payment will be charged again. Production should support idempotency keys to prevent duplicate processing.

**Float arithmetic for prices**: Prices are stored and calculated as Python floats, which can introduce floating-point precision errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). The use of `round(..., 2)` mitigates this in most cases, but production financial calculations should use `Decimal` types throughout.

**No pagination on menu or order list**: The menu endpoint returns all products in a single response. This is fine for a small catalog (13 items), but would not scale to hundreds or thousands of products. There is no order listing endpoint at all.

**Rate limiting by IP only**: Behind a reverse proxy or NAT, many clients may share the same IP address, causing legitimate users to be rate-limited. In production, rate limiting should be tied to authenticated user identity or API keys.

**Single CORS origin**: Only `http://localhost:3000` is allowed. This must be configurable for real deployments.

**No request logging or tracing**: While the payment and notification services log their operations, there is no structured request logging, correlation IDs, or distributed tracing. Production APIs need observability through request logs, metrics, and traces.

### 11.3 Production Readiness Checklist

If this project were to go live, the following changes would need to be implemented:

| Area | Current State | Required Change |
|---|---|---|
| **Database** | SQLite (file-based) | PostgreSQL with connection pooling |
| **Authentication** | Trusted `X-Role` header | JWT/OAuth2 with token validation |
| **Authorization** | Role in header | Claims from signed tokens; ownership checks |
| **User identity** | None | User model; orders tied to user IDs |
| **Payment retries** | Immediate, 3 attempts | Exponential backoff with jitter; circuit breaker |
| **Notifications** | Fire-and-forget | Message queue (RabbitMQ/SQS) or outbox pattern |
| **Idempotency** | None | Idempotency keys on order creation |
| **Price precision** | Python `float` | `Decimal` types end-to-end |
| **CORS** | Hardcoded localhost | Configurable via environment variables |
| **Rate limiting** | Per-IP only | Per-user or per-API-key |
| **Observability** | Basic logging | Structured logs, metrics, distributed tracing |
| **Secrets management** | Environment variables | Vault or cloud secrets manager |
| **Deployment** | Local dev server | Containerized (Docker), orchestrated (K8s), with health checks and graceful shutdown |
| **API versioning** | None | URL prefix (`/v1/`) or header-based versioning |
| **Testing** | Unit + integration | Add load testing, contract testing, and end-to-end tests |
