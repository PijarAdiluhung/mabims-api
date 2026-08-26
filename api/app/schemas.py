from __future__ import annotations

from pydantic import BaseModel, Field


class ConversionInput(BaseModel):
    date: str
    calendar: str
    tz: str | None = None


class ConversionOutput(BaseModel):
    date: str
    calendar: str


class ConvertResponse(BaseModel):
    input: ConversionInput
    output: ConversionOutput
    source: str
    warnings: list[str] = Field(default_factory=list)


class RangeItem(BaseModel):
    gregorian: str
    hijri: str
    source: str


class EventItem(BaseModel):
    event: str
    name: str
    hijri: str
    gregorian: str
    source: str


class EventsResponse(BaseModel):
    input: dict
    count: int
    events: list[EventItem]
    warnings: list[str] = Field(default_factory=list)


class RangeResponse(BaseModel):
    input: dict
    count: int
    items: list[RangeItem]
    warnings: list[str] = Field(default_factory=list)


class MonthResponse(RangeResponse):
    pass


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


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
