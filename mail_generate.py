from datetime import datetime
from db.db_tables import Message
import jinja2
from mail.email_utils import EmailSender
import os
import pandas as pd
import sqlite3
from utils import push_to_db


class MailGenerator:
    def __init__(self, db_url: str = "db/listings.db"):
        self.conn = sqlite3.connect(db_url)
        self.max_prior_send_date = self.retrieve_max_prior_send()
        self.new_listings = self.retrieve_new_listings(
            max_send_date=self.max_prior_send_date
        )
        self.send_date_raw = datetime.now()
        self.send_date = self.send_date_raw.strftime("%Y-%m-%d %H:%M:00")
        self.template_prepped_listings = self.format_listing_data()
        self.rendered_email_template = self.render_template()

    def retrieve_max_prior_send(self):
        """
        Check most recently run message list to see timestamp of most recent send
        """
        sent_message_query = """
            SELECT MAX(sent_data_upload_date)
            FROM message
        """
        sent_message_max_date_df = pd.read_sql_query(sent_message_query, self.conn)
        if sent_message_max_date_df.iloc[0, 0] is None:
            sent_message_max_date_str = datetime(1970, 1, 1)
        else:
            sent_message_max_date_str = sent_message_max_date_df.iloc[0, 0]

        return sent_message_max_date_str

    def retrieve_new_listings(self, max_send_date: str):
        """
        Pull listings found after that timestamp
        """
        leiden_postal_codes = [
            "2311",
            "2312",
            "2313",
            "2314",
            "2315",
            "2316",
            "2317",
            "2318",
            "2321",
            "2322",
            "2323",
            "2324",
            "2331",
            "2332",
            "2333",
            "2334",
        ]
        leiden_postal_codes_str = "'" + "','".join(leiden_postal_codes) + "'"
        new_listings_query = """
            SELECT url_append, upload_date, publish_date, domain, postal_code, 
                street, house_number, house_addition, locale, rent_total, area_dwelling
            FROM listings
            WHERE upload_date > '%s'
            AND (SUBSTR(postal_code, 1, 4) IN (%s) 
                OR domain = 'https://kamernet.nl')
        """ % (
            max_send_date,
            leiden_postal_codes_str,
        )
        new_listings = pd.read_sql_query(new_listings_query, self.conn)
        if new_listings.empty:
            # Need to add in exit with no email thing
            return None
        return new_listings

    def format_listing_data(self):
        """
        Format into jinja friendly data
        """
        listing_list = []
        zebra_striped_row_color = "#e6e9f1"
        is_odd = True

        domain_specific_url_dict = {
            "https://www.room.nl": "/en/offerings/to-rent/details",
            "https://kamernet.nl": "",
            "https://www.pararius.com": "",
            "https://www.funda.nl": "/en/koop/leiden",
        }

        all_sent_url_appends = []

        for _, r in self.new_listings.iterrows():
            listing_dict = {}

            domain_specific_url_path = domain_specific_url_dict[r["domain"]]

            if r["url_append"][0] != "/":
                listing_url = "%s%s/%s" % (
                    r["domain"],
                    domain_specific_url_path,
                    r["url_append"],
                )
            else:
                listing_url = r["domain"] + domain_specific_url_path + r["url_append"]
            listing_dict["url"] = listing_url
            all_sent_url_appends.append(r["url_append"])

            street = r["street"].replace("-", " ").capitalize()
            house_number = r["house_number"] if r["house_number"] is not None else ""
            house_addition = (
                r["house_addition"] if r["house_addition"] is not None else ""
            )
            if house_addition not in (None, ""):
                address = "%s %s, %s" % (street, house_number, house_addition)
            else:
                address = "%s %s" % (street, house_number)
            listing_dict["address"] = address

            postal_code_raw = r["postal_code"]
            if postal_code_raw is None:
                postal_code = "?"
            else:
                postal_code = postal_code_raw.replace(" ", "")
            listing_dict["postal_code"] = postal_code

            listing_dict["locale"] = r["locale"].capitalize()

            rent_total = "€%s" % r["rent_total"]
            listing_dict["rent_total"] = rent_total

            listing_dict["area_dwelling"] = r["area_dwelling"]

            publish_date_raw = r["publish_date"]
            if publish_date_raw is None or publish_date_raw in ("1", "0"):
                publish_date = "N/A"
            else:
                publish_date = publish_date_raw[:16].replace("T", " ")
            listing_dict["publish_date"] = publish_date

            listing_dict["domain"] = r["domain"]

            if is_odd:
                listing_dict["bg_color"] = zebra_striped_row_color
                is_odd = False
            else:
                listing_dict["bg_color"] = "#ffffff"
                is_odd = True

            listing_list.append(listing_dict)

        return listing_list

    def render_template(
        self,
        email_template_dir: str = "static/",
        email_template_file: str = "email_template.html",
    ):
        """
        Load template assets
        """
        template_loader = jinja2.FileSystemLoader(searchpath=email_template_dir)
        template_env = jinja2.Environment(loader=template_loader)
        email_template = template_env.get_template(email_template_file)
        rendered_template = email_template.render(
            send_date=self.send_date,
            last_send_date=self.max_prior_send_date,
            listing_list=self.template_prepped_listings,
        )

        return rendered_template

    def retrieve_recipients(self, recipient_file_path: str = "recipients.txt"):
        """
        Pull recipient list
        """
        recipients_file = open(recipient_file_path, "r")
        recipients_text = recipients_file.read()
        recipient_list = recipients_text.split("\n")
        recipients_file.close()

        return recipient_list

    def execute_mail(self, rendered_template=None):
        """
        Mail out listings
        """
        recipient_list = self.retrieve_recipients()
        if rendered_template is None:
            rendered_template = self.rendered_email_template
        title_str = "House Search Email for %s" % self.send_date
        e = EmailSender()
        e.send_mail(
            message=rendered_template, recipients=recipient_list, mail_title=title_str
        )

        print("Emails sent succesfully.")

        self.push_logs_to_db(recipient_list, self.send_date_raw)

    def push_logs_to_db(
        self,
        recipient_list: list,
        send_date_raw,
        app_user_email_key: str = "GMAIL_USER_EMAIL",
    ):
        """
        Update message table with newest sent data
        """
        sent_data_upload_date_raw = self.new_listings["upload_date"][0]
        sent_data_upload_date = datetime.strptime(
            sent_data_upload_date_raw, "%Y-%m-%d %H:%M:00"
        )

        all_sent_url_appends = [
            r["url_append"] for _, r in self.new_listings.iterrows()
        ]
        message_table_data = [
            {"recipient": x, "sent_url_append": y}
            for y in all_sent_url_appends
            for x in recipient_list
        ]
        [
            x.update({"sender": os.environ.get(app_user_email_key)})
            for x in message_table_data
        ]
        [x.update({"send_date": send_date_raw}) for x in message_table_data]
        [
            x.update({"sent_data_upload_date": sent_data_upload_date})
            for x in message_table_data
        ]

        push_to_db(
            message_table_data,
            push_data_pk="sent_url_append",
            table=Message,
            table_pk=Message.sent_url_append,
        )
