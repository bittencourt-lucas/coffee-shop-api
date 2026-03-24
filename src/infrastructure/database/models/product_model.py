import sqlalchemy

from src.infrastructure.database.connection import metadata

products_table = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("base_price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("variation", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("price_change", sqlalchemy.Float, nullable=False),
)
