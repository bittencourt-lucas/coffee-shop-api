# Coffee Shop API

A RESTful API for a coffee shop built with **FastAPI** and **Clean Architecture**. Handles the menu, order creation, order tracking, and status management with JWT-based authentication and role-based access control.

## Architecture

The project follows Clean Architecture with a Repository Pattern, organized into three layers:

- **`core/`** — Pure Python: entities, enums, abstract repository interfaces, abstract service interfaces, and exceptions. No framework dependencies.
- **`use_cases/`** — Application logic. Depends only on `core/`. Each use case is a single class with an `execute` method.
- **`infrastructure/`** — Everything framework-specific: SQLAlchemy table models, concrete repository implementations, FastAPI routes, Pydantic schemas, external service clients, and auth utilities.

## Authentication

Protected endpoints require a valid JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Obtain a token by signing in via `POST /auth/sign-in`. The token encodes the user's ID and role — no database lookup is needed per request. A missing, invalid, or expired token returns `401`. A valid token with an insufficient role returns `403`.

Sign out via `POST /auth/sign-out` to invalidate the token immediately. Revoked tokens are stored in a denylist keyed by `jti` claim and rejected on all subsequent requests, even if not yet expired.

## Endpoints

| Method  | Path                      | Auth Required  | Rate Limit | Description                                       |
|---------|---------------------------|----------------|------------|---------------------------------------------------|
| `GET`   | `/healthcheck`            | No             | —          | Liveness probe                                    |
| `GET`   | `/menu`                   | No             | —          | List all products grouped by name with variations |
| `POST`  | `/users/`                 | No             | —          | Register a new user (role always `CUSTOMER`)      |
| `GET`   | `/users/{id}`             | Any valid JWT  | —          | Get a user by ID                                  |
| `POST`  | `/auth/sign-in`           | No             | —          | Authenticate and receive a JWT                    |
| `POST`  | `/auth/sign-out`          | Any valid JWT  | —          | Revoke the current JWT immediately                |
| `POST`  | `/orders/`                | Any valid JWT  | 10/min     | Create an order and process payment               |
| `GET`   | `/orders/{id}`            | Any valid JWT  | —          | Get full order details (customers: own orders only) |
| `PATCH` | `/orders/{id}/status`     | MANAGER token  | —          | Advance order status                              |

### Idempotency

`POST /orders/` and `POST /users/` support the `Idempotency-Key` request header. Sending the same key on a repeated request returns the original cached response without re-processing. Keys must be 128 characters or fewer and expire after 24 hours.

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

- **JWT authentication** — Roles are derived from signed HS256 tokens. The secret key and expiration are configurable via environment variables. If the default secret is used at startup, a `CRITICAL` log warning is emitted.
- **Token revocation** — `POST /auth/sign-out` inserts the token's `jti` claim into a `revoked_tokens` denylist. All subsequent requests with that token return `401`, even if the token has not expired yet. Expired entries are purged automatically every 60 minutes.
- **Role lockdown** — Registration via `POST /users/` always creates a `CUSTOMER`. There is no self-service path to the `MANAGER` role.
- **Timing-safe sign-in** — The sign-in path always runs a bcrypt verification, even when the email is not found, to prevent response-time attacks that distinguish existing from non-existing accounts.
- **Password hashing** — Passwords are hashed with bcrypt before storage. A minimum length of 8 characters is enforced at the API layer. Plaintext passwords are never persisted.
- **CORS** — Restricted to explicit allowed origins, methods, and headers via `CORSMiddleware`.
- **Rate limiting** — `POST /orders/` is limited to 10 requests/minute per IP using `slowapi`. Exceeding the limit returns `429 Too Many Requests`.
- **Input validation** — `product_ids` is capped at 50 items per order; `Idempotency-Key` headers are capped at 128 characters.
- **Error sanitization** — External service errors are logged server-side only; clients receive generic error messages.
- **Structured logging** — Services use Python `logging` instead of `print`.
- **Configurable secrets** — All external URLs, the database connection string, and the JWT secret key are loaded from environment variables via `pydantic-settings`.
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
pip install fastapi[standard] databases[aiosqlite] alembic httpx pydantic-settings slowapi "python-jose[cryptography]" bcrypt

# (Optional) Copy and edit the environment file
cp .env.example .env
```

### Configuration

All settings can be overridden via environment variables (prefixed with `COFFEE_SHOP_`):

| Variable                              | Default                                          | Description              |
|---------------------------------------|--------------------------------------------------|--------------------------|
| `COFFEE_SHOP_DATABASE_URL`            | `sqlite+aiosqlite:///./coffee_shop.db`           | Database connection      |
| `COFFEE_SHOP_PAYMENT_URL`             | `https://challenge.trio.dev/api/v1/payment`      | Payment service URL      |
| `COFFEE_SHOP_NOTIFICATION_URL`        | `https://challenge.trio.dev/api/v1/notification` | Notification service URL |
| `COFFEE_SHOP_JWT_SECRET_KEY`          | `change-me-in-production`                        | JWT signing secret       |
| `COFFEE_SHOP_JWT_ALGORITHM`           | `HS256`                                          | JWT signing algorithm    |
| `COFFEE_SHOP_JWT_EXPIRATION_MINUTES`  | `60`                                             | Token lifetime (minutes) |

> **Important**: Always override `COFFEE_SHOP_JWT_SECRET_KEY` with a strong random value in any non-local environment.

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

137 tests across unit and integration suites.

```
Name                                                                   Stmts   Miss  Cover
-------------------------------------------------------------------------------------------
src\core\entities\*                                                       66      0   100%
src\core\enums\*                                                          13      0   100%
src\core\exceptions.py                                                    15      0   100%
src\core\services\*                                                        7      0   100%
src\infrastructure\api\routes\order_routes.py                             49      0   100%
src\infrastructure\api\routes\user_routes.py                              33      0   100%
src\infrastructure\api\routes\auth_routes.py                              18      0   100%
src\infrastructure\api\routes\product_routes.py                           10      0   100%
src\infrastructure\api\schemas\*                                          55      0   100%
src\infrastructure\auth\jwt.py                                            23      2    91%
src\infrastructure\auth\password.py                                        6      0   100%
src\infrastructure\database\models\*                                      19      0   100%
src\infrastructure\database\repositories\order_repository.py              47      1    98%
src\infrastructure\database\repositories\user_repository.py               29      2    93%
src\infrastructure\database\seed.py                                       11      0   100%
src\infrastructure\services\payment_service.py                            23      0   100%
src\use_cases\*                                                           91      0   100%
-------------------------------------------------------------------------------------------
TOTAL                                                                    852     65    92%
```

Overall coverage: **92%**. Uncovered lines are limited to abstract method stubs, the app lifespan startup/shutdown hooks, the background purge loop's sleep iteration, and the notification service's live HTTP path (intentionally not exercised in tests, as the service is mocked via dependency injection).
