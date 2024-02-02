# Instantiatable classes for specific rental sites. Classes hold raw data but return formatted data

from copy import deepcopy
from datetime import datetime, timedelta
import json
import logging
from math import ceil
import puller_configs
import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import utils


logger = logging.getLogger(__name__)


class Room:
    """
    Queries Room for rental information straight from Hexia
    """

    def __init__(self, domain: str = puller_configs.ROOM_DOMAIN):
        """
        On initialization immediately queries for results and loads relevant mapping configs
        """
        self.site_domain = domain
        search_domain = puller_configs.ROOM_RESULT_METADATA_DOMAIN
        total_results_count = self.get_total_results_count(
            total_result_domain=search_domain
        )
        fmted_search_params = puller_configs.ROOM_SEARCH_PARAMS % total_results_count
        search_url = search_domain + fmted_search_params
        self.rentals = self.get_total_results(result_search_url=search_url)
        mapping_f = open(puller_configs.ROOM_DB_KEY_MAP_PATH)
        self.db_mapping_dict = json.load(mapping_f)
        logger.info("Room init. complete")

    def get_total_results_count(self, total_result_domain: str):
        """
        Wrapper for getting total number of results from Room Hexia API
        """
        total_results_count_resp_dict = utils.generic_get_request_wrap(
            total_result_domain, json.loads
        )
        n_total_results = total_results_count_resp_dict["_metadata"][
            "total_search_count"
        ]

        return n_total_results

    def get_total_results(self, result_search_url: str):
        """
        Wrapper for pulling all rentals from Room Hexia API
        """
        total_results_resp_dict = utils.generic_get_request_wrap(
            result_search_url, json.loads
        )
        result_rentals = total_results_resp_dict["data"]

        return result_rentals

    def parse_rental_obj(
        self, rental_obj: dict, layer1_target_keys: list, layern_target_keys: list
    ):
        """
        Recursively extract nested values from rental JSON return as define by target key params
        """
        parsed_results = {}
        # Layer 1 handling for standard dict key value return
        if layer1_target_keys is not None:
            l1_results = {x: rental_obj[x] for x in layer1_target_keys}
            parsed_results.update(l1_results)
            if layern_target_keys is None:
                return l1_results
        l2_results = {}
        # Check for multi layer keys
        for ln_key in layern_target_keys:
            layernm1_key = ln_key.pop(0)
            layernm1_obj = rental_obj[layernm1_key]
            # Final layer if length of key list is 1 - return value through l2_results
            if len(ln_key) == 1:
                ln_key_str = ln_key[0]
                ln_result = self.parse_rental_obj(
                    layernm1_obj, layer1_target_keys=ln_key, layern_target_keys=None
                )
                ln_result_key = "%s_%s" % (layernm1_key, ln_key_str)
                l2_results[ln_result_key] = ln_result[ln_key_str]
            # If key list is > 1, continue to dig with layer1_target_keys being None
            elif len(ln_key) > 1:
                # ln_key_new_lead = ln_key[0]
                ln_key_list_sub_keys = ln_key[1:]
                if len(ln_key_list_sub_keys) == 1:
                    l2_results = self.parse_rental_obj(
                        layernm1_obj,
                        layer1_target_keys=ln_key_list_sub_keys,
                        layern_target_keys=None,
                    )
                else:
                    l2_results = self.parse_rental_obj(
                        layernm1_obj,
                        layer1_target_keys=None,
                        layern_target_keys=[ln_key_list_sub_keys],
                    )
            elif len(ln_key) == 0:
                l2_results = {layernm1_key: layernm1_obj}
                return l2_results

        parsed_results.update(l2_results)

        return parsed_results

    def parse_rentals(
        self,
        L1_keymap: list = puller_configs.ROOM_L1_TARGET_RENTAL_KEYS,
        Ln_keymap: list = puller_configs.ROOM_Ln_TARGET_RENTAL_KEYS,
    ):
        """
        Shorten extracted rentals into DB friendly format and prepare for upload to DB
        """

        logger.info("Starting Room parse")

        shortened_results = []
        for rental_obj in self.rentals:
            tmp_l1_keys = deepcopy(L1_keymap)
            tmp_ln_keys = deepcopy(Ln_keymap)

            if "postalcode" not in rental_obj and "postalcode" in tmp_l1_keys:
                tmp_l1_keys.pop(tmp_l1_keys.index("postalcode"))
                if "postcode" in rental_obj:
                    tmp_l1_keys.append("postcode")

            if "street" not in rental_obj:
                continue

            if "houseNumber" not in rental_obj:
                continue

            if "gemeenteGeoLocatieNaam" not in rental_obj:
                continue

            if rental_obj["gemeenteGeoLocatieNaam"] is None:
                continue

            truncated_info_dict = self.parse_rental_obj(
                rental_obj, tmp_l1_keys, tmp_ln_keys
            )
            if "specifiekeVoorzieningen" in truncated_info_dict:
                amenity_details = truncated_info_dict["specifiekeVoorzieningen"]
                amenity_list = [x["localizedName"] for x in amenity_details]
                amenity_str = ", ".join(amenity_list)
                truncated_info_dict["specifiekeVoorzieningen"] = amenity_str
            truncated_info_dict["domain"] = self.site_domain
            renamed_info_dict = {
                self.db_mapping_dict[k]: v for k, v in truncated_info_dict.items()
            }
            shortened_results.append(renamed_info_dict)

        logger.info("Finished Room parse")

        return shortened_results


