import logging

from gspread_asyncio import AsyncioGspreadWorksheet
from aiogram.types import User

# import db
# from db import Event
from .base import GoogleSheetsClient
from enums import OptionData, BookStatus, book_status_dict


logger = logging.getLogger('google_api')


class TicketsGoogleClient(GoogleSheetsClient):

    event_info_range = 'B1:B4'
    close_msg_range = 'F1:K3'
    ticket_start_cell = 'D11'
    status_column = 'K'
    mark_ok_column = 'O'
    status_list_range = 'K11:k200'

    async def _update_event_info(
        self,
        worksheet: AsyncioGspreadWorksheet,
        event: 'Event',
        # event: Event,
    ):
        values = [
            [event.is_active],
            [event.name],
            [event.date_str()],
            [event.time_str()],
        ]

        await self._safe_update(worksheet=worksheet, cell_range=self.event_info_range, values=values)
        await self._safe_merge(worksheet=worksheet, cell_range=self.close_msg_range)

        close_msg = [[event.close_msg]] if event.close_msg else [['']]
        await self._safe_update(worksheet=worksheet, cell_range=self.close_msg_range, values=close_msg)

    async def _update_options(
        self,
        worksheet: AsyncioGspreadWorksheet,
        options: list[OptionData],
        start_row: int = 5
    ):
        values = []
        cancel_status = book_status_dict.get(BookStatus.CANCELED, '-')
        status_range = f'{self.status_column}:{self.status_column}'

        for option in options:
            row_num = start_row + len(values)
            # formula = f'={option.place}-SUMIFS(E:E; F:F; A{row_num})'
            # формула считает свободные места кроме статуса Отменён
            formula = f'={option.place}-SUMIFS(E:E; F:F; A{row_num}; {status_range}; "<>"&"{cancel_status}")'

            # formula = (
            #     f'=IFERROR('
            #     f'{option.place}-SUMIF(F:F, B{row_num}, E:E), '
            #     f'{option.place}'
            #     f')'
            # )

            values.append([option.name, formula, option.id])

        return await self._safe_update(
            worksheet=worksheet,
            cell_range=f"A{start_row}:C{start_row + 10}",
            values=values,
            raw=False
        )


    async def create_event_sheet(
            self,
            event: 'Event',
            spreadsheet_id: str,
            # sheet_name: str,
            options: list[OptionData],
            # page_id: int | None = None,
    ) -> int:
        spreadsheet = await self.open_spreadsheet(spreadsheet_id)
        # spreadsheet = await self.open_spreadsheet('1iSB7AK7erwnvURjWmUWSFLlDu-LpHE2b_99AXkU3d90')

        sheet_name = f'{event.date_str()[:-5]} {event.name}'[:100]

        # worksheet = await self.create_worksheet(
        #     spreadsheet=spreadsheet,
        #     worksheet_name=sheet_name,
        # )

        if event.gs_page:
            worksheet: AsyncioGspreadWorksheet = await spreadsheet.get_worksheet_by_id(event.gs_page)
        else:
            worksheet = await self.create_worksheet(
                spreadsheet=spreadsheet,
                worksheet_name=sheet_name,
            )

            if not worksheet:
                raise RuntimeError("Не удалось создать вкладку Google Sheets")

            # заполняем список
        await self._safe_add_dropdown(
            worksheet=worksheet, cell_range=self.status_list_range, values=book_status_dict.values()
        )

        # обновляем основные данные мероприятия
        await self._update_event_info(worksheet=worksheet, event=event)

        # обновляем опции
        await self._update_options(worksheet=worksheet, options=options)

        return worksheet.id


    async def add_or_update_ticket_row(
            self,
            spreadsheet_id: str,
            ticket: 'Ticket',
            page_id: str,
            option_name: str,
            user: 'User',
            ticket_row: int = None,
            status: BookStatus = BookStatus.NEW,
    ) -> int:

        logger.warning(f'add_ticket_row_to_registration')

        spreadsheet = await self.open_spreadsheet(spreadsheet_id)
        # spreadsheet = await self.open_spreadsheet('1iSB7AK7erwnvURjWmUWSFLlDu-LpHE2b_99AXkU3d90')

        worksheet = await spreadsheet.get_worksheet_by_id(page_id)
        user_link = f'https://t.me/{user.username}' if user.username else '-'
        # ID, Мест, Опции, Имя, Username, Телефон, Ссылка, Оплатил, Примечание, Откуда
        status_str = book_status_dict.get(status)
        row = [
            ticket.id,  1,  option_name, user.full_name, user.username, 'user.phone', user_link, status_str
        ]

        # если запись существует просто её обновляем
        if ticket_row:
            cell_range = f"F{ticket_row}:J{ticket_row}"
            new_row = [row]

            await self._safe_update(worksheet=worksheet, cell_range=cell_range, values=new_row)
            # return ticket_row

        else:
            response = await self._safe_add_row(worksheet=worksheet, row=row, cell_range=self.ticket_start_cell)
            # получает номер строки
            ticket_row = self._extract_updated_row(response)

        # ставим галочку, чтоб не летел повторный запрос на апи
        mark_ok_cell = f'{self.mark_ok_column}{ticket_row}'
        await self._safe_update(worksheet=worksheet, cell_range=mark_ok_cell, values=[['✅']])

        return ticket_row

    async def update_book_status(
            self,
            spreadsheet_id: str,
            sheet_name: str,
            status: str,
            row: int,
    ) -> None:
        spreadsheet = await self.open_spreadsheet(spreadsheet_id)

        if str(sheet_name).isdigit():
            worksheet = await spreadsheet.get_worksheet_by_id(int(sheet_name))
        else:
            worksheet = await spreadsheet.worksheet(sheet_name)

        cell_range = f"{self.status_column}{row}"
        new_values = [[book_status_dict.get(status)]]

        await self._safe_update(worksheet=worksheet, cell_range=cell_range, values=new_values)
