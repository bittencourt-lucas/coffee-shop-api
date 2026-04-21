import sqlalchemy

from src.infrastructure.database.connection import metadata

revoked_tokens_table = sqlalchemy.Table(
    "revoked_tokens",
    metadata,
    sqlalchemy.Column("jti", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("expires_at", sqlalchemy.DateTime, nullable=False),
)
