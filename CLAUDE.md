# CLAUDE.md

## Project Overview

Coffee Shop REST API built with **FastAPI** and **Clean Architecture**. Handles menu browsing, order creation with external payment processing, order tracking, and status management with role-based access control.

- **Python 3.12+**, **SQLite** (async via `databases` + `aiosqlite`), **Alembic** for migrations
- Entry point: `src/main.py`

## Commands

**Always activate the virtual environment before running any command:**

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

```bash
# Run the dev server
fastapi dev src/main.py

# Run all tests
./venv/Scripts/python -m pytest tests/

# Run linter
./venv/Scripts/python -m flake8 src/ tests/

# Run migrations
alembic upgrade head
```

**A task is NOT complete until both `pytest` and `flake8` pass cleanly.** Always run both before considering any work done.

## Architecture

Clean Architecture with three layers. Dependencies flow inward only: `infrastructure -> use_cases -> core`.

```
src/
├── core/                    # Pure Python — NO framework dependencies
│   ├── entities/            # Dataclasses: Product, Order, OrderDetail, OrderItem, MenuItem, MenuVariation
│   ├── enums/               # OrderStatus (WAITING, PREPARATION, READY, DELIVERED), Role (CUSTOMER, MANAGER)
│   ├── repositories/        # Abstract repository interfaces (ABC)
│   ├── services/            # Abstract service interfaces (ABC): AbstractPaymentService, AbstractNotificationService
│   └── exceptions.py        # InvalidProductError, InvalidStatusTransitionError, PaymentFailedError
│
├── use_cases/               # Application logic — depends only on core
│   ├── order/               # CreateOrder, GetOrderDetail, UpdateOrderStatus
│   └── product/             # GetMenu
│
├── infrastructure/          # Framework-specific implementations
│   ├── api/
│   │   ├── routes/          # FastAPI routers: healthcheck, product (menu), order
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── middleware/      # RoleMiddleware (X-Role header), rate_limit (slowapi)
│   │   └── dependencies.py  # DI wiring: repositories, services, role validation
│   ├── database/
│   │   ├── models/          # SQLAlchemy table definitions (products, orders, order_products)
│   │   ├── repositories/    # Concrete repository implementations
│   │   ├── connection.py    # Database instance + metadata
│   │   └── seed.py          # Product catalog seeding (runs on startup if empty)
│   ├── services/            # PaymentService (with retries), NotificationService (fire-and-forget)
│   └── settings.py          # pydantic-settings: env vars with COFFEE_SHOP_ prefix
│
└── main.py                  # FastAPI app, lifespan, middleware registration
```

## Key Patterns

- **Repository Pattern**: Abstract interfaces in `core/repositories/`, concrete implementations in `infrastructure/database/repositories/`. Always code against the abstract interface.
- **Use Cases**: Each is a single class with an `execute()` method. Instantiated with its dependencies (repositories, services) in the route handler via FastAPI `Depends()`.
- **Dependency Injection**: Wired in `infrastructure/api/dependencies.py`. FastAPI's `Depends()` provides repositories and services to route handlers. Tests override these via `app.dependency_overrides`.
- **Configuration**: All external URLs and the database connection string come from `infrastructure/settings.py` (pydantic-settings). Override via `COFFEE_SHOP_*` environment variables.
- **Middleware execution order**: CORS -> RoleMiddleware -> route handler. Rate limiting is applied per-route via `@limiter.limit()` decorator.

## Testing

- **Unit tests** (`tests/unit/`): Test use cases and services in isolation using `AsyncMock`. No database or HTTP calls.
- **Integration tests** (`tests/integration/`): Test full request/response cycle via `httpx.AsyncClient` with ASGI transport. Use a file-based test SQLite DB, cleaned up after each test.
- **Test fixtures** are in `tests/integration/conftest.py`. Key fixtures: `test_db`, `client` (empty DB), `seeded_client` (pre-populated catalog).
- **External services** (payment, notification) are mocked via dependency overrides in integration tests.
- **Rate limiter** is disabled during tests (`limiter.enabled = False` in conftest).
- `asyncio_mode = "auto"` is set in `pyproject.toml` — no need for `@pytest.mark.asyncio`.

## Style and Conventions

- **Logging**: Use Python `logging` module, never `print()`. Each module gets its own logger: `logger = logging.getLogger(__name__)`.
- **Imports**: Absolute imports from `src.*`. Group: stdlib, third-party, local.
- **Linting**: `flake8` with default settings. Keep lines under the limit, no unused imports/variables.
- **Error handling in routes**: Catch domain exceptions and raise `HTTPException`. Never expose internal/external service error details to clients — return generic messages and log details server-side.
- **Enums**: Use Python `enum.Enum` for fixed sets (roles, statuses). Pydantic validates enum values automatically.
- **UUIDs**: Used for all entity IDs. Stored as strings in SQLite, converted to/from `uuid.UUID` in repository layer.
