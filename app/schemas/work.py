from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkCreate(BaseModel):
    openalex_id: str
    title: str
    publication_year: int | None = None
    publication_date: date | None = None
    cited_by_count: int = 0
    doi: str | None = None


class WorkResponse(WorkCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkUpdate(BaseModel):
    title: str | None = None
    publication_year: int | None = None
    publication_date: date | None = None
    cited_by_count: int | None = None
    doi: str | None = None


class WorkBatchImport(BaseModel):
    openalex_ids: list[str] = Field(
        min_length=1,
        max_length=100,
    )


class WorkImportError(BaseModel):
    openalex_id: str
    error: str


class WorkBatchImportResponse(BaseModel):
    imported: list[WorkResponse]
    errors: list[WorkImportError]