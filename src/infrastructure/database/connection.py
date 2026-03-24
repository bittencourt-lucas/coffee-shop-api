import databases
import sqlalchemy

DATABASE_URL = "sqlite+aiosqlite:///./coffee_shop.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