class Kamernet:
    """
    Queries Kamernet for rental information straight from .NET WebAPI
    """

    def __init__(self, domain: str = puller_configs.KAMERNET_DOMAIN):
        self.site_domain = domain
        search_domain = puller_configs.KAMERNET_SEARCH_DOMAIN
        init_search_pl = deepcopy(puller_configs.KAMERNET_SEARCH_PL)
        init_search_pl["pageNo"] = init_search_pl["pageNo"] % 1
        total_results_count = self.get_total_results_count(
            total_result_domain=search_domain, total_result_payload=init_search_pl
        )
        self.rentals = self.get_total_results(
            result_search_url=search_domain, total_results=total_results_count
        )
        mapping_f = open(puller_configs.KAMERNET_DB_KEY_MAP_PATH)
        self.db_mapping_dict = json.load(mapping_f)
        logger.info("Kamernet init. complete")

    def get_total_results_count(
        self, total_result_domain: str, total_result_payload: dict
    ):
        """
        Wrapper for getting total number of results from Kamernet .NET WebAPI
        """
        total_results_count_resp_dict = utils.generic_post_request_wrap(
            total_result_domain, handler_func=json.loads, pl=total_result_payload
        )
        n_total_results = total_results_count_resp_dict["total"]

        return n_total_results

    def get_total_results(
        self, result_search_url: str, total_results: int, results_per_page: int = 18
    ):
        """
        Wrapper for pulling all rentals from Kamernet .NET WebAPI, iterating over page sizes as needed
        """
        n_pages_required = ceil(total_results / results_per_page)
        total_results = []
        for page_i in range(1, n_pages_required + 1):
            page_payload = deepcopy(puller_configs.KAMERNET_SEARCH_PL)
            page_payload["pageNo"] = page_payload["pageNo"] % page_i
            page_results = utils.generic_post_request_wrap(
                result_search_url, handler_func=json.loads, pl=page_payload
            )
            page_results_listings = page_results["listings"]
            total_results += page_results_listings

            sleep(5)

        return total_results

    def parse_rental_obj(self, rental_obj: dict, layer1_target_keys: list):
        """
        Extract and format relevant keys from raw returned rental objects
        """
        parsed_results = {k: rental_obj[k] for k in layer1_target_keys}

        # Specific handling of remap for furnishingId
        furnishing_map = puller_configs.KAMERNET_FURNISHING_MAP
        obj_furnishing_id = parsed_results["furnishingId"]
        parsed_results["furnishingId"] = furnishing_map[obj_furnishing_id]

        # Conversion of availability dates back to datetimes
        if parsed_results["availabilityStartDate"] is not None:
            avail_start = parsed_results["availabilityStartDate"]
            avail_start_dt = datetime.strptime(avail_start[:10], "%Y-%m-%d")
            parsed_results["availabilityStartDate"] = avail_start_dt

        if parsed_results["availabilityEndDate"] is not None:
            avail_end = parsed_results["availabilityEndDate"]
            avail_end_dt = datetime.strptime(avail_end[:10], "%Y-%m-%d")
            parsed_results["availabilityEndDate"] = avail_end_dt

        # Specific handling of remap for listingType
        listing_type_map = puller_configs.KAMERNET_LISTING_TYPE_MAP
        obj_listing_type_id = parsed_results["listingType"]
        parsed_results["listingType"] = listing_type_map[obj_listing_type_id]

        # Cleaning street str
        parsed_results["street"] = parsed_results["street"].lower().replace(" ", "-")

        # Cleaning city str
        parsed_results["city"] = parsed_results["city"].lower().replace(" ", "-")

        # Rebuilding url_append
        url_append_fmter = "/en/for-rent/%s-%s/%s/%s-%.0f"
        fmted_url_append = url_append_fmter % (
            parsed_results["listingType"],
            parsed_results["city"],
            parsed_results["street"],
            parsed_results["listingType"],
            parsed_results["listingId"],
        )
        parsed_results["url_append"] = fmted_url_append
        parsed_results["domain"] = self.site_domain

        return parsed_results

    def parse_rentals(self):
        """
        Parse all rental objects and remap keys for DB upsert
        """
        logger.info("Starting Kamernet parse")
        full_parsed_rental_objs = [
            self.parse_rental_obj(x, puller_configs.KAMERNET_L1_KEYS)
            for x in self.rentals
        ]
        key_remapped_objs = [
            {self.db_mapping_dict[k]: v for k, v in x.items()}
            for x in full_parsed_rental_objs
        ]

        logger.info("Finished Kamernet parse")

        return key_remapped_objs


