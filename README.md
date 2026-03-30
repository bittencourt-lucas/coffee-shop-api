# Coffee Shop API

A RESTful API for a coffee shop built with **FastAPI** and **Clean Architecture**. Handles the menu, order creation, order tracking, and status management with role-based access control and payment/notification integrations.

## Architecture

The project follows Clean Architecture with a Repository Pattern, organized into three layers:

- **`core/`** — Pure Python: entities, enums, abstract repository interfaces, abstract service interfaces, and exceptions. No framework dependencies.
- **`use_cases/`** — Application logic. Depends only on `core/`. Each use case is a single class with an `execute` method.
- **`infrastructure/`** — Everything framework-specific: SQLAlchemy table models, concrete repository implementations, FastAPI routes, Pydantic schemas, and external service clients.

## Endpoints

All requests require an `X-Role` header. Valid values: `CUSTOMER`, `MANAGER`. Defaults to `CUSTOMER` if omitted.

| Method  | Path                      | Role     | Description                                      |
|---------|---------------------------|----------|--------------------------------------------------|
| `GET`   | `/menu`                   | Any      | List all products grouped by name with variations |
| `POST`  | `/orders/`                | Any      | Create an order and process payment              |
| `GET`   | `/orders/{id}`            | Any      | Get full order details                           |
| `PATCH` | `/orders/{id}/status`     | MANAGER  | Advance order status                             |

### Order Status Flow

Status transitions are strictly enforced in sequence:

```
WAITING → PREPARATION → READY → DELIVERED
```

Any out-of-sequence update returns `422`.

### External Integrations

- **Payment** (`POST /api/v1/payment`) — called on order creation. Retries up to 3 times; returns `502` if all attempts fail.
- **Notification** (`POST /api/v1/notification`) — called after every status update. Runs as a fire-and-forget background task; failures are logged to the terminal and never affect the response.

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
pip install fastapi[standard] databases[aiosqlite] alembic httpx
```

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

71 tests across unit and integration suites.

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
