import sqlalchemy

from src.infrastructure.database.connection import metadata

idempotency_keys_table = sqlalchemy.Table(
    "idempotency_keys",
    metadata,
    sqlalchemy.Column("key", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("status_code", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("response_body", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        server_default=sqlalchemy.func.now(),
        nullable=False,
    ),
)
