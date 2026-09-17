from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .i18n import t

Source = Literal["mabims", "mabims-computed", "mabims-retro"]



class ConversionInput(BaseModel):
    date: str
    calendar: str
    tz: str | None = None


class ConversionOutput(BaseModel):
    date: str
    calendar: str
    day: int
    month: int
    month_name: str
    year: int


SOURCE_DESCRIPTION = t("schema.source")
WARNINGS_DESCRIPTION = t("schema.warnings")


class ConvertResponse(BaseModel):
    input: ConversionInput
    output: ConversionOutput
    source: Source = Field(description=SOURCE_DESCRIPTION)
    warnings: list[str] = Field(default_factory=list, description=WARNINGS_DESCRIPTION)


class NextDate(ConversionOutput):
    source: Source = Field(description=SOURCE_DESCRIPTION)


class TodayResponse(ConvertResponse):
    next: NextDate | None = Field(default=None, description=t("schema.today.next"))


class RangeItem(BaseModel):
    gregorian: str
    hijri: str
    source: Source


class RangeInput(BaseModel):
    start: str
    end: str
    calendar: str


class EventItem(BaseModel):
    event: str
    name: str
    hijri: str
    gregorian: str
    source: Source


class EventsInput(BaseModel):
    year: int
    calendar: str


class EventsResponse(BaseModel):
    input: EventsInput
    count: int
    events: list[EventItem]
    warnings: list[str] = Field(default_factory=list)


class RangeResponse(BaseModel):
    input: RangeInput
    count: int
    items: list[RangeItem]
    warnings: list[str] = Field(default_factory=list)


class MonthInput(BaseModel):
    year: int
    month: int
    calendar: str


class MonthResponse(BaseModel):
    input: MonthInput
    count: int
    items: list[RangeItem]
    warnings: list[str] = Field(default_factory=list)


class YearInput(BaseModel):
    year: int
    calendar: str


class YearResponse(BaseModel):
    input: YearInput
    count: int
    months: dict[int, list[RangeItem]]
    warnings: list[str] = Field(default_factory=list)


class Coverage(BaseModel):
    first: str
    last: str


class MetaResponse(BaseModel):
    version: str
    data_version: str
    coverage: Coverage
    computed_active: bool = False
    computed_months: list[str] = Field(default_factory=list)
    method: str | None = None
    docs_url: str
    hilal_image_range: list[int] | None = Field(
        default=None,
        description=t("schema.hilal_image_range"),
    )
    divergences: list[dict[str, Any]] = Field(
        default_factory=list,
        description=t("schema.divergences"),
    )
    table_version: str | None = Field(
        default=None,
        description=t("schema.table_version"),
    )


class HealthResponse(BaseModel):
    status: str
    version: str
    build_hash: str


class HilalMonth(BaseModel):
    name: str
    number: int
    year: int
    start: str


class HilalPrevMonth(BaseModel):
    name: str
    number: int
    year: int
    length: int


class DecidingSite(BaseModel):
    __doc__ = t("schema.deciding_site.model")

    name: str
    lat: float
    lon: float
    elev_m: float
    tz: str = Field(description=t("schema.deciding_site.tz"))


class HilalEvening(BaseModel):
    hijri_date: str
    hijri_day: int
    gregorian_date: str
    sunset: str
    moonset: str
    moon_alt_deg: float = Field(description=t("schema.hilal_evening.moon_alt_deg"))
    moon_az_deg: float = Field(description=t("schema.hilal_evening.moon_az_deg"))
    sun_alt_deg: float = Field(description=t("schema.hilal_evening.sun_alt_deg"))
    elongation_deg: float = Field(description=t("schema.hilal_evening.elongation_deg"))
    illumination_pct: float
    age_hours: float
    deciding_site: DecidingSite = Field(
        description=t("schema.hilal_evening.deciding_site"),
    )
    sites_checked: int = Field(
        default=0, description=t("schema.hilal_evening.sites_checked")
    )
    alt_ok: bool = Field(description=t("schema.hilal_evening.alt_ok"))
    elong_ok: bool = Field(description=t("schema.hilal_evening.elong_ok"))
    visible: bool = Field(description=t("schema.hilal_evening.visible"))


class HilalInput(BaseModel):
    month: int
    year: int


class HilalInfoResponse(BaseModel):
    input: HilalInput
    month: HilalMonth
    previous_month: HilalPrevMonth
    evening: HilalEvening
    source: Source = Field(description=SOURCE_DESCRIPTION)
    warnings: list[str] = Field(default_factory=list, description=WARNINGS_DESCRIPTION)


class HilalHistoryInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str | None = Field(default=None, alias="from", description=t("schema.hilal_history.from"))
    to_: str | None = Field(default=None, alias="to", description=t("schema.hilal_history.to"))


class HilalHistoryItem(BaseModel):
    month: HilalMonth
    previous_month: HilalPrevMonth
    evening: HilalEvening
    source: Source = Field(description=SOURCE_DESCRIPTION)
    warnings: list[str] = Field(default_factory=list, description=WARNINGS_DESCRIPTION)


class HilalHistoryResponse(BaseModel):
    input: HilalHistoryInput
    count: int
    range: Coverage | None = Field(
        default=None, description=t("schema.hilal_history.range")
    )
    months: list[HilalHistoryItem]
    warnings: list[str] = Field(default_factory=list)


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class TableResponse(BaseModel):
    version: str
    gregorian_to_hijri: dict[str, str]
    hijri_to_gregorian: dict[str, str]
