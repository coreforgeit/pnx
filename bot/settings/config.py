import os

from zoneinfo import ZoneInfo


class Config:
    debug = bool(int(os.getenv('DEBUG')))

    if debug:
        token = os.getenv("TEST_TOKEN")
        bot_username = 'tushchkan_test_3_bot'
        google_key_path = os.path.join('data', 'cred.json')

        # pay_url = os.getenv('PAY_URL_TEST')
        # application_id = os.getenv('APPLICATION_ID_TEST')
        # pay_secret = os.getenv('PAY_SECRET_TEST')
        # store_id = os.getenv('STORE_ID_TEST')
        callback_url = 'https://webhook.site/e0fd0984-9582-43fe-a126-ed73e2d7791f'

        pay_url = os.getenv('PAY_URL')
        application_id = os.getenv('APPLICATION_ID')
        pay_secret = os.getenv('PAY_SECRET')
        store_id = os.getenv('STORE_ID')

    else:
        token = os.getenv("TOKEN")
        bot_username = 'Ponaexali_bot'
        google_key_path = os.path.join('data', 'cred.json')

        pay_url = os.getenv('PAY_URL')
        application_id = os.getenv('APPLICATION_ID')
        pay_secret = os.getenv('PAY_SECRET')
        store_id = os.getenv('STORE_ID')


        # callback_url = os.getenv('CALLBACK_URL')
        callback_url = 'http://62.113.102.141/api/v1/payment/'

    max_free_ticket = 3
    bot_link = f'https://t.me/{bot_username}?start='

    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('POSTGRES_DB')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')

    tz = ZoneInfo('Asia/Tashkent')

    path_temp = 'temp'
    date_format = '%d.%m.%Y'
    time_format = '%H:%M'
    datetime_format = '%H:%M %d.%m.%Y'


conf = Config()
