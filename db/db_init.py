import logging
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from .db_tables import Listing, Message


logger = logging.getLogger(__name__)


def validate_database(db_file_path: str = "sqlite:///db/listings.db"):
    engine = create_engine(db_file_path)
    if not database_exists(engine.url):
        create_database(engine.url)
        Listing.metadata.create_all(engine)
        Message.metadata.create_all(engine)
        logger.info("Created new database: %s" % db_file_path)
    else:
        logger.info("Database %s already exists" % db_file_path)


if __name__ == "__main__":
    validate_database()
