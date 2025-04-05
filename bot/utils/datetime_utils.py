from datetime import datetime, timedelta, time

import typing as t

from settings import conf

from datetime import datetime, date
import re


# Приводит цифровую дату к формату 'дд.мм.гггг' с проверкой и добавлением года
def hand_date_format(date_str: str) -> str:
    date_str = date_str.strip()
    today = date.today()

    # Возможные цифровые разделители
    separators = [r"\.", "/", "-", " "]

    for sep in separators:
        # регулярка: ищем 2-3 числовых блока, разделённых текущим разделителем
        pattern = fr"^(\d{{1,2}}){sep}(\d{{1,2}})({sep}(\d{{2,4}}))?$"
        match = re.match(pattern, date_str)

        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            raw_year = match.group(4)

            if raw_year is None:
                year = today.year  # если года нет, подставляем текущий
            elif len(raw_year) == 2:
                year = int("20" + raw_year)  # 2 цифры → 20XX
            else:
                year = int(raw_year)

            try:
                norm_data_str = f'{day:02}.{month:02}.{year}'
                normalized = datetime.strptime(norm_data_str, conf.date_format).date()
                return norm_data_str
            except:
                pass



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

