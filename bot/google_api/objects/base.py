import logging
import asyncio
import gspread_asyncio
import typing as t

from gspread_asyncio import AsyncioGspreadWorksheet, AsyncioGspreadSpreadsheet
from google.oauth2.service_account import Credentials
from gspread.exceptions import GSpreadException, SpreadsheetNotFound, WorksheetNotFound, APIError


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
