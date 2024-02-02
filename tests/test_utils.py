from .. import utils
from datetime import datetime
from ..db.db_tables import Listing, Message
import json
import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def filter_comp_vals():
    return {"var": 1, "val": 2}


@pytest.fixture(scope="module")
def push_to_db_configs():
    parent_dir_path = str(Path(os.getcwd()).parent.absolute())
    db_url = "sqlite:///%s/db/listings.db" % parent_dir_path
    engine = create_engine(db_url)
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    yield {"db_url": db_url, "pass_session": session}
    session.rollback()
    session.close()


@pytest.fixture()
def push_to_db_listing_configs(push_to_db_configs):
    listing_specific_configs = {
        "push_data_pk": "url_append",
        "table": Listing,
        "table_pk": Listing.url_append,
    }

    return push_to_db_configs | listing_specific_configs


@pytest.fixture()
def push_to_db_message_configs(push_to_db_configs):
    message_specific_configs = {
        "push_data_pk": "sent_url_append",
        "table": Message,
        "table_pk": Message.sent_url_append,
    }

    return push_to_db_configs | message_specific_configs


@pytest.fixture()
def push_to_db_listing_success_configs(push_to_db_listing_configs):
    data = {
        "url_append": "path/to/listing",
        "upload_date": datetime.now(),
        "domain": "mysite.nl",
        "domain_id": "h4sh_v4lu3",
        "postal_code": "TEST_PS_CODE_TEST",
        "street": "Streetie",
        "house_number": 1,
        "house_addition": "A",
        "locale": "Streetsburg",
        "rent_buy": "rent",
        "available_date": datetime.now(),
        "rent_total": 999.99,
        "area_dwelling": 50.0,
        "district": "Zuid-Streetsville",
        "room_count": 4,
        "floor": 1.0,
    }

    push_to_db_listing_configs.update({"data": [data]})

    return push_to_db_listing_configs


@pytest.fixture()
def push_to_db_listing_failure_configs(push_to_db_listing_configs):
    data = {
        "rent_total": 999.99,
    }

    push_to_db_listing_configs.update({"data": [data]})

    return push_to_db_listing_configs


@pytest.fixture()
def push_to_db_message_success_configs(push_to_db_message_configs):
    data = {
        "sent_url_append": "path/to/listing",
        "sender": "TEST_me@gmail.com_TEST",
        "recipient": "you@yahoo.com",
        "send_date": datetime.now(),
        "sent_data_upload_date": datetime.now(),
    }

    push_to_db_message_configs.update({"data": [data]})

    return push_to_db_message_configs


@pytest.fixture()
def push_to_db_message_failure_configs(push_to_db_message_configs):
    data = {
        "sender": "TEST_me@gmail.com_TEST",
        "recipient": "you@yahoo.com",
        "send_date": datetime.now(),
        "sent_data_upload_date": datetime.now(),
    }

    push_to_db_message_configs.update({"data": [data]})

    return push_to_db_message_configs


@pytest.fixture()
def generic_get_request_configs():
    def get_handler_func(return_dict_raw):
        return_dict = json.loads(return_dict_raw)
        return return_dict["url"]

    url = "https://httpbin.org/get"
    handler_func = get_handler_func

    return {"url": url, "handler_func": handler_func}


def test_filter_comp_eq(filter_comp_vals):
    assert_neq = utils.filter_comp(**filter_comp_vals, comp="eq")

    assert_eq = utils.filter_comp(
        filter_comp_vals["var"], filter_comp_vals["var"], comp="eq"
    )

    assert (assert_eq, assert_neq) == (True, False)


def test_filter_comp_lte(filter_comp_vals):
    assert_lt = utils.filter_comp(**filter_comp_vals, comp="lte")

    assert_eq = utils.filter_comp(
        filter_comp_vals["var"], filter_comp_vals["var"], comp="lte"
    )

    assert (assert_lt, assert_eq) == (True, True)


def test_filter_comp_lt(filter_comp_vals):
    assert_lt = utils.filter_comp(**filter_comp_vals, comp="lt")

    assert (assert_lt) == (True)


def test_filter_comp_gte(filter_comp_vals):
    assert_gt = utils.filter_comp(**filter_comp_vals, comp="gte")

    assert_eq = utils.filter_comp(
        filter_comp_vals["var"], filter_comp_vals["var"], comp="gte"
    )

    assert (assert_gt, assert_eq) == (False, True)


def test_filter_comp_gt(filter_comp_vals):
    assert_gt = utils.filter_comp(**filter_comp_vals, comp="gte")
    assert (assert_gt) == (False)


def test_push_listings_success(push_to_db_listing_success_configs):
    utils.push_to_db(**push_to_db_listing_success_configs)
    session = push_to_db_listing_success_configs["pass_session"]
    pushed_row = (
        session.query(Listing).filter_by(postal_code="TEST_PS_CODE_TEST").first()
    )

    assert pushed_row.url_append == "path/to/listing"
    assert pushed_row.domain == "mysite.nl"
    assert pushed_row.street == "Streetie"
    assert pushed_row.rent_total == 999.99


def test_push_listings_failure(push_to_db_listing_failure_configs):
    with pytest.raises(KeyError):
        utils.push_to_db(**push_to_db_listing_failure_configs)

    assert True


def test_push_message_success(push_to_db_message_success_configs):
    utils.push_to_db(**push_to_db_message_success_configs)
    session = push_to_db_message_success_configs["pass_session"]
    pushed_row = (
        session.query(Message).filter_by(sender="TEST_me@gmail.com_TEST").first()
    )

    assert pushed_row.sent_url_append == "path/to/listing"
    assert pushed_row.sender == "TEST_me@gmail.com_TEST"
    assert pushed_row.recipient == "you@yahoo.com"


def test_push_message_failure(push_to_db_message_failure_configs):
    with pytest.raises(KeyError):
        utils.push_to_db(**push_to_db_message_failure_configs)

    assert True


def test_generic_get_request(generic_get_request_configs):
    get_response = utils.generic_get_request_wrap(**generic_get_request_configs)

    assert get_response == "https://httpbin.org/get"