class Pararius:
    """
    Queries Pararius for rental information using Selenium
    """

    def __init__(
        self,
        domain: str = puller_configs.PARARIUS_DOMAIN,
        headless=True,
        proxy_list: list = None,
        proxy_list_path: str = puller_configs.PROXY_PATH,
    ):
        self.site_domain = domain
        self.driver = utils.Driver(
            headless=headless, proxy_list=proxy_list, proxy_list_path=proxy_list_path
        )
        init_search_url = puller_configs.PARARIUS_SEARCH_URL % 1
        init_search_soup = self.driver.selenium_soup_get(
            init_search_url, test_element_class="search-list", by_method=By.CLASS_NAME
        )
        all_listing_links = self.get_all_listing_links(
            init_search_soup, puller_configs.PARARIUS_SEARCH_URL
        )
        self.all_listing_links_unique = list(set(all_listing_links))
        logger.info("Pararius init. complete")

    def get_total_results_count(self, soup):
        """
        Extracts total listings count from generic search page
        """
        listing_total_attrs = {"class": "search-list-header__count"}
        title_obj = soup.find("span", attrs=listing_total_attrs)
        return int(title_obj.text)

    def get_single_page_listings(self, soup):
        """
        Retrieve all listing links on a search page
        """
        listings = soup.find_all(
            "li", attrs={"class": "search-list__item search-list__item--listing"}
        )
        title_attrs = {"class": "listing-search-item__title"}
        listing_title_objs = [x.find("h2", attrs=title_attrs) for x in listings]
        listing_links = [x.find("a").get("href") for x in listing_title_objs]
        return listing_links

    def get_all_listing_links(self, starter_soup, search_url: str):
        """
        Overall executor for retriveing all listing links
        """
        total_listing_n = self.get_total_results_count(starter_soup)

        listing_count = 0
        page_i = 1

        all_listing_urls = []

        while listing_count < total_listing_n:
            fmted_search_url = search_url % page_i
            search_soup = self.driver.selenium_soup_get(
                fmted_search_url,
                test_element_class="search-list",
                by_method=By.CLASS_NAME,
            )
            listing_urls = self.get_single_page_listings(search_soup)
            all_listing_urls += listing_urls

            sleep(random.randrange(2, 10))

            listing_count += len(listing_urls)
            page_i += 1

        all_listing_urls = list(set(all_listing_urls))

        return all_listing_urls

    def parse_rental_obj(self, listing_link: str, sleep_buffer: bool = True):
        """
        Get DOM of and parse relevant data for a single listing URL
        """
        listing_full_url = self.site_domain + listing_link
        logger.info("Parsing %s" % listing_full_url)
        listing_soup = self.driver.selenium_soup_get(
            listing_full_url,
            test_element_class="listing-detail-summary__title",
            by_method=By.CLASS_NAME,
        )

        listing_dict = {}

        # Get street/city
        listing_dict["url_append"] = listing_link
        url_portions = listing_link.split("/")
        if url_portions[2] == "project":
            return None
        street_str = url_portions[-1].capitalize()
        locale_str = url_portions[2].capitalize()
        listing_dict["domain_id"] = url_portions[3]
        listing_dict["street"] = street_str
        listing_dict["locale"] = locale_str

        # Get postal/district
        postal_code_attrs = {"class": "listing-detail-summary__location"}
        postal_code_raw_str = listing_soup.find("div", attrs=postal_code_attrs).text
        postal_code_str = postal_code_raw_str.split(" (")[0].replace(" ", "")
        district_str = postal_code_raw_str.split(" (")[1][:-1]
        listing_dict["postal_code"] = postal_code_str
        listing_dict["locale"] = locale_str

        # Get transfer info
        transfer_info_attrs = {"class": "listing-features__list"}
        transfer_info_obj = listing_soup.find("dl", attrs=transfer_info_attrs)
        transfer_lineitem_attrs = {"class": "listing-features__main-description"}
        transfer_lineitem_objs = transfer_info_obj.find_all(
            "span", attrs=transfer_lineitem_attrs
        )
        transfer_lineitem_raw_texts = [x.text for x in transfer_lineitem_objs]

        price_obj_attrs = {
            "class": "listing-features__description listing-features__description--for_rent_price"
        }
        price_obj = transfer_info_obj.find("dd", attrs=price_obj_attrs)
        sub_price_obj_attrs = {"class": "listing-features__sub-description"}
        sub_price_obj = price_obj.find("ul", attrs=sub_price_obj_attrs)
        if sub_price_obj is not None:
            sub_price_text = sub_price_obj.find("li").text
            if "Includes" in sub_price_text:
                listing_dict["additional_costs"] = 1
            else:
                listing_dict["additional_costs"] = 0

        service_costs_attrs = {
            "class": "listing-features__description listing-features__description--service_costs"
        }
        service_costs_obj = transfer_info_obj.find("dd", attrs=service_costs_attrs)
        if service_costs_obj is not None:
            service_costs_raw = service_costs_obj.find("span").text
            service_costs_str = "".join(re.findall("\d*", service_costs_raw))
            listing_dict["additional_costs"] = int(service_costs_str)

        price_idx = 0
        posted_idx = 1
        available_idx = 3
        furnished_idx = 4

        price_value = transfer_lineitem_raw_texts[price_idx]
        if "Price on request" in price_value:
            listing_dict["rent_total"] = -1
        else:
            price_re_find = re.findall("\d*", price_value)
            price_num = int("".join([x for x in price_re_find if x != ""]))
            listing_dict["rent_total"] = price_num

        posted_value = transfer_lineitem_raw_texts[posted_idx]
        if "weeks" in posted_value:
            num_weeks = int(re.findall("\d*", posted_value)[0])
            today_date = datetime.now()
            time_diff = timedelta(weeks=num_weeks)
            posted_date = today_date - time_diff
        elif "months" in posted_value:
            num_months = int(re.findall("\d*", posted_value)[0])
            today_date = datetime.now()
            weeks_constant = 4.33
            time_diff = timedelta(weeks=num_months * weeks_constant)
            posted_date = today_date - time_diff
        else:
            posted_date = datetime.strptime(posted_value, "%d-%m-%Y")
        listing_dict["publish_date"] = posted_date

        available_date = transfer_lineitem_raw_texts[available_idx]
        if "From" in available_date:
            available_date_split = available_date.split(" ")
            available_date_value = datetime.strptime(
                available_date_split[1], "%d-%m-%Y"
            )
        elif available_date == "Immediately":
            available_date_value = datetime.now()
        elif available_date == "In consultation":
            available_date_value = datetime.now()
        listing_dict["available_date"] = available_date_value

        furnished_info = transfer_lineitem_raw_texts[furnished_idx]
        listing_dict["additional_info"] = [furnished_info]

        # Get dimensions info
        surface_area_attrs = {
            "class": "listing-features__description listing-features__description--surface_area"
        }
        surface_area_obj = listing_soup.find("dd", attrs=surface_area_attrs)
        surface_area_text_obj = surface_area_obj.find("span")
        surface_area_text = surface_area_text_obj.text.split(" ")[0]
        listing_dict["area_dwelling"] = int(surface_area_text)

        # Dwelling type check
        dwelling_type_attrs = {
            "class": "listing-features__description listing-features__description--dwelling_type"
        }
        dwelling_obj = listing_soup.find("dd", attrs=dwelling_type_attrs)
        if dwelling_obj is not None:
            dwelling_type = dwelling_obj.find("span").text
            listing_dict["dwelling_type"] = dwelling_type

        # Property type check
        proprety_type_attrs = {
            "class": "listing-features__description listing-features__description--property_types"
        }
        property_obj = listing_soup.find("dd", attrs=proprety_type_attrs)
        if property_obj is not None:
            property_type = property_obj.find("span").text
            listing_dict["building_Type"] = property_type

        listing_dict["additional_costs"] = None
        listing_dict["additional_info"] = ";".join(listing_dict["additional_info"])
        listing_dict["domain"] = self.site_domain

        if sleep_buffer:
            sleep(random.randint(2, 10))

        return listing_dict

    def parse_rentals(self):
        """
        Executor for parsing all listings in self.all_listing_links_unique
        """
        logger.info("Starting Pararius parse")
        all_parsed = [self.parse_rental_obj(x) for x in self.all_listing_links_unique]
        stripped_parsed_listings = [x for x in all_parsed if x is not None]

        logger.info("Finished Pararius parse")

        return stripped_parsed_listings


