import time

from celery import shared_task
from celery.utils.log import get_task_logger

from assignments.models import Assignment, Currency, CurrencyData, UserCurrency
from datetime import datetime, timedelta
import requests

logger = get_task_logger(__name__)


@shared_task()
def task_execute(job_params):
    assignment = Assignment.objects.get(pk=job_params["db_id"])

    assignment.sum = assignment.first_term + assignment.second_term

    assignment.save()


@shared_task()
def fetch_and_save_data():
    # Make your API request here
    logger.info("The sample task just ran")


def calculate_last_30_days_range():
    end_date = datetime.now()  # Current date and time # There is a bug
    start_date = end_date - timedelta(days=30)  # 30 days ago

    # Exclude Sundays and Mondays from the date range
    while start_date <= end_date:
        if start_date.weekday() in [0, 6]:  # Monday is 0, Sunday is 6
            start_date += timedelta(days=1)  # Move to the next day
        else:
            break

    return start_date, end_date


def fetch_actual_currency_data(start_date=None, end_date=None):
    """
    Make an API request to Central Russian Bank to extract information for today.
    """
    if not start_date or not end_date:
        url = 'https://www.cbr-xml-daily.ru/daily_json.js'

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception


def update_currency_data():
    """
    Extract currency from the database. In case we don't have any currency, populate
    database with the data from received JSON file. Otherwise, just update the "date" and
    "price" columns in existing currency data.

    Some edge cases which must be considered:
    TODO: API provides new currencies, which do not exist in Currency table.
    """

    actual_currency_data = fetch_actual_currency_data()
    currencies = Currency.objects.all()

    # If there are no currencies in the DataBase, create new and populate data for the current day.
    if len(currencies) == 0:
        for currency_code, currency_info in actual_currency_data['Valute'].items():
            created_currency = Currency.objects.create(char_code=currency_code)
            datetime_obj = datetime.fromisoformat(actual_currency_data["Date"])
            date = datetime_obj.date()

            price = currency_info["Value"]
            CurrencyData.objects.create(currency=created_currency, date=date, price=price)

    # Otherwise update data for today for all currencies.
    else:
        for currency_code, currency_info in actual_currency_data['Valute'].items():
            currency = Currency.objects.get(char_code=currency_code)
            price = currency_info['Value']
            datetime_obj = datetime.fromisoformat(actual_currency_data["Date"])
            date = datetime_obj.date()

            update_existing_currency_data(currency, date, price)


    # Update Currency data for the last 30 days excluding Mondays and Sundays


    end_date = datetime.now()  # Current date and time # There is a bug
    start_date = end_date - timedelta(days=30)  # 30 days ago

    current_date = start_date
    while current_date <= end_date:
        # Construct the API URL for the current date
        month_str = str(current_date.month).zfill(2)
        day_str = str(current_date.day).zfill(2)
        api_url = f"https://www.cbr-xml-daily.ru/archive/{current_date.year}/{month_str}/{day_str}/daily_json.js"

        # Make the API request
        response = requests.get(api_url)

        # Check if the API request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()

            # Process and save the data to the CurrencyData model
            for currency_code, currency_info in data['Valute'].items():

                currency = Currency.objects.get(char_code=currency_code)
                price = currency_info['Value']
                datetime_obj = datetime.fromisoformat(actual_currency_data["Date"])
                date = datetime_obj.date()

                update_existing_currency_data(currency, date, price)

        # Wait 0.5 second in order to keel the limit of API calls per second.
        # Move to the next day
        time.sleep(0.5)
        current_date += timedelta(days=1)


def update_existing_currency_data(currency, current_date, price):
    """
    In case there exists data about currency for the specified date in the DataBase, we update price
    Otherwise, we add information about currency for the specified date in the DataBase.
    """

    existing_currency_data = CurrencyData.objects.filter(currency=currency, date=current_date).first()

    if existing_currency_data:
        # Check if the price is different
        if existing_currency_data.price != price:
            # Update the price if it's different
            existing_currency_data.price = price
            existing_currency_data.save()
    else:
        # Create a new CurrencyData object if it doesn't exist
        currency_data = CurrencyData(currency=currency, date=current_date, price=price)
        currency_data.save()
