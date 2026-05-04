from fastapi import APIRouter

from .schemas import (
    MainSheetRequest,
    OptionsSheetRequest,
    SheetResponse,
    TextsSheetRequest,
    TicketSheetRequest,
)


router = APIRouter(
    prefix="",
    tags=["sheet-api"],
)


@router.post("/main/", response_model=SheetResponse)
async def update_main(payload: MainSheetRequest) -> SheetResponse:
    return SheetResponse()


@router.post("/options/", response_model=SheetResponse)
async def update_options(payload: OptionsSheetRequest) -> SheetResponse:
    return SheetResponse()


@router.post("/texts/", response_model=SheetResponse)
async def update_texts(payload: TextsSheetRequest) -> SheetResponse:
    return SheetResponse()


@router.post("/ticket/", response_model=SheetResponse)
async def update_ticket(payload: TicketSheetRequest) -> SheetResponse:
    return SheetResponse()
