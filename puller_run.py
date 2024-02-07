from datetime import datetime
from db import db_init
from itertools import chain
import logging
from pullers import Funda, Kamernet, Pararius, Room
import sys
import warnings
from utils import push_to_db
from mail_generate import MailGenerator


logging.basicConfig(
    filename="house_search_logs.txt",
    filemode="a",
    level=logging.INFO,
    format="[%(asctime)s] %(name)s|%(funcName)s:%(lineno)d: %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def execute_pullers(run_headless: bool = True):
    """
    Initialize and execute pullers to retrieve data
    """
    room_obj = Room()
    kamer_obj = Kamernet()
    pararius_obj = Pararius(headless=run_headless)
    funda_obj = Funda(headless=run_headless)

    obj_list = [room_obj, kamer_obj, pararius_obj, funda_obj]
    pulled_results = [x.parse_rentals() for x in obj_list]
    flattened_results = list(chain(*pulled_results))
    return flattened_results


if __name__ == "__main__":
    """
    Executes all pullers as well as push to DB. Can run headless with argument T or F.
    """
    if len(sys.argv) == 1:
        is_headless_str = "F"
    else:
        is_headless_str = sys.argv[1]

    if is_headless_str == "T":
        is_headless = True
    elif is_headless_str == "F":
        is_headless = False
    else:
        warnings.warn(
            "Unaccepted parameter for headless passed. Defaulting to non-headless."
        )
        is_headless = False

    logger.info("Starting DB validation.")

    db_init.validate_database()
    logger.info("Running pullers.")
    results = execute_pullers(run_headless=is_headless)
    curr_datetime = datetime.now()
    truncated_datetime = curr_datetime.replace(second=0, microsecond=0)
    [x.update({"upload_date": truncated_datetime}) for x in results]
    logger.info("Pushing results to db.")
    push_to_db(results)

    logger.info("Initializing MailGenerator")
    mail_gen = MailGenerator()
    if mail_gen.new_listings is not None:
        logger.info("Sending out mail using MailGenerator")
        mail_gen.execute_mail()
        logger.info("Emails sent out successfully.")
    else:
        logger.info("No new listings found.")
