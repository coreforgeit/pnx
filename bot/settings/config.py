import os

from zoneinfo import ZoneInfo


class Config:
    debug = bool(int(os.getenv('DEBUG')))

    if debug:
        token = os.getenv("TEST_TOKEN")
        admin_chat = -4658767585
        bot_username = 'tushchkan_test_3_bot'
        google_key_path = os.path.join('data', 'cred.json')
        pay_url = "https://dev-mesh.multicard.uz/"
        application_id = os.getenv('APPLICATION_ID_TEST')
        pay_secret = os.getenv('PAY_SECRET_TEST')
        store_id = 6
        callback_url = 'https://webhook.site/ad0a6a49-b151-44ff-8bdc-8e1a4709bbc4'

    else:
        token = os.getenv("TEST_TOKEN")
        admin_chat = -4658767585
        bot_username = 'tushchkan_test_3_bot'
        google_key_path = os.path.join('data', 'cred.json')
        pay_url = "https://dev-mesh.multicard.uz/"
        application_id = os.getenv('APPLICATION_ID_TEST')
        pay_secret = os.getenv('PAY_SECRET_TEST')
        store_id = os.getenv('STORE_ID')
        callback_url = 'http://89.111.155.92/api/v1/payment/'

    test_url = 'https://webhook.site/ad0a6a49-b151-44ff-8bdc-8e1a4709bbc4'

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
