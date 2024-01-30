from datetime import datetime
import jinja2
from mail.email_utils import EmailSender
import pandas as pd
import sqlite3

leiden_postal_codes = ['2311',
    '2312',
    '2313',
    '2314',
    '2315',
    '2316',
    '2317',
    '2318',
    '2321',
    '2322',
    '2323',
    '2324',
    '2331',
    '2332',
    '2333',
    '2334'
]
leiden_postal_codes_str = "'" + "','".join(leiden_postal_codes) + "'"

# Check most recently run message list to see timestamp of most recent send
sent_message_query = """
    SELECT MAX(sent_data_upload_date)
    FROM message
"""
conn = sqlite3.connect("db/listings.db")

sent_message_max_date_df = pd.read_sql_query(sent_message_query, conn)
if sent_message_max_date_df.iloc[0, 0] is None:
    sent_message_max_date = datetime(1970, 1, 1)
else:
    sent_message_max_date = sent_message_max_date_df.iloc[0, 0]

sent_message_max_date_str = sent_message_max_date.strftime("%Y-%m-%d %H:%M:00")

# Pull listings found after that timestamp
new_listings_query = """
    SELECT url_append, upload_date, publish_date, domain, postal_code, 
        street, house_number, house_addition, locale, rent_total, area_dwelling
    FROM listings
    WHERE upload_date > '%s'
    AND (SUBSTR(postal_code, 1, 4) IN (%s) 
        OR domain = 'https://kamernet.nl')
""" % (sent_message_max_date_str, leiden_postal_codes_str)
new_listings = pd.read_sql_query(new_listings_query, conn)
if new_listings.empty:
    # Need to add in exit with no email thing
    pass

# Format into jinja friendly data
send_date_raw = datetime.now()
send_date = send_date_raw.strftime("%Y-%m-%d %H:%M:00")
listing_list = []
zebra_striped_row_color = "#e6e9f1"
is_odd = True

domain_specific_url_dict = {
    "https://www.room.nl": "/en/offerings/to-rent/details",
    "https://kamernet.nl": "",
    "https://www.pararius.com": "",
    "https://www.funda.nl": "/en/koop/leiden"

}

for _, r in new_listings.iterrows():
    listing_dict = {}

    domain_specific_url_path = domain_specific_url_dict[r['domain']]

    if r['url_append'][0] != "/":
        listing_url = "%s%s/%s" % (r['domain'], domain_specific_url_path, r['url_append'])
    else:
        listing_url = r['domain'] + domain_specific_url_path + r['url_append']
    listing_dict['url'] = listing_url

    street = r['street'].replace("-", " ").capitalize()
    house_number = r['house_number'] if r['house_number'] is not None else  ""
    house_addition = r['house_addition'] if r['house_addition'] is not None else  ""
    if house_addition not in (None, ""):
        address = "%s %s, %s" % (street, house_number, house_addition)
    else:
         address = "%s %s" % (street, house_number)
    listing_dict['address'] = address

    postal_code_raw = r['postal_code']
    if postal_code_raw is None:
        postal_code = "?"
    else:
        postal_code = postal_code_raw.replace(" ", "")
    listing_dict['postal_code'] = postal_code

    listing_dict['locale'] = r['locale'].capitalize()

    rent_total = "€%s" % r['rent_total']
    listing_dict['rent_total'] = rent_total

    listing_dict['area_dwelling'] = r['area_dwelling']

    publish_date_raw = r['publish_date']
    if publish_date_raw is None or publish_date_raw in ("1", "0"):
        publish_date = "N/A"
    else:
        publish_date = publish_date_raw[:16].replace("T", " ")
    listing_dict['publish_date'] = publish_date

    listing_dict['domain'] = r['domain']

    if is_odd:
        listing_dict['bg_color'] = zebra_striped_row_color
        is_odd = False
    else:
        listing_dict['bg_color'] = "#ffffff"
        is_odd = True

    listing_list.append(listing_dict)

# Load template assets
template_dir = "static/"
email_template_file = "email_template.html"
template_loader = jinja2.FileSystemLoader(searchpath = template_dir)
template_env = jinja2.Environment(loader=template_loader)
email_template = template_env.get_template(email_template_file)
rendered_template = email_template.render(send_date = send_date,
                                          last_send_date = sent_message_max_date_str,
                                          listing_list = listing_list)

# Mail out listings
title_str = "House Search Email for %s" % send_date
e = EmailSender()
e.send_mail(message = rendered_template,
            recipients = ['colinsyyip@gmail.com'],
            mail_title = title_str)

# Update message table with newest sent data
# TO DO