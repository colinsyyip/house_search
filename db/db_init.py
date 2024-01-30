from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from .db_tables import Listing, Message


def validate_database(db_file_path: str = "sqlite:///db/listings.db"):
    engine = create_engine(db_file_path)
    if not database_exists(engine.url):
        create_database(engine.url)
        Listing.metadata.create_all(engine)
        Message.metadata.create_all(engine)
        print("Created new database: %s" % db_file_path)
    else:
        print("Database %s already exists" % db_file_path)


if __name__ == "__main__":
    validate_database()