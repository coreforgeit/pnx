import os
import gspread_asyncio
from google.oauth2.service_account import Credentials

from settings import conf


def get_creds():
    creds = Credentials.from_service_account_file(conf.google_key_path)
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
