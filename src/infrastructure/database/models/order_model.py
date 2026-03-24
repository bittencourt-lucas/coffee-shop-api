import sqlalchemy

from src.infrastructure.database.connection import metadata

orders_table = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("status", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("total_price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("users.id"),
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
