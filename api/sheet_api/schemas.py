from datetime import date, datetime, time
import typing as t

from pydantic import BaseModel, ConfigDict, Field, field_validator
from enums import book_status_inverted_dict


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


class TextsSheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: tuple[str | None]

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: t.Any) -> tuple[str | None]:
        if not isinstance(value, list | tuple) or len(value) != 1:
            raise ValueError("data должен содержать 1 текстовое значение")

        text = value[0]
        if text is None or text == "":
            return (None,)

        if not isinstance(text, str):
            raise ValueError("текст должен быть строкой")

        return (text,)


class OptionData(BaseSchema):
    name: str
    place_count: int
    option_id: int

    @classmethod
    def from_row(cls, row: t.Any) -> t.Self | None:
        if not isinstance(row, list | tuple) or len(row) != 3:
            return None

        name, place_count, option_id = row

        if not isinstance(name, str) or not name.strip():
            return None

        place_count = cls._parse_int(place_count)
        option_id = cls._parse_int(option_id)
        if place_count is None or option_id is None:
            return None

        return cls(name=name.strip(), place_count=place_count, option_id=option_id)

    @staticmethod
    def _parse_int(value: t.Any) -> int | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())

        return None


class OptionsSheetRequest(BaseSchema):
    page_id: int
    sheet_name: str = Field(alias="sheetName")
    data: list[OptionData]

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: t.Any) -> list[OptionData]:
        if not isinstance(value, list):
            raise ValueError("data должен быть списком опций")

        options = []
        for row in value:
            option = OptionData.from_row(row)
            if option:
                options.append(option)

        if not options:
            raise ValueError("data не содержит валидных опций")

        return options


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

        status = book_status_inverted_dict.get(value[7])
        if not status:
            raise ValueError("Некорректный статус")

        return TicketData(
            ticket_id=value[0],
            place_count=value[1],
            option_name=value[2],
            full_name=value[3],
            username=value[4] or None,
            phone=value[5],
            link=value[6] or None,
            status=status,
        )


class SheetResponse(BaseSchema):
    status: str = "ok"
