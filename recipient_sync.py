import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import pandas as pd


logging.basicConfig(
    filename="house_search_logs.txt",
    filemode="a",
    level=logging.INFO,
    format="[%(asctime)s] %(name)s|%(funcName)s:%(lineno)d: %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def creds_get(
    token_path: str = "token.json",
    credentials_path: str = "credentials.json",
    SCOPES=["https://www.googleapis.com/auth/spreadsheets.readonly"],
):
    creds = None
    if os.path.exists(token_path):
        logger.info("No valid token.json found.")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token.json.")
            creds.refresh(Request())
        else:
            logger.info("Looking for crednetials.json.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    logger.info("Sheets API credentials retrieved.")

    return creds


def build_sheets_api(**kwargs):
    creds = creds_get(**kwargs)
    try:
        service = build("sheets", "v4", credentials=creds)
        logger.info("Sheets API service built.")
    except HttpError as err:
        logger.info(err)

    sheet = service.spreadsheets()

    return sheet


def pull_all_subscription_records(
    spreadsheet_id: str = os.environ.get("SHEETS_PAGE_ID"),
    range_name: str = os.environ.get("SHEETS_RANGE"),
):
    sheet = build_sheets_api()
    result = (
        sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    )
    logger.info("Values from sheet at %s retrieved." % spreadsheet_id)
    values = result.get("values", [])
    if not values:
        logger.info("Nothing found.")
        return None
    return values


def email_status_parse(
    data_df: pd.DataFrame,
    email: str,
    email_col_key: str = "email",
    date_key: str = "ts_fmt",
    action_key: str = "action",
):
    data_df_slice = data_df.loc[data_df[email_col_key].eq(email)]
    data_df_slice.sort_values(date_key, inplace=True, ascending=False)
    data_df_slice.reset_index(inplace=True)

    email_most_recent_action = data_df_slice.loc[0, action_key]

    return email_most_recent_action


def parse_subscription_records(
    values_list, value_col_names: list = ["ts", "email", "action"]
):
    values_df = pd.DataFrame(values_list)
    values_df.columns = value_col_names
    ts_key = value_col_names[0]
    ts_fmt_str = "%m/%d/%Y %H:%M:%S"
    values_df["%s_fmt" % ts_key] = pd.to_datetime(values_df["ts"], format=ts_fmt_str)
    all_emails = values_df["email"].unique()

    email_status_dict = {x: email_status_parse(values_df, x) for x in all_emails}

    return email_status_dict


def filter_subscription_dict(status_dict):
    return [k for k, v in status_dict.items() if v == "Subscribing"]


def execute_recipients_update(file_name: str = "recipients.txt", **kwargs):
    sheet_values = pull_all_subscription_records(**kwargs)
    recipient_dict = parse_subscription_records(sheet_values, **kwargs)
    final_subscription_list = filter_subscription_dict(recipient_dict, **kwargs)
    final_subscription_str = "\n".join(final_subscription_list)
    with open(file_name, "w") as f:
        f.write(final_subscription_str)
        f.close()

    logger.info("%s updated with values from mailing list sheet." % file_name)

    return None


if __name__ == "__main__":
    execute_recipients_update()
