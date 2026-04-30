from gspread_asyncio import AsyncioGspreadWorksheet

# import db
# from db import Event
from .base import GoogleSheetsClient
from enums import OptionData


class TicketsGoogleClient(GoogleSheetsClient):

    event_info_range = 'B1:B4'
    close_msg_range = 'F1:K3'

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

        for option in options:
            row_num = start_row + len(values)
            formula = f'={option.place}-SUMIFS(E:E; F:F; A{row_num})'
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

    async def insert_ticket_row(
        self,
        worksheet: AsyncioGspreadWorksheet,
        row_values: list[str | int | float | bool | None],
    ):
        # TODO:
        # 1. Найти первую пустую строку в диапазоне D:J, начиная с 11 строки
        # 2. Собрать cell_range вида D{row}:J{row}
        # 3. Передать данные в _safe_update

        cell_range = "D11:J11"

        return await self._safe_update(
            worksheet=worksheet,
            cell_range=cell_range,
            values=[row_values],
        )

    async def create_event_sheet(
            self,
            event: 'Event',
            spreadsheet_id: str,
            # sheet_name: str,
            options: list[OptionData],
            # page_id: int | None = None,
    ) -> int:
        # spreadsheet = await self.open_spreadsheet(spreadsheet_id)
        spreadsheet = await self.open_spreadsheet('1iSB7AK7erwnvURjWmUWSFLlDu-LpHE2b_99AXkU3d90')

        sheet_name = f'{event.date_str()[:-5]} {event.name}'[:100]

        # TODO:
        worksheet = await self.create_worksheet(
            spreadsheet=spreadsheet,
            worksheet_name=sheet_name,
        )

        # if event.gs_page:
        #     worksheet: AsyncioGspreadWorksheet = await spreadsheet.get_worksheet_by_id(event.gs_page)
        # else:
        #     worksheet = await self.create_worksheet(
        #         spreadsheet=spreadsheet,
        #         worksheet_name=sheet_name,
        #         rows=100,
        #         cols=10,
        #     )
        #
        #     if worksheet is None:
        #         raise RuntimeError("Не удалось создать вкладку Google Sheets")

        # обновляем основные данные мероприятия
        await self._update_event_info(worksheet=worksheet, event=event)

        # обновляем опции
        await self._update_options(worksheet=worksheet, options=options)

        # option_rows = [["ID", "Название", "Места", "Стоимость"]]

        # for option in options:
        #     opt_obj = OptionData(**option)
        #     option_rows.append([
        #         opt_obj.id,
        #         opt_obj.name,
        #         opt_obj.place,
        #         opt_obj.price,
        #     ])
        #
        # await self._safe_update(
        #     worksheet=worksheet,
        #     cell_range=f"A1:D{len(option_rows)}",
        #     values=option_rows,
        # )
        #
        # await self._safe_update(
        #     worksheet=worksheet,
        #     cell_range="F1:K1",
        #     values=[["ID", "Опция", "Имя", "Статус", "В базе", "Ошибка"]],
        # )

        return worksheet.id