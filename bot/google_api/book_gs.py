import asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from gspread.exceptions import APIError, WorksheetNotFound

from typing import Union

from .base import agcm
from settings import log_error
from enums import OptionData, Key, book_status_dict, BookStatus


# --- Обёртка для безопасного update ---
async def safe_update(worksheet, cell_range, values):
    max_retries = 10
    pause_sec = 2

    for attempt in range(max_retries):
        try:
            return await worksheet.update(cell_range, values)
        except APIError as e:
            if "Quota exceeded" in str(e):
                print(f"Превышена квота, попытка {attempt+1}/{max_retries}, жду {pause_sec} сек...")
                await asyncio.sleep(pause_sec)
            else:
                raise  # другие ошибки не глотаем
    raise Exception("Превышен лимит попыток записи в Google Sheets")


async def add_or_update_book_gs(
        spreadsheet_id: str,
        sheet_name: str,
        book_id: int,
        full_name: str,
        booking_time: str,
        count_place: int,
        comment: str,
        status: str,
        start_row: int = 2,
        max_attempts: int = 100,
        pause_on_quota_sec: int = 3,
        row_num: int = None
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.worksheet(sheet_name)

    if not comment:
        comment = '-'

    new_values = [[book_id, full_name, booking_time, count_place, comment, book_status_dict.get(status), "✅"]]

    # row = start_row
    row = row_num or start_row
    cell_range = f"B{row}:H{row}"

    if row_num:
        # cell_range = f"B{row_num}:H{row_num}"
        await safe_update(worksheet=worksheet, cell_range=cell_range, values=new_values)
        return row_num

    attempts = 0
    while attempts < max_attempts:
        cell_range = f"B{row}:H{row}"

        try:
            existing = await worksheet.get(cell_range)
            if not any(cell.strip() for cell in existing[0] if cell):
                # await worksheet.update(cell_range, new_values)
                await safe_update(worksheet=worksheet, cell_range=cell_range, values=new_values)
                return row
            row += 1
            attempts += 1
        except APIError as e:
            if "Quota exceeded" in str(e):
                print(f"[{row}] Превышена квота. Пауза {pause_on_quota_sec} сек...")
                await asyncio.sleep(pause_on_quota_sec)
            else:
                raise  # пробрасываем другие ошибки

        except Exception as e:
            log_error(e)

    raise Exception(f"Не удалось найти пустую строку за {max_attempts} попыток")


async def update_book_status_gs(
        spreadsheet_id: str,
        sheet_name: str,
        status: str,
        book_type: str,
        row: int,
) -> None:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    if str(sheet_name).isdigit():
        worksheet = await spreadsheet.get_worksheet_by_id(int(sheet_name))
    else:
        worksheet = await spreadsheet.worksheet(sheet_name)

    new_values = [[book_status_dict.get(status)]]

    attempts = 0
    cell_range = f"G{row}" if book_type == Key.QR_BOOK.value else f"I{row}"

    await safe_update(worksheet=worksheet, cell_range=cell_range, values=new_values)

    # while attempts < 30:
    #     cell_range = f"G{row}"
    #     try:
    #         await worksheet.update(cell_range, new_values)
    #         return row
    #
    #     except APIError as e:
    #         attempts += 1
    #         if "Quota exceeded" in str(e):
    #             pause_on_quota_sec = 3
    #             await asyncio.sleep(pause_on_quota_sec)
    #         else:
    #             raise  # пробрасываем другие ошибки
    #
    # raise Exception(f"Не удалось найти пустую строку за 30 попыток")


# --- Основная функция ---
async def create_event_sheet(
        spreadsheet_id: str,
        sheet_name: str,
        options: list[dict],
        page_id: int = None
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)

    if page_id:
        worksheet = await spreadsheet.get_worksheet_by_id(page_id)
    else:
        worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)

    # Заголовки опций
    # await safe_update(worksheet, "A1:D1", [["ID", "Название", "Места", "Стоимость"]])

    option_rows = [["ID", "Название", "Места", "Стоимость"]]
    for option in options:
        opt_obj = OptionData(**option)
        option_rows.append([opt_obj.id, opt_obj.name, opt_obj.place, opt_obj.price])

    await safe_update(worksheet, f"A1:D{len(option_rows)}", option_rows)

    # Таблица регистрации
    await safe_update(worksheet, "F1:K1", [["ID", "Опция", "Имя", "Статус", "В базе", "Ошибка"]])

    return worksheet.id


# --- Добавить билет в первую свободную строку таблицы регистрации ---
async def add_ticket_row_to_registration(
        spreadsheet_id: str,
        page_id: str,
        ticket_id: int,
        option_name: str,
        user_name: str,
        start_row: int = 2,
        ticket_row: int = None,
        status: str = BookStatus.CONFIRMED.value
) -> int:
    max_rows: int = 50
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.get_worksheet_by_id(page_id)

    # если запись существует просто её обновляем
    if ticket_row:
        cell_range = f"F{ticket_row}:J{ticket_row}"

        new_row = [[ticket_id, option_name, user_name, book_status_dict.get(status), "✅"]]
        await safe_update(worksheet, cell_range, new_row)
        return ticket_row

    for row in range(start_row, start_row + max_rows):
        cell_range = f"F{row}:J{row}"
        try:
            existing = await worksheet.get(cell_range)
        except APIError as e:
            if "Quota exceeded" in str(e):
                print(f"Quota hit on row {row}, sleeping...")
                await asyncio.sleep(2)
                continue
            else:
                raise

        # если все ячейки пусты
        if not any(cell.strip() for cell in existing[0] if cell):
            new_row = [[ticket_id, option_name, user_name, book_status_dict.get(status), "✅"]]
            await safe_update(worksheet, cell_range, new_row)
            return row

    raise Exception("Не удалось найти пустую строку в диапазоне регистрации")
