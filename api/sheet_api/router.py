import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_session
from .schemas import (
    MainSheetRequest,
    OptionsSheetRequest,
    SheetResponse,
    TextsSheetRequest,
    TicketSheetRequest,
)
from .services import SheetService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["sheet-api"],
)

'''
{
  "page_id": 1019137990,
  "sheetName": "08.05 🔄 Обмен данными",
  "data": [
    true,
    "🔄 Обмен данными",
    "08.05.2026",
    "20:00"
  ]

'''

@router.post("/main/", response_model=SheetResponse)
async def update_main(
        request: Request,
        payload: MainSheetRequest,
        session: AsyncSession = Depends(get_session),
) -> SheetResponse:
    # logger.warning(f"path: {request.url.path}")
    # logger.warning(f"full url: {request.url}")
    # logger.warning(f'payload: {payload}')
    updated = await SheetService.update_main(session=session, payload=payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    return SheetResponse()


@router.post("/options/", response_model=SheetResponse)
async def update_options(
        payload: OptionsSheetRequest,
        session: AsyncSession = Depends(get_session),
) -> SheetResponse:
    logger.warning(f'payload: {payload}')

    updated = await SheetService.update_options(session=session, payload=payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Опции мероприятия не найдены")

    return SheetResponse()


@router.post("/texts/", response_model=SheetResponse)
async def update_texts(
        payload: TextsSheetRequest,
        session: AsyncSession = Depends(get_session),
) -> SheetResponse:
    updated = await SheetService.update_texts(session=session, payload=payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    return SheetResponse()


@router.post("/ticket/", response_model=SheetResponse)
async def update_ticket(
        payload: TicketSheetRequest,
        session: AsyncSession = Depends(get_session),
) -> SheetResponse:
    updated = await SheetService.update_ticket(session=session, payload=payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Билет не найден")

    return SheetResponse()
