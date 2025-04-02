import asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from gspread.exceptions import APIError
from typing import Union


from .base import agcm


async def add_book_gs(
    spreadsheet_id: str,
    sheet_name: str,
    full_name: str,
    booking_time: str,
    count_place: int,
    comment: str,
    attended: Union[bool, str],
    start_row: int = 2,
    max_attempts: int = 1000,
    pause_on_quota_sec: int = 3
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.worksheet(sheet_name)

    attended_str = "✅" if attended is True else ("◽️" if attended is False else str(attended))
    new_values = [[full_name, booking_time, count_place, comment, attended_str]]

    row = start_row
    attempts = 0

    while attempts < max_attempts:
        cell_range = f"C{row}:G{row}"
        try:
            existing = await worksheet.get(cell_range)
            if not any(cell.strip() for cell in existing[0] if cell):
                await worksheet.update(cell_range, new_values)
                return row
            row += 1
            attempts += 1
        except APIError as e:
            if "Quota exceeded" in str(e):
                print(f"[{row}] Превышена квота. Пауза {pause_on_quota_sec} сек...")
                await asyncio.sleep(pause_on_quota_sec)
            else:
                raise  # пробрасываем другие ошибки

    raise Exception(f"Не удалось найти пустую строку за {max_attempts} попыток")


async def update_book_gs(
    spreadsheet_id: str,
    sheet_name: str,
    full_name: str,
    booking_time: str,
    count_place: str,
    attended: Union[bool, str],
    row: int,
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.worksheet(sheet_name)

    attended_str = "✅" if attended is True else ("❌" if attended is False else str(attended))
    new_values = [[full_name, booking_time, count_place, attended_str]]

    attempts = 0

    while attempts < 30:
        cell_range = f"C{row}:F{row}"
        try:
            await worksheet.update(cell_range, new_values)
            return row

        except APIError as e:
            attempts += 1
            if "Quota exceeded" in str(e):
                pause_on_quota_sec = 3
                print(f"[{row}] Превышена квота. Пауза {pause_on_quota_sec} сек...")
                await asyncio.sleep(pause_on_quota_sec)
            else:
                raise  # пробрасываем другие ошибки

    raise Exception(f"Не удалось найти пустую строку за 30 попыток")


