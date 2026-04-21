# Coffee Shop API

A RESTful API for a coffee shop built with **FastAPI** and **Clean Architecture**. Handles the menu, order creation, order tracking, and status management with role-based access control and payment/notification integrations.

## Architecture

The project follows Clean Architecture with a Repository Pattern, organized into three layers:

- **`core/`** — Pure Python: entities, enums, abstract repository interfaces, abstract service interfaces, and exceptions. No framework dependencies.
- **`use_cases/`** — Application logic. Depends only on `core/`. Each use case is a single class with an `execute` method.
- **`infrastructure/`** — Everything framework-specific: SQLAlchemy table models, concrete repository implementations, FastAPI routes, Pydantic schemas, and external service clients.

## Endpoints

All requests require an `X-Role` header. Valid values: `CUSTOMER`, `MANAGER`. Defaults to `CUSTOMER` if omitted.

| Method  | Path                      | Role     | Rate Limit | Description                                      |
|---------|---------------------------|----------|------------|--------------------------------------------------|
| `GET`   | `/menu`                   | Any      | —          | List all products grouped by name with variations |
| `POST`  | `/orders/`                | Any      | 10/min     | Create an order and process payment              |
| `GET`   | `/orders/{id}`            | Any      | —          | Get full order details                           |
| `PATCH` | `/orders/{id}/status`     | MANAGER  | —          | Advance order status                             |
| `POST`  | `/users/`                 | Any      | —          | Create a user                                    |
| `GET`   | `/users/{id}`             | Any      | —          | Get a user by ID                                 |

### Idempotency

`POST /orders/` supports the `Idempotency-Key` request header. Sending the same key on a repeated request returns the original cached response without re-charging payment or creating a duplicate order. Keys expire after 24 hours. Requests without the header are processed normally.

### Order Status Flow

Status transitions are strictly enforced in sequence:

```
WAITING → PREPARATION → READY → DELIVERED
```

Any out-of-sequence update returns `422`.

### External Integrations

- **Payment** (`POST /api/v1/payment`) — called on order creation. Retries up to 3 times; returns `502` if all attempts fail. External service errors are not exposed to clients.
- **Notification** (`POST /api/v1/notification`) — called after every status update. Runs as a fire-and-forget background task; failures are logged and never affect the response.

### Security

- **CORS** — Restricted to explicit allowed origins, methods, and headers via `CORSMiddleware`.
- **Rate limiting** — `POST /orders/` is limited to 10 requests/minute per IP using `slowapi`. Exceeding the limit returns `429 Too Many Requests`.
- **Input validation** — `product_ids` is capped at 50 items per order to prevent abuse.
- **Error sanitization** — External service errors are logged server-side only; clients receive generic error messages.
- **Structured logging** — Payment and notification services use Python `logging` instead of `print`.
- **Configurable secrets** — All external URLs and the database connection string are loaded from environment variables via `pydantic-settings`, not hardcoded.
- **Explicit timeouts** — All outbound HTTP calls use a 10-second timeout.

---

## Running Locally

### Prerequisites

- Python 3.12+
- A virtual environment with dependencies installed

### Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install fastapi[standard] databases[aiosqlite] alembic httpx pydantic-settings slowapi

# (Optional) Copy and edit the environment file
cp .env.example .env
```

### Configuration

All settings can be overridden via environment variables (prefixed with `COFFEE_SHOP_`):

| Variable                       | Default                                          | Description            |
|--------------------------------|--------------------------------------------------|------------------------|
| `COFFEE_SHOP_DATABASE_URL`     | `sqlite+aiosqlite:///./coffee_shop.db`           | Database connection    |
| `COFFEE_SHOP_PAYMENT_URL`      | `https://challenge.trio.dev/api/v1/payment`      | Payment service URL    |
| `COFFEE_SHOP_NOTIFICATION_URL` | `https://challenge.trio.dev/api/v1/notification`  | Notification service URL |

### Database

```bash
# Apply all migrations (creates the SQLite database)
alembic upgrade head
```

The database file `coffee_shop.db` will be created in the project root. The product catalog is seeded automatically on startup.

### Start the server

```bash
fastapi dev src/main.py
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`.

---

## Running the Tests

### Install test dependencies

```bash
pip install pytest pytest-asyncio
```

### Run all tests

```bash
pytest tests/
```

### Run with coverage

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Test Coverage

93 tests across unit and integration suites.

```
Name                                                             Stmts   Miss  Cover
------------------------------------------------------------------------------------
src\core\entities\*                                                 43      0   100%
src\core\enums\*                                                    13      0   100%
src\core\exceptions.py                                               7      0   100%
src\core\services\*                                                  7      0   100%
src\infrastructure\api\routes\order_routes.py                       32      0   100%
src\infrastructure\api\routes\product_routes.py                     11      0   100%
src\infrastructure\api\schemas\*                                    36      0   100%
src\infrastructure\database\models\*                                10      0   100%
src\infrastructure\database\repositories\order_repository.py        41      0   100%
src\infrastructure\database\seed.py                                 11      0   100%
src\infrastructure\services\payment_service.py                      21      0   100%
src\use_cases\*                                                     68      0   100%
------------------------------------------------------------------------------------
TOTAL                                                              450     38    92%
```

Overall coverage: **92%**. Uncovered lines are limited to abstract method stubs, the app lifespan startup/shutdown hooks, and the notification service's live HTTP path (intentionally not exercised in tests, as the service is mocked via dependency injection).
