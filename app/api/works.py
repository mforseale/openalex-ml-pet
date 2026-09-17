from typing import Literal

from app.exceptions import WorkAlreadyExistsError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.work import (
    WorkBatchImport,
    WorkBatchImportResponse,
    WorkCreate,
    WorkResponse,
    WorkUpdate,
)
from app.services.work_service import WorkService


router = APIRouter(
    prefix="/works",
    tags=["works"],
)

service = WorkService()


@router.get(
    "",
    response_model=list[WorkResponse],
)

def get_works(
    publication_year: int | None = Query(None, ge=1800, le=2100),
    min_citations: int | None = Query(None, ge=0),

    sort_by: Literal[
        "id",
        "publication_year",
        "cited_by_count",
        "created_at",
    ] = "id",

    order: Literal["asc", "desc"] = "asc",

    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),

    db: Session = Depends(get_db),
):
    return service.get_works(
        db=db,
        publication_year=publication_year,
        min_citations=min_citations,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{work_id}",
    response_model=WorkResponse,
)
def get_work(
    work_id: int,
    db: Session = Depends(get_db),
):
    try:
        return service.get_work(
            db,
            work_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.post(
    "",
    response_model=WorkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_work(
    data: WorkCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.create_work(
            db,
            data,
        )

    except WorkAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.patch(
    "/{work_id}",
    response_model=WorkResponse,
)
def update_work(
    work_id: int,
    data: WorkUpdate,
    db: Session = Depends(get_db),
):
    try:
        return service.update_work(
            db,
            work_id,
            data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.delete(
    "/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_work(
    work_id: int,
    db: Session = Depends(get_db),
):
    try:
        service.delete_work(
            db,
            work_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.post(
    "/import/batch",
    response_model=WorkBatchImportResponse,
)
def import_works_batch(
    data: WorkBatchImport,
    db: Session = Depends(get_db),
):
    return service.import_works_batch(
        db,
        data.openalex_ids,
    )


@router.post(
    "/import/{openalex_id}",
    response_model=WorkResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_work(
    openalex_id: str,
    db: Session = Depends(get_db),
):
    try:
        return service.import_work(
            db,
            openalex_id,
        )

    except WorkAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )