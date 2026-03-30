import databases
import sqlalchemy

from src.infrastructure.settings import settings

database = databases.Database(settings.database_url)
metadata = sqlalchemy.MetaData()
