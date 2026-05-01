import logging
import asyncio
import gspread_asyncio
import typing as t
import re

from gspread_asyncio import AsyncioGspreadWorksheet, AsyncioGspreadSpreadsheet
from google.oauth2.service_account import Credentials
from gspread.exceptions import GSpreadException, SpreadsheetNotFound, WorksheetNotFound, APIError
from gspread.utils import a1_range_to_grid_range


logger = logging.getLogger('google_api')


class GoogleSheetsClient:
    SCOPES: tuple[str, ...] = (
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    )

    def __init__(self, google_key_path: str):
        self.google_key_path = google_key_path
        self._manager = gspread_asyncio.AsyncioGspreadClientManager(
            self._get_creds
        )

    def _get_creds(self) -> Credentials:
        creds = Credentials.from_service_account_file(self.google_key_path)
        return creds.with_scopes(self.SCOPES)

    async def get_client(self):
        return await self._manager.authorize()

    async def open_spreadsheet(self, spreadsheet_id: str):
        client = await self.get_client()
        return await client.open_by_key(spreadsheet_id)

    async def get_worksheet(self, spreadsheet_id: str, worksheet_name: str):
        spreadsheet = await self.open_spreadsheet(spreadsheet_id)
        return await spreadsheet.worksheet(worksheet_name)

    async def create_worksheet(
            self,
            spreadsheet: AsyncioGspreadSpreadsheet,  # gspread_asyncio.AsyncioGspreadSpreadsheet
            worksheet_name: str,
            rows: int = 200,
            cols: int = 20,
            max_attempts: int = 20,
    ) -> AsyncioGspreadWorksheet | None:

        logger.info(f'create_worksheet: {rows} {cols}')
        for attempt in range(max_attempts):
            title = worksheet_name if attempt == 0 else f"{worksheet_name} ({attempt})"

            try:
                worksheet = await spreadsheet.add_worksheet(
                    title=title,
                    rows=rows,
                    cols=cols,
                )
                return worksheet

            except APIError as exc:
                message = str(exc)

                if "already exists" in message or "A sheet with the name" in message:
                    continue

                raise

        return None

    async def check_connection(
        self,
        spreadsheet_id: str,
        worksheet_name: str | None = None,
    ) -> bool:
        try:
            spreadsheet = await self.open_spreadsheet(spreadsheet_id)

            if worksheet_name:
                await spreadsheet.worksheet(worksheet_name)
            else:
                await spreadsheet.fetch_sheet_metadata()

            return True

        except SpreadsheetNotFound:
            logger.exception("Google spreadsheet not found: %s", spreadsheet_id)
            return False

        except WorksheetNotFound:
            logger.exception(
                "Google worksheet not found: spreadsheet_id=%s, worksheet_name=%s",
                spreadsheet_id,
                worksheet_name,
            )
            return False

        except GSpreadException:
            logger.exception("Google Sheets API error")
            return False

        except Exception:
            logger.exception("Unexpected Google Sheets connection error")
            return False

    async def _clear_range(
            self,
            worksheet: AsyncioGspreadWorksheet,
            cell_range: str,
    ):
        return await worksheet.batch_clear([cell_range])

    @staticmethod
    def _extract_updated_row(response: dict | None) -> int | None:
        if not response:
            return None

        updated_range = response.get("updates", {}).get("updatedRange")
        logger.warning(f'updated_range: {updated_range}')

        if not updated_range:
            return None

        # Google возвращает диапазон вида "'Sheet 1'!D12:H12"; берём номер первой строки.
        row_range = updated_range.split("!", 1)[-1]
        match = re.search(r"\$?[A-Z]+\$?(\d+)", row_range)
        return int(match.group(1)) if match else None

    async def _safe_update(
        self,
        worksheet: AsyncioGspreadWorksheet,
        cell_range: str,
        values: list[list],
        raw: bool = True,
        max_retries: int = 10,
        pause_sec: int = 2,
    ):
        for attempt in range(1, max_retries + 1):
            try:
                return await worksheet.update(range_name=cell_range, values=values, raw=raw)

            except APIError as exc:
                if "Quota exceeded" not in str(exc):
                    logger.exception("Google Sheets update error")
                    raise

                logger.warning(
                    "Превышена квота Google Sheets, попытка %s/%s, жду %s сек.",
                    attempt,
                    max_retries,
                    pause_sec,
                )

                if attempt == max_retries:
                    break

                await asyncio.sleep(pause_sec)

        raise RuntimeError("Превышен лимит попыток записи в Google Sheets")

    async def _safe_merge(
        self,
        worksheet: AsyncioGspreadWorksheet,
        cell_range: str,
        max_retries: int = 10,
        pause_sec: int = 2
    ):
        for attempt in range(max_retries):
            try:
                return await worksheet.merge_cells(cell_range)
            except APIError as e:
                if "Quota exceeded" in str(e):
                    print(f"Превышена квота, попытка {attempt + 1}/{max_retries}, жду {pause_sec} сек...")
                    await asyncio.sleep(pause_sec)
                else:
                    raise  # другие ошибки не глотаем
        raise Exception("Превышен лимит попыток записи в Google Sheets")

    async def _safe_add_dropdown(
        self,
        worksheet: AsyncioGspreadWorksheet,
        cell_range: str,
        values: list[str],
        input_message: str | None = None,
        strict: bool = True,
        show_custom_ui: bool = True,
        max_retries: int = 10,
        pause_sec: int = 2,
    ) -> dict | None:

        logger.warning(f'values: {values}')
        if not values:
            return None

        rule = {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [
                    {"userEnteredValue": str(value)}
                    for value in values
                ],
            },
            "strict": strict,
            "showCustomUi": show_custom_ui,
        }

        if input_message:
            rule["inputMessage"] = input_message

        body = {
            "requests": [
                {
                    "setDataValidation": {
                        "range": a1_range_to_grid_range(cell_range, sheet_id=worksheet.id),
                        "rule": rule,
                    }
                }
            ]
        }
        logger.warning(f'attempt')
        for attempt in range(1, max_retries + 1):
            try:
                return await worksheet.agcm._call(
                    worksheet.ws.client.batch_update,
                    worksheet.ws.spreadsheet_id,
                    body,
                )
            except APIError as e:
                if "Quota exceeded" in str(e):
                    print(f"Превышена квота, попытка {attempt}/{max_retries}, жду {pause_sec} сек...")
                    if attempt < max_retries:
                        await asyncio.sleep(pause_sec)
                else:
                    return None

        return None


    async def _safe_add_row(
        self,
        worksheet: AsyncioGspreadWorksheet,
        row: list,
        cell_range: str,
        max_retries: int = 10,
        pause_sec: int = 2
    ) -> dict | None:
        for attempt in range(1, max_retries + 1):
            try:
                return await worksheet.append_row(values=row, table_range=cell_range)

            except APIError as e:
                if "Quota exceeded" in str(e):
                    print(f"Превышена квота, попытка {attempt}/{max_retries}, жду {pause_sec} сек...")
                    if attempt < max_retries:
                        await asyncio.sleep(pause_sec)
                else:
                    return None

        return None
