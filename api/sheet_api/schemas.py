from datetime import date, datetime, time
import typing as t

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MainSheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: tuple[bool, str, date, time]

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: t.Any) -> tuple[bool, str, date, time]:
        if not isinstance(value, list | tuple) or len(value) != 4:
            raise ValueError("data должен содержать 4 значения")

        is_active, name, event_date, event_time = value

        return (
            cls._parse_bool(is_active),
            str(name),
            cls._parse_date(event_date),
            cls._parse_time(event_time),
        )

    @staticmethod
    def _parse_bool(value: t.Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"true", "1", "yes", "y", "да"}:
                return True

            if normalized in {"false", "0", "no", "n", "нет"}:
                return False

        raise ValueError("первое значение data должно быть булевым")

    @staticmethod
    def _parse_date(value: t.Any) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        if isinstance(value, str):
            return datetime.strptime(value, "%d.%m.%Y").date()

        raise ValueError("третье значение data должно быть датой в формате ДД.ММ.ГГГГ")

    @staticmethod
    def _parse_time(value: t.Any) -> time:
        if isinstance(value, time):
            return value

        if isinstance(value, str):
            return datetime.strptime(value, "%H:%M").time()

        raise ValueError("четвёртое значение data должно быть временем в формате ЧЧ:ММ")


class SheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: t.Any


class TextsSheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: tuple[str]

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: t.Any) -> tuple[str]:
        if not isinstance(value, list | tuple) or len(value) != 1:
            raise ValueError("data должен содержать 1 текстовое значение")

        text = value[0]

        if not isinstance(text, str):
            raise ValueError("текст должен быть строкой")

        return (text,)


class OptionData(BaseSchema):
    name: str
    place_count: int
    option_id: int

    @classmethod
    def from_row(cls, row: t.Any) -> "OptionData":
        if not isinstance(row, list | tuple) or len(row) != 3:
            raise ValueError("каждая опция должна содержать название, количество мест и id")

        return cls(name=row[0], place_count=row[1], option_id=row[2])


class OptionsSheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: list[OptionData]

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: t.Any) -> list[OptionData]:
        if not isinstance(value, list):
            raise ValueError("data должен быть списком опций")

        return [OptionData.from_row(row) for row in value]


class TicketData(BaseSchema):
    ticket_id: int
    place_count: int
    option_name: str
    full_name: str
    username: str | None = None
    phone: str
    link: str | None = None
    status: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("телефон должен быть строкой")

        return value

    @property
    def phone_digits(self) -> str:
        return "".join(ch for ch in self.phone if ch.isdigit())


class TicketSheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: TicketData
    row: int

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: t.Any) -> TicketData:
        if not isinstance(value, list | tuple) or len(value) != 8:
            raise ValueError("data должен содержать 8 значений билета")

        return TicketData(
            ticket_id=value[0],
            place_count=value[1],
            option_name=value[2],
            full_name=value[3],
            username=value[4] or None,
            phone=value[5],
            link=value[6] or None,
            status=value[7],
        )


class SheetResponse(BaseSchema):
    status: str = "ok"
