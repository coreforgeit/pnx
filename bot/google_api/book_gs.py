import asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from gspread.exceptions import APIError, WorksheetNotFound

from typing import Union

from .base import agcm
from enums import OptionData, Key, book_status_dict


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
        max_attempts: int = 1000,
        pause_on_quota_sec: int = 3,
        row_num: int = None
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.worksheet(sheet_name)

    new_values = [[book_id, full_name, booking_time, count_place, comment, book_status_dict.get(status)]]

    row = start_row
    attempts = 0

    if row_num:
        cell_range = f"C{row_num}:G{row_num}"
        await worksheet.update(cell_range, new_values)
        return row_num

    while attempts < max_attempts:
        cell_range = f"B{row}:G{row}"
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
    status: str,
    row: int,
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.worksheet(sheet_name)

    new_values = [[book_status_dict.get(status)]]

    attempts = 0

    while attempts < 30:
        cell_range = f"G{row}"
        try:
            await worksheet.update(cell_range, new_values)
            return row

        except APIError as e:
            attempts += 1
            if "Quota exceeded" in str(e):
                pause_on_quota_sec = 3
                await asyncio.sleep(pause_on_quota_sec)
            else:
                raise  # пробрасываем другие ошибки

    raise Exception(f"Не удалось найти пустую строку за 30 попыток")


# --- Обёртка для безопасного update ---
async def safe_update(worksheet, cell_range, values):
    max_retries = 5
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


# --- Основная функция ---
async def create_event_sheet(
        spreadsheet_id: str,
        sheet_name: str,
        options: list[dict],
        page_id: int = None
) -> int:
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)

    # Удаляем старый лист (если есть)
    # try:
    #     existing = await spreadsheet.worksheet(sheet_name)
    #     # await spreadsheet.del_worksheet(existing)
    # except Exception:
    #     pass

    if page_id:
        worksheet = await spreadsheet.get_worksheet_by_id(page_id)
        # await worksheet.update_title(sheet_name)
    else:
        worksheet = await spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)

    # Заголовки опций
    await safe_update(worksheet, "A1:D1", [["ID", "Название", "Места", "Стоимость"]])

    option_rows = []
    for option in options:
        opt_obj = OptionData(**option)
        option_rows.append([opt_obj.id, opt_obj.name, opt_obj.place, opt_obj.price])
    await safe_update(worksheet, f"A2:D{len(option_rows)+1}", option_rows)

    # Таблица регистрации
    await safe_update(worksheet, "F1:J1", [["ID", "Опция", "Имя", "Пришёл", "В базе"]])
    # empty_rows = [[i+1, "", "", "⬜"] for i in range(20)]
    # await safe_update(worksheet, "F2:I21", empty_rows)

    return worksheet.id


# --- Добавить билет в первую свободную строку таблицы регистрации ---
async def add_ticket_row_to_registration(
    spreadsheet_id: str,
    page_id: str,
    ticket_id: int,
    option_name: str,
    user_name: str,
    start_row: int = 2,
) -> int:
    max_rows: int = 500
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)
    worksheet = await spreadsheet.get_worksheet_by_id(page_id)

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
            new_row = [[ticket_id, option_name, user_name, "⬜", "✅"]]
            await safe_update(worksheet, cell_range, new_row)
            return row

    raise Exception("Не удалось найти пустую строку в диапазоне регистрации")


# отмечает отменённым
async def mark_booking_cancelled(
        spreadsheet_id: str,
        row: int,
        book_type: str,
        page_id: int = None,
        page_name: str = None,
):
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(spreadsheet_id)

    # Если не указан диапазон — используем F:I в строке
    if book_type == Key.QR_BOOK.value:
        worksheet = await spreadsheet.worksheet(page_name)
        cancel_cell = f"F{row}"
        cancel_message = ["❌ Отменено"]

    else:
        worksheet = await spreadsheet.get_worksheet_by_id(page_id)
        cancel_cell = f"I{row}:J{row}"
        cancel_message = ["❌ Отменено", "❌ Отменено"]

    await safe_update(worksheet, cancel_cell, [cancel_message])

