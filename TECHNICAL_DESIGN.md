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
  - [3.3 JWT Authentication](#33-jwt-authentication)
  - [3.4 Other Dependencies](#34-other-dependencies)
- [4. API Endpoints](#4-api-endpoints)
  - [4.1 Health Check](#41-health-check)
  - [4.2 Get Menu](#42-get-menu)
  - [4.3 Create User](#43-create-user)
  - [4.4 Get User](#44-get-user)
  - [4.5 Sign In](#45-sign-in)
  - [4.6 Create Order](#46-create-order)
  - [4.7 Get Order Detail](#47-get-order-detail)
  - [4.8 Update Order Status](#48-update-order-status)
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
  - [8.6 JWT Authentication and Role Extraction](#86-jwt-authentication-and-role-extraction)
  - [8.7 Password Security](#87-password-security)
- [9. Database Design](#9-database-design)
  - [9.1 Schema](#91-schema)
  - [9.2 Migrations](#92-migrations)
  - [9.3 Seeding](#93-seeding)
- [10. Data Flow](#10-data-flow)
  - [10.1 User Registration and Sign-In](#101-user-registration-and-sign-in)
  - [10.2 Order Creation](#102-order-creation)
  - [10.3 Status Update](#103-status-update)
- [11. Caveats, Pitfalls, and Production Considerations](#11-caveats-pitfalls-and-production-considerations)
  - [11.1 Deliberate Simplifications](#111-deliberate-simplifications)
  - [11.2 Known Limitations](#112-known-limitations)
  - [11.3 Production Readiness Checklist](#113-production-readiness-checklist)

---

## 1. Overview

The Coffee Shop API is a REST API built with FastAPI that simulates a coffee shop order management system. It supports user registration, JWT-based authentication, menu browsing, order creation with external payment processing, order tracking, and status management with role-based access control.

The API is designed as a demonstration project that showcases clean architecture principles, proper separation of concerns, and common backend patterns — while making deliberate trade-offs in database choice and a few operational areas for the sake of simplicity.

---

## 2. Architecture

### 2.1 Clean Architecture

The project follows Clean Architecture, organizing code into three concentric layers with strict dependency rules:

- **Core Layer** (`src/core/`): Pure Python with zero framework dependencies. Contains entities (dataclasses), enums, abstract repository interfaces (ABCs), abstract service interfaces, and domain exceptions. This layer defines *what* the application does without knowing *how*.

- **Use Cases Layer** (`src/use_cases/`): Application-specific business rules. Each use case is a single class with an `execute()` method that orchestrates core entities, repositories, and services. Depends only on the core layer.

- **Infrastructure Layer** (`src/infrastructure/`): All framework-specific code — FastAPI routes, Pydantic schemas, SQLAlchemy models, database repositories, HTTP service clients, middleware, auth utilities, and configuration. This is the only layer that depends on external libraries.

### 2.2 Dependency Flow

Dependencies flow strictly inward:

```
Infrastructure → Use Cases → Core
```

The infrastructure layer depends on use cases, which depend on core. The core layer never imports from use cases or infrastructure. This is enforced through abstract interfaces: core defines `AbstractPaymentService` and `AbstractProductRepository`, while infrastructure provides the concrete implementations.

> **Note**: `src/infrastructure/auth/` (password hashing, JWT creation) is imported directly by use cases (`CreateUser`, `SignIn`). This is the only deliberate inward exception — the auth utilities contain no framework dependencies and act as pure helper functions, so the coupling is low-risk. A stricter approach would wrap them behind an interface in `core/services/`.

### 2.3 Project Structure

```
src/
├── core/                          # Pure domain logic
│   ├── entities/                  # Product, Order, OrderDetail, OrderItem, MenuItem, MenuVariation, User
│   ├── enums/                     # OrderStatus, Role
│   ├── repositories/              # AbstractProductRepository, AbstractOrderRepository,
│   │                              # AbstractUserRepository, AbstractIdempotencyRepository
│   ├── services/                  # AbstractPaymentService, AbstractNotificationService
│   └── exceptions.py              # InvalidProductError, InvalidStatusTransitionError,
│                                  # PaymentFailedError, InvalidCredentialsError
│
├── use_cases/                     # Application business rules
│   ├── order/                     # CreateOrder, GetOrderDetail, UpdateOrderStatus
│   ├── product/                   # GetMenu
│   └── user/                      # CreateUser, GetUser, SignIn
│
├── infrastructure/                # Framework-specific implementations
│   ├── api/
│   │   ├── routes/                # FastAPI routers (healthcheck, product, order, user, auth)
│   │   ├── schemas/               # Pydantic request/response models
│   │   ├── middleware/            # RoleMiddleware (JWT extraction), rate_limit (slowapi)
│   │   └── dependencies.py       # DI wiring and role authorization
│   ├── auth/
│   │   ├── jwt.py                 # create_access_token (python-jose, HS256)
│   │   └── password.py            # hash_password / verify_password (bcrypt)
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

### 3.3 JWT Authentication

The API uses JWT (JSON Web Tokens) for authentication and role-based access control. Tokens are issued by `POST /auth/sign-in` after verifying the user's email and bcrypt-hashed password.

**Token structure** (HS256-signed payload):

```json
{
  "sub": "<user_id>",
  "role": "CUSTOMER",
  "exp": 1749000000
}
```

**Role extraction**: `RoleMiddleware` decodes the token from the `Authorization: Bearer <token>` header on every request and sets `request.state.role`. No database lookup is needed — the role is embedded directly in the token claims. If no token is present, the middleware defaults to `Role.CUSTOMER`, allowing public endpoints to remain accessible without authentication. If a token is present but invalid or expired, the middleware returns `401` immediately.

**Configuration** (all overridable via `COFFEE_SHOP_*` environment variables):

| Setting | Default | Description |
|---|---|---|
| `jwt_secret_key` | `change-me-in-production` | HMAC signing key — **must be overridden** |
| `jwt_algorithm` | `HS256` | Signing algorithm |
| `jwt_expiration_minutes` | `60` | Token lifetime |

**Trade-offs of embedding role in the token:**
- **Pro**: No per-request database lookup; horizontally scalable without shared session state.
- **Con**: If a user's role is changed in the database, their existing token still carries the old role until it expires. A production system may need a token revocation mechanism (e.g., a denylist in Redis) or shorter token lifetimes to bound this window.

### 3.4 Other Dependencies

| Dependency | Purpose | Why chosen |
|---|---|---|
| `databases[aiosqlite]` | Async database access | Lightweight async layer compatible with SQLAlchemy table definitions |
| `Alembic` | Database migrations | Industry standard for SQLAlchemy; version-controlled schema changes |
| `httpx` | Async HTTP client | Modern, async-native alternative to `requests`; used for payment and notification calls |
| `pydantic-settings` | Configuration management | Type-safe environment variable loading with the `COFFEE_SHOP_` prefix convention |
| `slowapi` | Rate limiting | Simple decorator-based rate limiting built on top of `limits` library |
| `python-jose[cryptography]` | JWT encoding/decoding | Widely used, supports multiple algorithms; `[cryptography]` extra enables RS256/ES256 for future upgrades |
| `bcrypt` | Password hashing | Industry-standard adaptive hash function; resistant to brute-force via cost factor |

**Why bcrypt directly instead of passlib**: `passlib` 1.7.x has a known incompatibility with `bcrypt >= 4.0.0` (the `__about__` attribute was removed), causing `verify_password` to silently fail. The `bcrypt` library is used directly to avoid this dependency on `passlib`'s version-detection logic.

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
| **Auth** | None |
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

### 4.3 Create User

| Property | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/users/` |
| **Auth** | None |
| **Rate Limit** | None |

**Headers**:

| Header | Required | Description |
|---|---|---|
| `Idempotency-Key` | No | If provided, the response is cached for 24 hours. A repeated request with the same key returns the cached response. |

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "role": "CUSTOMER"
}
```

**Response** (`201 Created`):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "CUSTOMER"
}
```

The `password_hash` is never included in any response. The password is hashed with bcrypt before storage.

**Error Responses**:

| Status | Condition |
|---|---|
| `409` | Email already registered |
| `422` | Missing or invalid fields |

### 4.4 Get User

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/{user_id}` |
| **Auth** | None |
| **Rate Limit** | None |

**Response** (`200 OK`):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "CUSTOMER"
}
```

**Error Responses**:

| Status | Condition |
|---|---|
| `404` | User not found |

### 4.5 Sign In

| Property | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/sign-in` |
| **Auth** | None |
| **Rate Limit** | None |

**Request**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response** (`200 OK`):
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Use the returned token in subsequent requests as `Authorization: Bearer <token>`.

**Error Responses**:

| Status | Condition |
|---|---|
| `401` | Invalid email or password |
| `422` | Missing or invalid fields |

Both "email not found" and "wrong password" return `401` with the same generic message to prevent user enumeration.

### 4.6 Create Order

| Property | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/orders/` |
| **Auth** | None (defaults to `CUSTOMER` role) |
| **Rate Limit** | 10 requests/minute per IP |

**Headers**:

| Header | Required | Description |
|---|---|---|
| `Idempotency-Key` | No | If provided, the response is cached for 24 hours. A repeated request with the same key returns the cached response without re-charging payment. |

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

**Flow**: Check idempotency cache (return cached response if hit) → validate products exist → calculate total → process payment (3 retries) → persist order atomically → save to idempotency cache → return response. Only successful (2xx) responses are cached; errors are never stored, allowing the client to retry a failed request with the same key.

### 4.7 Get Order Detail

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/orders/{order_id}` |
| **Auth** | None |
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

### 4.8 Update Order Status

| Property | Value |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/orders/{order_id}/status` |
| **Auth** | `MANAGER` JWT required |
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
| `401` | No token or invalid/expired token |
| `403` | Token is valid but role is not `MANAGER` |
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
- **User**: `id`, `email`, `role`, `password_hash`

`password_hash` is part of the `User` entity because it is core domain data. It is never serialized in any API response — the `UserResponse` Pydantic schema selects only `id`, `email`, and `role`.

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

Roles are stored in the `users` table and embedded in JWT claims at sign-in time. The middleware reads the role from the token — not from a request header — so a client cannot forge their role.

---

## 6. Key Design Patterns

### 6.1 Repository Pattern

Abstract interfaces are defined in `src/core/repositories/` using Python ABCs. Concrete implementations live in `src/infrastructure/database/repositories/`. This decouples the domain logic from the database:

- `AbstractProductRepository` defines `list_all()` and `get_by_ids()`
- `AbstractOrderRepository` defines `create()`, `get_by_id()`, `get_detail_by_id()`, and `update_status()`
- `AbstractUserRepository` defines `create()`, `get_by_id()`, `get_by_email()`, and `list_all()`
- `AbstractIdempotencyRepository` defines `get(key)` and `save(key, status_code, body)` — used exclusively at the API layer, not inside use cases

The same approach applies to external services (`AbstractPaymentService`, `AbstractNotificationService`). This enables straightforward testing — tests inject mocks or stubs without touching the database or external APIs.

### 6.2 Use Case Pattern

Each use case is a single-responsibility class with an `execute()` method:

- `CreateOrder.execute(product_ids)` — validates, calculates, pays, persists
- `GetOrderDetail.execute(order_id)` — retrieves full order with item details
- `UpdateOrderStatus.execute(order_id, new_status)` — validates transition, updates, notifies
- `GetMenu.execute()` — fetches and groups products into menu items
- `CreateUser.execute(email, role, password)` — hashes password, creates user with a new UUID
- `GetUser.execute(user_id)` — retrieves a user by ID or returns `None`
- `SignIn.execute(email, password)` — verifies credentials, returns a signed JWT

### 6.3 Dependency Injection

All wiring happens in `src/infrastructure/api/dependencies.py`. FastAPI's `Depends()` system provides:

- **Repositories**: `get_product_repository()`, `get_order_repository()`, `get_user_repository()`, `get_idempotency_repository()` — instantiated with the database connection
- **Services**: `get_payment_service()`, `get_notification_service()` — instantiated per request
- **Authorization**: `require_roles(*allowed_roles)` — returns a dependency that checks `request.state.role` (set by `RoleMiddleware` from the JWT) and raises `403` if unauthorized

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
- **Allowed Headers**: `X-Role`, `Content-Type`, `Idempotency-Key`, `Authorization`

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
- `order_id` and `user_id` path parameters must be valid UUIDs
- `email` fields are validated as proper email addresses via `EmailStr`

Invalid payloads are automatically rejected with `422 Unprocessable Entity` before reaching route handler logic.

### 8.4 Error Sanitization

Internal error details are never exposed to clients:

- Payment failures return a generic `"Payment could not be processed"` message (502). The actual error reason is logged server-side.
- Authentication failures return the same `"Invalid email or password"` message for both unknown email and wrong password, preventing user enumeration.
- Notification failures are entirely invisible to clients.
- Database errors result in generic 500 responses, not stack traces.

This prevents information leakage that could help an attacker understand the system's internals.

### 8.5 HTTP Timeouts

All outbound HTTP calls (payment, notification) use a 10-second timeout. This prevents the application from hanging indefinitely if an external service becomes unresponsive.

### 8.6 JWT Authentication and Role Extraction

`RoleMiddleware` (`src/infrastructure/api/middleware/role_middleware.py`) runs on every request and follows this logic:

1. If no `Authorization` header is present: set `request.state.role = Role.CUSTOMER` and proceed.
2. If the header is present but does not start with `Bearer `: return `401`.
3. Decode the token using the configured secret key and algorithm.
4. Extract the `role` claim and set `request.state.role`.
5. If decoding fails (expired, tampered, wrong key, missing claim): return `401`.

This design means:
- Public endpoints (menu, order creation, user registration, sign-in) work without any token.
- Role-protected endpoints use `require_roles()` which checks `request.state.role`.
- The role cannot be forged by a client because it is extracted from the cryptographically signed token, not from a plain request header.

### 8.7 Password Security

Passwords are handled as follows:

- `hash_password(plain)` — calls `bcrypt.hashpw` with a freshly generated salt. The cost factor is bcrypt's default (12 rounds), making brute-force attacks expensive.
- `verify_password(plain, hashed)` — calls `bcrypt.checkpw` in constant time to prevent timing attacks.
- The `password_hash` field is part of the `User` entity but is never included in any Pydantic response schema (`UserResponse` only exposes `id`, `email`, `role`).

---

## 9. Database Design

### 9.1 Schema

Five tables:

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

**`users`**

| Column | Type | Constraints |
|---|---|---|
| `id` | String (UUID) | Primary Key |
| `email` | String | NOT NULL, UNIQUE |
| `role` | String | NOT NULL |
| `password_hash` | String | NOT NULL |

**`idempotency_keys`**

| Column | Type | Constraints |
|---|---|---|
| `key` | String | Primary Key |
| `status_code` | Integer | NOT NULL |
| `response_body` | Text (JSON) | NOT NULL |
| `created_at` | DateTime | NOT NULL, server default: now() |

Idempotency entries older than 24 hours are treated as expired and ignored on lookup (no background purge — expired rows are simply skipped by the TTL check in `IdempotencyRepository.get()`).

UUIDs are stored as strings because SQLite has no native UUID type. The repository layer handles conversion between `str` and `uuid.UUID`.

### 9.2 Migrations

Managed by Alembic. Migration history:

1. **Initial schema** — creates products, orders, and order_products tables
2. **Remove users table** — drops an earlier user-related table that was superseded by header-based role checks
3. **Add created_at** — adds the `created_at` timestamp column to orders
4. **Add users table** — creates the users table with `id`, `email` (unique), and `role`
5. **Add idempotency_keys table** — creates the idempotency_keys table
6. **Add password_hash to users** — adds the `password_hash` NOT NULL column to the users table

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

### 10.1 User Registration and Sign-In

```
── Registration ──────────────────────────────────────────────────
Client
  │
  ▼
POST /users/ { email, password, role }  [Idempotency-Key: <key>]
  │
  ├─ RoleMiddleware: no token → role = CUSTOMER
  ├─ 0. IdempotencyRepository.get(key) ──► Cache hit → return cached 201
  │
  ▼
CreateUser.execute(email, role, password)
  │
  ├─ 1. hash_password(password) ──► bcrypt hash
  ├─ 2. UserRepository.create(user) ──► INSERT into users
  │     └─ Unique constraint violation → 409 Conflict
  │
  ├─ 3. IdempotencyRepository.save(key, 201, body) ──► Cache response
  │
  ▼
201 Created { id, email, role }

── Sign-In ────────────────────────────────────────────────────────
Client
  │
  ▼
POST /auth/sign-in { email, password }
  │
  ▼
SignIn.execute(email, password)
  │
  ├─ 1. UserRepository.get_by_email(email) ──► Fetch user
  │     └─ Not found → InvalidCredentialsError → 401
  │
  ├─ 2. verify_password(password, user.password_hash) ──► bcrypt.checkpw
  │     └─ Mismatch → InvalidCredentialsError → 401
  │
  ├─ 3. create_access_token(user.id, user.role) ──► JWT signed with HS256
  │
  ▼
200 OK { access_token: "<jwt>", token_type: "bearer" }
```

### 10.2 Order Creation

```
Client
  │
  ▼
POST /orders/ { product_ids: [...] }  [Idempotency-Key: <key>]
  │
  ├─ RoleMiddleware: decode JWT (or default CUSTOMER)
  ├─ Rate Limiter: check 10/min per IP
  │
  ├─ 0. IdempotencyRepository.get(key) ──► Check cache (if key present)
  │     └─ Cache hit → return cached 201 response immediately
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
  ├─ 5. IdempotencyRepository.save(key, 201, body) ──► Cache response
  │
  ▼
201 Created { id, status: "WAITING", total_price, product_ids }
```

### 10.3 Status Update

```
Client (MANAGER)
  │
  ▼
PATCH /orders/{id}/status { status: "PREPARATION" }
  Authorization: Bearer <manager-jwt>
  │
  ├─ RoleMiddleware: decode JWT → role = MANAGER
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

**No user identity on orders**: Orders are not associated with any user ID. Anyone who knows an order's UUID can view or update it. In production, orders must be tied to authenticated users, and access must be scoped — customers should only see their own orders.

**Role baked into JWT at sign-in**: If a user's role changes in the database, their existing token retains the old role until expiry. For a short-lived demo this is acceptable, but production would need a token revocation mechanism or very short token lifetimes.

### 11.2 Known Limitations

**Payment retry without backoff**: The payment service retries immediately 3 times with no delay between attempts. Under sustained payment service degradation, this amplifies load on the failing service. Production should use exponential backoff with jitter and consider a circuit breaker pattern.

**Notification delivery is not guaranteed**: Notifications are fire-and-forget via `asyncio.create_task()`. If the notification service is down or the application process crashes after updating the status but before the notification task completes, the notification is lost. Production should use a message queue or transactional outbox pattern.

**Float arithmetic for prices**: Prices are stored and calculated as Python floats, which can introduce floating-point precision errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). The use of `round(..., 2)` mitigates this in most cases, but production financial calculations should use `Decimal` types throughout.

**No pagination on menu or order list**: The menu endpoint returns all products in a single response. This is fine for a small catalog (13 items), but would not scale to hundreds or thousands of products. There is no order listing endpoint at all.

**Rate limiting by IP only**: Behind a reverse proxy or NAT, many clients may share the same IP address, causing legitimate users to be rate-limited. In production, rate limiting should be tied to authenticated user identity or API keys.

**Single CORS origin**: Only `http://localhost:3000` is allowed. This must be configurable for real deployments.

**No request logging or tracing**: While the payment and notification services log their operations, there is no structured request logging, correlation IDs, or distributed tracing. Production APIs need observability through request logs, metrics, and traces.

**Expired idempotency keys are never purged**: Rows older than 24 hours are ignored at read time but remain in the database indefinitely. A background job or scheduled SQL DELETE would be needed to reclaim storage.

### 11.3 Production Readiness Checklist

If this project were to go live, the following changes would need to be implemented:

| Area | Current State | Required Change |
|---|---|---|
| **Database** | SQLite (file-based) | PostgreSQL with connection pooling |
| **JWT secret** | Default `change-me-in-production` | Strong random secret via secrets manager |
| **Token revocation** | None | Token denylist (Redis) or short-lived tokens with refresh |
| **Authorization scope** | Role only; no ownership checks | Associate orders with user IDs; scope access by owner |
| **Payment retries** | Immediate, 3 attempts | Exponential backoff with jitter; circuit breaker |
| **Notifications** | Fire-and-forget | Message queue (RabbitMQ/SQS) or outbox pattern |
| **Idempotency** | `POST /orders/` and `POST /users/`; no key purge | Add periodic cleanup of expired keys |
| **Price precision** | Python `float` | `Decimal` types end-to-end |
| **CORS** | Hardcoded localhost | Configurable via environment variables |
| **Rate limiting** | Per-IP only | Per-user or per-API-key |
| **Observability** | Basic logging | Structured logs, metrics, distributed tracing |
| **Secrets management** | Environment variables | Vault or cloud secrets manager |
| **Deployment** | Local dev server | Containerized (Docker), orchestrated (K8s), with health checks and graceful shutdown |
| **API versioning** | None | URL prefix (`/v1/`) or header-based versioning |
| **Testing** | Unit + integration | Add load testing, contract testing, and end-to-end tests |
