from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from db_tables import Listing

def validate_database():
     engine = create_engine('sqlite:///listings.db')
     if not database_exists(engine.url): 
        create_database(engine.url)  
        Listing.metadata.create_all(engine)
     else:
         print("Database Already Exists")
    