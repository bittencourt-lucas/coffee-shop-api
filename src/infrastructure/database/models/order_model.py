import sqlalchemy

from src.infrastructure.database.connection import metadata

orders_table = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("total_price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        server_default=sqlalchemy.func.now(),
        nullable=False,
    ),
)

order_products_table = sqlalchemy.Table(
    "order_products",
    metadata,
    sqlalchemy.Column(
        "order_id",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("orders.id"),
        nullable=False,
    ),
    sqlalchemy.Column(
        "product_id",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("products.id"),
        nullable=False,
    ),
)
