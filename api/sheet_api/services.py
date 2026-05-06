import logging
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from db import Event, EventOption, Ticket, User

from .schemas import (
    MainSheetRequest,
    OptionsSheetRequest,
    TextsSheetRequest,
    TicketSheetRequest,
)
from enums import book_status_inverted_dict

logger = logging.getLogger(__name__)


class SheetService:
    @staticmethod
    async def update_main(session: AsyncSession, payload: MainSheetRequest) -> bool:
        is_active, name, event_date, event_time = payload.data
        logger.warning(f'payload.data: {payload.data}')
        query = (
            sa.update(Event)
            .where(Event.gs_page == payload.page_id)
            .values(
                is_active=is_active,
                name=name,
                date_event=event_date,
                time_event=event_time,
                updated_at=datetime.now(),
            )
        )

        result = await session.execute(query)
        await session.commit()
        logger.warning(f'result.rowcount: {result.rowcount}')
        return result.rowcount > 0

    @staticmethod
    async def update_texts(session: AsyncSession, payload: TextsSheetRequest) -> bool:
        text = payload.data[0]

        query = (
            sa.update(Event)
            .where(Event.gs_page == payload.page_id)
            .values(
                text=text,
                updated_at=datetime.now(),
            )
        )

        result = await session.execute(query)
        await session.commit()

        return result.rowcount > 0

    @staticmethod
    async def update_options(session: AsyncSession, payload: OptionsSheetRequest) -> bool:
        event_id_query = sa.select(Event.id).where(Event.gs_page == payload.page_id).scalar_subquery()
        updated_count = 0
        updated_row_ids = [o.option_id for o in payload.data]

        # обнавление записей
        for option in payload.data:
            # >> name='Фри 5' place_count=50 option_id=2
            logger.warning(f'>> {option}')
            query = (
                sa.update(EventOption)
                .where(
                    EventOption.id == option.option_id,
                    # EventOption.event_id == event_id_query,
                )
                .values(
                    name=option.name,
                    empty_place=option.place_count,
                    updated_at=datetime.now(),
                )
            )

            result = await session.execute(query)
            updated_count += result.rowcount

        # удаляем нетронутые опции
        query = (
            sa.update(EventOption)
            .where(
                EventOption.id.not_in(updated_row_ids),
                EventOption.event_id == event_id_query,
            )
        )
        await session.execute(query)

        await session.commit()
        return True

    @staticmethod
    async def update_ticket(session: AsyncSession, payload: TicketSheetRequest) -> bool:
        ticket_data = payload.data

        ticket = await Ticket.get_by_id(session=session, entry_id=ticket_data.ticket_id)
        if not ticket:
            return False

        ticket.status = ticket_data.status
        ticket.phone = ticket_data.phone
        ticket.gs_row = payload.row
        ticket.updated_at = datetime.now()

        option = await EventOption.get_by_name_and_event_id(
            session=session,
            name=ticket_data.option_name,
            event_id=ticket.event_id,
        )

        if option:
            ticket.option = option
        # или ticket.option_id = option.id

        await session.commit()

        return True

        # ticket = await Ticket.get_by_id(entry_id=ticket_data.ticket_id)
        #
        # ticket_update = (
        #     sa.update(Ticket)
        #     .where(Ticket.id == ticket_data.ticket_id)
        #     .values(
        #         # status=ticket_data.status,
        #         status=book_status_inverted_dict.get(ticket_data.status),
        #         phone=ticket_data.phone,
        #         gs_row=payload.row,
        #         updated_at=datetime.now(),
        #     )
        # )
        #
        # option = await EventOption.get_by_name_and_event_id(
        #     session, name=ticket_data.option_name, event_id=ticket.event_id
        # )
        #
        # ticket_update.values(option=option)
        #
        # ticket_result = await session.execute(ticket_update)

        # тут будет номер телефона
        # user_update = (
        #     sa.update(User)
        #     .where(User.id == user_id)
        #     .values(
        #         full_name=ticket_data.full_name,
        #         username=ticket_data.username,
        #         last_visit=datetime.now(),
        #     )
        # )
        # await session.execute(user_update)
        # await session.commit()

        # return ticket_result.rowcount > 0
