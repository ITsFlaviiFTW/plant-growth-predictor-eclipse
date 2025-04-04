# databaseInit.py
from database.database import engine
from database.models import Base

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
