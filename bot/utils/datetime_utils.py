from datetime import datetime, timedelta, time

import typing as t

from settings import conf


# список на следующие
def hand_time_format(time_str: str) -> t.Optional[str]:
    try:
        time_split = time_str.split(':')
        if len(time_split) == 1 and time_split[0].isdigit() and int(time_split[0]) < 24:
            time_str = f'{time_str}:00'

        check = datetime.strptime(time_str, conf.time_format)
        return time_str

    except:
        return None

