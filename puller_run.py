from datetime import datetime
from db import db_init
from itertools import chain
import logging
from logging import StreamHandler
from pullers import Funda, Kamernet, Pararius, Room
import sys
import warnings
from utils import push_to_db
from mail_generate import MailGenerator


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s|%(funcName)s:%(lineno)d: %(message)s",
)
logging.getLogger(__name__).setLevel(logging.INFO)
logging.getLogger(__name__).addHandler(StreamHandler())


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

    db_init.validate_database()
    results = execute_pullers(run_headless=is_headless)
    curr_datetime = datetime.now()
    truncated_datetime = curr_datetime.replace(second=0, microsecond=0)
    [x.update({"upload_date": truncated_datetime}) for x in results]
    push_to_db(results)

    mail_gen = MailGenerator()
    if mail_gen.new_listings is not None:
        mail_gen.execute_mail()
