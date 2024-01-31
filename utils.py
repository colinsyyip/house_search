from bs4 import BeautifulSoup
from db.db_tables import Listing
from fake_useragent import UserAgent
from multiprocessing import Process, Queue
import random
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
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


def push_to_db(
    data,
    push_data_pk: str = "url_append",
    table=Listing,
    table_pk=Listing.url_append,
    db_url="sqlite:///db/listings.db",
):
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for data_dict in data:
            data_pk = data_dict[push_data_pk]
            query_stmt = select(table).where(table_pk == data_pk)
            query_result = conn.execute(query_stmt)
            is_exists = query_result.first()
            if not is_exists:
                insert_statement = insert(table)
                conn.execute(insert_statement, data_dict)
                conn.commit()
            else:
                update_statement = update(table).where(table_pk == data_pk)
                conn.execute(update_statement, data_dict)
        conn.close()
    return None


def generic_get_request_wrap(url, handler_func):
    response = requests.get(url)
    status_code = response.status_code
    if status_code != 200:
        raise ValueError(
            "Request failure at URL %s with response status code %s"
            % (url, status_code)
        )
    raw_response = response.text
    return handler_func(raw_response)


def generic_post_request_wrap(url, handler_func, pl=None):
    response = requests.post(url, json=pl)
    status_code = response.status_code
    if status_code != 200:
        raise ValueError(
            "Request failure at URL %s with response status code %s"
            % (url, status_code)
        )
    raw_response = response.text
    return handler_func(raw_response)


class Driver:
    def __init__(
        self,
        headless: bool = False,
        proxy_list: list = None,
        proxy_list_path: str = None,
        proxy_sequential_pick: bool = True,
        proxy_timeout: int = 10,
        selenium_timeout: int = 60,
    ):
        self.proxies = None
        self.driver_params = {
            "headless": headless,
            "selenium_timeout": selenium_timeout,
        }
        if proxy_list is not None and proxy_list_path is not None:
            raise ValueError(
                "Both proxy_list and proxy_list_path passed. Requires one or the other."
            )

        if proxy_list is not None:
            self.proxy_idx = 0
            self.proxies = proxy_list
            self.max_proxy_idx = len(self.proxies)
            self.driver_params["proxy_sequential_pick"] = proxy_sequential_pick
            self.driver_params["proxy_timeout"] = proxy_timeout
            self.thread_queue = Queue()

        if proxy_list_path is not None:
            self.proxy_idx = 1
            proxy_file = open(proxy_list_path, "r")
            raw_proxy_file = proxy_file.read()
            self.proxies = raw_proxy_file.split("\n")
            self.max_proxy_idx = len(self.proxies)
            self.driver_params["proxy_sequential_pick"] = proxy_sequential_pick
            self.driver_params["proxy_timeout"] = proxy_timeout
            self.thread_queue = Queue()

        self.driver_init(**self.driver_params)

    def threaded_proxy_driver_init(
        self, proxy_ip: str, headless: bool = False, thread_sniff: bool = False
    ):
        opts = self.driver_opts_init(headless=headless)
        opts.add_argument("--proxy-server=%s" % proxy_ip)

        driver = webdriver.Firefox(options=opts)
        driver_window_pos_x = random.randrange(0, 1920)
        driver_window_pos_y = random.randrange(0, 1080)
        driver.set_window_position(driver_window_pos_x, driver_window_pos_y)
        if thread_sniff:
            self.thread_queue.put(proxy_ip)
            print("Driver succesfully verified proxy. Quitting this instance.")
            driver.quit()
        else:
            print("Driver succesfully created at %s" % proxy_ip)
            return driver

    def driver_init(
        self,
        headless: bool = False,
        proxy_sequential_pick: bool = True,
        selenium_timeout: int = 60,
        proxy_timeout: int = 10,
        n_proxy_tries: int = 10,
    ):
        self.driver = None
        if self.proxies is not None:
            n_tries = 0
            while n_tries < n_proxy_tries:
                n_tries += 1
                proxy_ip = self.proxy_get(proxy_sequential_pick)
                driver_process = Process(
                    target=self.threaded_proxy_driver_init,
                    name="Threaded_Driver",
                    args=(proxy_ip, headless, True),
                )
                driver_process.start()
                driver_process.join(proxy_timeout)

                # breakpoint()

                if driver_process.is_alive():
                    driver_process.terminate()
                    driver_process.join()
                    continue

                succesful_proxy_ip = self.thread_queue.get()
                break
            self.driver = self.threaded_proxy_driver_init(
                succesful_proxy_ip, headless, False
            )
        else:
            opts = self.driver_opts_init(headless=headless)
            self.driver = webdriver.Firefox(options=opts)

        self.driver.set_page_load_timeout(selenium_timeout)

    def driver_opts_init(self, headless: bool = False, randomize_ua: bool = True):
        opts = webdriver.FirefoxOptions()
        opts.add_argument("--enable-javascript")
        window_x = random.randrange(1000, 2000)
        window_y = random.randrange(800, 1200)
        opts.add_argument("--width=%s" % window_x)
        opts.add_argument("--height=%s" % window_y)
        if randomize_ua:
            ua = UserAgent()
            user_agent = ua.random
            opts.add_argument("--user-agent=%s" % user_agent)
        if headless:
            opts.add_argument("--headless")

        return opts

    def proxy_get(self, sequential_pick: bool = False):
        # Switch from pop to just select and cycle through
        if sequential_pick:
            proxy_idx = self.proxy_idx
            self.proxy_idx += 1
            if self.proxy_idx == self.max_proxy_idx:
                self.proxy_idx = 0
        else:
            max_proxy_idx = len(self.proxies) - 1
            proxy_idx = random.randrange(0, max_proxy_idx)
        proxy_ip = self.proxies[proxy_idx]

        return proxy_ip

    def selenium_soup_get(
        self, url: int, test_element_class: str, by_method, load_delay: int = 10
    ):
        """
        Function for Selenium get request awaiting load of test element
        """
        try:
            self.driver.get(url)
            test_element = EC.presence_of_element_located(
                (by_method, test_element_class)
            )
            _ = WebDriverWait(self.driver, load_delay).until(test_element)
        except TimeoutException:
            self.driver.quit()
            print("Restarting driver")
            self.driver_init(**self.driver_params)
            self.driver.get(url)
            test_element = EC.presence_of_element_located(
                (by_method, test_element_class)
            )
            _ = WebDriverWait(self.driver, load_delay).until(test_element)

        resp_source = self.driver.page_source
        soup = BeautifulSoup(resp_source, "html.parser")

        return soup