class Funda:
    """
    Queries Funda for rental information using Selenium
    """

    def __init__(
        self,
        domain: str = puller_configs.FUNDA_DOMAIN,
        headless=True,
        proxy_list: list = None,
        proxy_list_path: str = puller_configs.PROXY_PATH,
    ):
        self.site_domain = domain
        self.driver = utils.Driver(
            headless=headless, proxy_list=proxy_list, proxy_list_path=proxy_list_path
        )
        init_search_url = puller_configs.FUNDA_SEARCH_URL % 1
        init_search_soup = self.driver.selenium_soup_get(
            init_search_url,
            "//div[@data-test-id='search-result-item']",
            by_method=By.XPATH,
        )
        all_listing_links = self.get_all_listing_links(
            init_search_soup, puller_configs.FUNDA_SEARCH_URL
        )
        self.all_listing_links_unique = list(set(all_listing_links))
        logger.info("Funda init. complete")

    def get_total_results_count(self, soup):
        """
        Extracts total listings count from generic search page
        """
        rental_count_div_attrs = {
            "class": "overflow-hidden text-ellipsis whitespace-nowrap font-semibold"
        }
        rental_count_obj = soup.find_all("div", attrs=rental_count_div_attrs)[0]
        rental_count_text = rental_count_obj.text
        rental_count_str_split = rental_count_text.replace(" ", "").split("\n")
        rental_count_num = int(rental_count_str_split[1])

        return rental_count_num

    def get_all_listing_links(self, starter_soup, search_url: str, n_results: int = 15):
        """
        Retrieve all listing links
        """
        total_listing_count = self.get_total_results_count(starter_soup)
        page_count = ceil(total_listing_count / n_results)

        result_links = []

        for page_num in range(1, page_count + 1):
            page_search_url = search_url % page_num
            page_soup = self.driver.selenium_soup_get(
                page_search_url,
                "//div[@data-test-id='search-result-item']",
                by_method=By.XPATH,
            )
            result_divs = page_soup.find_all(
                "div", attrs={"data-test-id": "search-result-item"}
            )
            for result in result_divs:
                listing_name_obj = result.find_all(
                    "a",
                    attrs={"class": "text-blue-2 visited:text-purple-1 cursor-pointer"},
                )[0]
                listing_link = listing_name_obj["href"]

                result_links.append(listing_link)

            sleep(random.randrange(3, 10))

        return result_links

    def parse_rental_obj(self, listing_link: str, sleep_buffer: bool = True):
        """
        Get DOM of and parse relevant data for a single listing URL
        """
        # Insert en for english results
        logger.info("Parsing %s" % listing_link)
        en_swapped_listing_link = listing_link.replace(
            "https://www.funda.nl/", "https://www.funda.nl/en/"
        )
        # bare_driver_instance = self.driver.driver
        result_soup = self.driver.selenium_soup_get(
            en_swapped_listing_link,
            "//span[@class='object-header__title']",
            by_method=By.XPATH,
        )

        listing_dict = {}

        domain_stripped_url = listing_link.split("leiden")[1]
        url_append = listing_link.split("leiden")[1]
        domain_id = domain_stripped_url.split("-")[1]

        # Street/house number/addition
        house_info_obj = result_soup.find_all("span", "object-header__title")[0]
        house_info_text = house_info_obj.text
        house_info_list = house_info_text.split(" ")
        street = house_info_list[0]
        house_number = house_info_list[1]
        if len(house_info_list) > 2:
            house_addition = house_info_list[2]
        else:
            house_addition = None

        # Neighbourhood/postal code
        postal_code_obj = result_soup.find_all(
            "span", "object-header__subtitle fd-color-dark-3"
        )[0]
        postal_code_text = postal_code_obj.text
        postal_code_text_list = postal_code_text.split(" ")
        postal_code_str_list = postal_code_text_list[:2]
        postal_code = "".join(postal_code_str_list)
        neighbourhood_title_span = result_soup.find_all(
            "span", "fd-text--ellipsis fd-text--nowrap fd-overflow-hidden"
        )[-1]
        locale = neighbourhood_title_span.text.replace(" ", "")

        # Ownership details
        table_headers = result_soup.find_all("h3", "object-kenmerken-list-header")
        table_headers_text = [x.text for x in table_headers]
        tables = result_soup.find_all("dl", "object-kenmerken-list")
        singular_table = False
        if len(table_headers_text) == 0:
            singular_table = True
        table_dict = dict(zip(table_headers_text, tables))

        # Area dwelling
        if not singular_table:
            area_objects = result_soup.find_all(
                "span", "kenmerken-highlighted__value fd-text--nowrap"
            )
            if len(area_objects) == 0:
                area_dwelling = 0
            else:
                sq_m_obj = area_objects[0]
                area_dwelling = int(sq_m_obj.text.replace(" m²", ""))

            try:
                ownership_table = table_dict["Transfer of ownership"]
            except KeyError:
                ownership_table = table_dict["Overdracht"]
            ownership_table_keys = [x.text for x in ownership_table.find_all("dt")]
            ownership_table_values = [
                x.text for x in ownership_table.find_all("dd") if x.find("dd") is None
            ]
            ownership_table_dict = dict(
                zip(ownership_table_keys, ownership_table_values)
            )

            if (
                "Rental agreement" in ownership_table_dict
                or "Huurovereenkomst" in ownership_table_dict
            ):
                rent_buy = "Rent"
            else:
                rent_buy = "Buy"

            if ownership_table_dict["Status"].replace("\n", "") == "Available":
                available_date = datetime.now()
            elif ownership_table_dict["Status"].replace("\n", "") == "Beschikbaar":
                available_date = datetime.now()
            else:
                available_date = None

            try:
                rent_total_str = ownership_table_dict["Rental price "]
            except KeyError:
                rent_total_str = ownership_table_dict["Huurprijs "]

            if (
                "Huurprijs op aanvraag" in rent_total_str
                or "Rental price on request" in rent_total_str
            ):
                rent_total = -1
            else:
                rent_numeric_match = re.search(
                    "(\d+\.||\.)*\d{3}", rent_total_str
                ).group()
                rent_total = int(re.sub("\,|\.", "", rent_numeric_match))

        else:
            feature_table = tables[0]
            rent_buy = "Rent"
            available_date = datetime.now()

            feature_table = tables[0]
            feature_table_keys = [x.text for x in feature_table.find_all("dt")]
            feature_table_values = [
                x.text for x in feature_table.find_all("dd") if x.find("dd") is None
            ]
            feature_table_dict = dict(zip(feature_table_keys, feature_table_values))

            try:
                area_dwelling_str = feature_table_dict["Area"]
            except KeyError:
                area_dwelling_str = feature_table_dict["Oppervlakte"]
            area_dwelling = int(area_dwelling_str.split(" ")[0])

            try:
                rent_total_str = feature_table_dict["Rental price "]
            except KeyError:
                rent_total_str = feature_table_dict["Huurprijs "]

            if (
                "Huurprijs op aanvraag" in rent_total_str
                or "Rental price on request" in rent_total_str
            ):
                rent_total = -1
            else:
                rent_numeric_match = re.search(
                    "(\d+\.||\.)*\d{3}", rent_total_str
                ).group()
                rent_total = int(re.sub("\,|\.", "", rent_numeric_match))

            rent_numeric_match = re.search("(\d+\.||\.)*\d{3}", rent_total_str).group()
            rent_total = int(re.sub("\,|\.", "", rent_numeric_match))

        listing_dict["url_append"] = url_append
        listing_dict["domain"] = self.site_domain
        listing_dict["domain_id"] = domain_id
        listing_dict["postal_code"] = postal_code
        listing_dict["street"] = street
        listing_dict["house_number"] = house_number
        listing_dict["house_addition"] = house_addition
        listing_dict["locale"] = locale
        listing_dict["rent_buy"] = rent_buy
        listing_dict["available_date"] = available_date
        listing_dict["area_dwelling"] = area_dwelling
        listing_dict["rent_total"] = rent_total

        if sleep_buffer:
            sleep(random.randint(2, 5))

        return listing_dict

    def parse_rentals(self):
        """
        Executor for parsing all listings in self.all_listing_links_unique
        """
        logger.info("Starting Funda parse")
        all_parsed = [self.parse_rental_obj(x) for x in self.all_listing_links_unique]
        logger.info("Finished Funda parse")
        return all_parsed
