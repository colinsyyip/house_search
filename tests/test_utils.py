from .. import utils
from datetime import datetime
from ..db.db_tables import Listing, Message
from ..__local_proxy_get import proxy_list_generate
import json
import os
from pathlib import Path
import pytest
from selenium.webdriver.common.by import By
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
def generic_get_request_success_configs():
    def get_handler_func(return_dict_raw):
        return_dict = json.loads(return_dict_raw)
        return return_dict["url"]

    url = "https://httpbin.org/get"
    handler_func = get_handler_func

    return {"url": url, "handler_func": handler_func}


@pytest.fixture()
def generic_get_request_failure_configs():
    def get_handler_func(return_dict_raw):
        return_dict = json.loads(return_dict_raw)
        return return_dict["url"]

    url = "https://httpbin.org/post"
    handler_func = get_handler_func

    return {"url": url, "handler_func": handler_func}


@pytest.fixture()
def generic_post_request_success_configs():
    def get_handler_func(return_dict_raw):
        return_dict = json.loads(return_dict_raw)
        return return_dict

    url = "https://httpbin.org/post"
    pl = {"foo": "bar"}
    handler_func = get_handler_func

    return {"url": url, "handler_func": handler_func, "pl": pl}


@pytest.fixture()
def generic_post_request_failure_configs():
    def get_handler_func(return_dict_raw):
        return_dict = json.loads(return_dict_raw)
        return return_dict

    url = "https://httpbin.org/get"
    pl = {"foo": "bar"}
    handler_func = get_handler_func

    return {"url": url, "handler_func": handler_func, "pl": pl}


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


def test_generic_get_request_success(generic_get_request_success_configs):
    get_response = utils.generic_get_request_wrap(**generic_get_request_success_configs)

    assert get_response == "https://httpbin.org/get"


def test_generic_get_request_failure(generic_get_request_failure_configs):
    with pytest.raises(ValueError) as exception_info:
        _ = utils.generic_get_request_wrap(**generic_get_request_failure_configs)

    assert type(exception_info.value) == ValueError


def test_generic_post_request_success(generic_post_request_success_configs):
    get_response = utils.generic_post_request_wrap(
        **generic_post_request_success_configs
    )
    get_response_data = get_response["json"]
    get_response_url = get_response["url"]

    assert get_response_data["foo"] == "bar"
    assert get_response_url == "https://httpbin.org/post"


def test_generic_post_request_failure(generic_post_request_failure_configs):
    with pytest.raises(ValueError) as exception_info:
        _ = utils.generic_post_request_wrap(**generic_post_request_failure_configs)

    assert type(exception_info.value) == ValueError


@pytest.fixture()
def driver_param_failure_params():
    return {
        "proxy_list": ["123.456.789:8080", "123.456.789:8081"],
        "proxy_list_path": "some/file/path.txt",
    }


@pytest.fixture()
def driver_param_no_proxy_init_params():
    return {"headless": True, "proxy_list": None, "proxy_list_path": None}


@pytest.fixture()
def selenium_soup_request_params():
    get_url = "https://httpbin.org/html"
    test_element_class = "//h1"
    by_method = By.XPATH

    return {
        "url": get_url,
        "test_element_class": test_element_class,
        "by_method": by_method,
    }


@pytest.fixture()
def proxy_list_file_generate():
    proxy_list_generate()


def test_driver_param_failure(driver_param_failure_params):
    with pytest.raises(ValueError) as exception_info:
        _ = utils.Driver(**driver_param_failure_params)

    excep_value = exception_info.value

    assert type(excep_value) == ValueError
    assert "Both proxy_list and proxy_list_path passed." in excep_value.args[0]


def test_driver_no_proxy_init(
    driver_param_no_proxy_init_params, selenium_soup_request_params
):
    driver = utils.Driver(**driver_param_no_proxy_init_params)
    soup = driver.selenium_soup_get(**selenium_soup_request_params)

    assert soup.h1.text == "Herman Melville - Moby-Dick"


def test_driver_proxy_list_init():
    # need to regen proxies
    pass


def test_driver_proxy_list_path_init():
    # need to regen proxies
    pass


def test_driver_proxy_try_limit_failure():
    pass


def test_driver_randomize_ua():
    pass


def test_driver_no_headless():
    pass


def test_driver_proxy_restart_on_timeout():
    pass
