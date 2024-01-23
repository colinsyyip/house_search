from db.db_tables import Listing
import requests
from sqlalchemy import create_engine, insert, select, update


def filter_comp(var, val, comp):
    if comp == "eq":
        return var == val
    if comp == "lte":
        return var <= val
    if comp == "lt":
        return var < val
    if comp == "gte":
        return var >= val
    if comp == "gt":
        return var > val
    
    return False


def push_to_db(data, db_url = 'sqlite:///db/listings.db'):
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for data_dict in data:
            data_pk = data_dict['url_append']
            query_stmt = select(Listing).where(Listing.url_append == data_pk)
            query_result = conn.execute(query_stmt)
            is_exists = query_result.first()
            if not is_exists:
                insert_statement = insert(Listing)
                conn.execute(insert_statement, data_dict)
                conn.commit()
            else:
                update_statement = update(Listing).where(Listing.url_append == data_pk)
                conn.execute(update_statement, data_dict)
        conn.close()
    return None


def generic_get_request_wrap(url, handler_func):
    response = requests.get(url)
    status_code = response.status_code
    if status_code != 200:
        raise ValueError("Request failure at URL %s with response status code %s" % (url, status_code))
    raw_response = response.text
    return handler_func(raw_response)


def generic_post_request_wrap(url, handler_func, pl = None):
    response = requests.post(url, json = pl)
    status_code = response.status_code
    if status_code != 200:
        raise ValueError("Request failure at URL %s with response status code %s" % (url, status_code))
    raw_response = response.text
    return handler_func(raw_response)