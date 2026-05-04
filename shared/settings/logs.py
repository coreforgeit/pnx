from datetime import datetime

import logging
import traceback
import os
import re

from .config import conf


def log_error(message, wt: bool = True) -> tuple[str, str]:
    now = datetime.now(conf.tz)
    log_folder = now.strftime ('%m-%Y')
    log_path = os.path.join('logs', log_folder)

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file_path = os.path.join(log_path, f'{now.day}.log')
    logging.basicConfig (level=logging.WARNING, filename=log_file_path, encoding='utf-8')
    if wt:
        ex_traceback = traceback.format_exc()
        tb = ''
        msg = ''
        start_row = '  File "/app'
        tb_split = ex_traceback.split('\n')
        for row in tb_split:
            if row.startswith(start_row) and not re.search ('venv', row):
                tb += f'{row}\n'

            if not row.startswith(' '):
                msg += f'{row}\n'

        logging.warning(f'{now}\n{tb}\n\n{msg}\n---------------------------------\n')
        return tb, msg
    else:
        logging.warning(f'{now}\n{message}\n\n---------------------------------\n')
        return message
