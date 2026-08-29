from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Source = Literal["mabims", "mabims-computed", "fallback:aladhan-ummalqura"]


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


class ConvertResponse(BaseModel):
    input: ConversionInput
    output: ConversionOutput
    source: Source = Field(description="Data origin: 'mabims' = curated from publicly available Kemenag tables, 'mabims-computed' = Neo MABIMS algorithmic estimates")
    warnings: list[str] = Field(default_factory=list, description="Non-empty when borderline months or computed fallback applies")


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
    fallback_active: bool
    fallback_months: list[str] = Field(default_factory=list)
    computed_active: bool = False
    computed_months: list[str] = Field(default_factory=list)
    method: str | None = None
    docs_url: str


class HealthResponse(BaseModel):
    status: str
    version: str


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


class HilalEvening(BaseModel):
    hijri_date: str
    hijri_day: int
    gregorian_date: str
    sunset: str
    moonset: str
    moon_alt_deg: float
    moon_az_deg: float
    sun_alt_deg: float
    elongation_deg: float
    illumination_pct: float
    age_hours: float
    alt_ok: bool = Field(description="Moon altitude >= 3.0 degrees at Sabang sunset")
    elong_ok: bool = Field(description="Elongation >= 6.4 degrees at Sabang sunset")
    visible: bool = Field(description="True when both alt_ok and elong_ok are true — criteria fulfilled, not a claim of actual observation")


class HilalInput(BaseModel):
    month: int
    year: int


class HilalInfoResponse(BaseModel):
    input: HilalInput
    month: HilalMonth
    previous_month: HilalPrevMonth
    evening: HilalEvening
    source: Source = Field(description="Data origin: 'mabims' = curated from publicly available Kemenag tables, 'mabims-computed' = Neo MABIMS algorithmic estimates")
    warnings: list[str] = Field(default_factory=list, description="Non-empty when borderline months or computed fallback applies")


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
