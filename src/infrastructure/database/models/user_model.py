import sqlalchemy

from src.infrastructure.database.connection import metadata

users_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("role", sqlalchemy.String, nullable=False),
)
