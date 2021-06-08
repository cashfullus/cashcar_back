import os
import csv
from datetime import datetime
from database.dbConnection import Database
import openpyxl as xl


BASE_FILE_LOCATION = os.getcwd() + "/static/file"

os.makedirs(BASE_FILE_LOCATION, exist_ok=True)


def datetime_to_string():
    return datetime.utcnow().strftime('%Y-%m-%d')

