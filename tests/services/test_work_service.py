from app.services.work_service import WorkService
from app.schemas.work import WorkCreate
import pytest

from app.exceptions import WorkAlreadyExistsError

def test_create_work_success(db_session):

    service = WorkService()

    data = WorkCreate(
        openalex_id="W_SERVICE_TEST",
        title="Service Test Article",
        publication_year=2026,
        cited_by_count=100,
    )

    work = service.create_work(
        db_session,
        data,
    )

    assert work.id is not None
    assert work.openalex_id == "W_SERVICE_TEST"
    assert work.title == "Service Test Article"

def test_create_work_duplicate(db_session):

    service = WorkService()

    data = WorkCreate(
        openalex_id="W_DUPLICATE",
        title="Duplicate Article",
        publication_year=2026,
        cited_by_count=50,
    )

    service.create_work(
        db_session,
        data,
    )


    with pytest.raises(WorkAlreadyExistsError):
        service.create_work(
            db_session,
            data,
        )

def test_get_work_success(db_session):

    service = WorkService()

    data = WorkCreate(
        openalex_id="W_GET_TEST",
        title="Get Test",
        publication_year=2025,
        cited_by_count=20,
    )

    created = service.create_work(
        db_session,
        data,
    )


    result = service.get_work(
        db_session,
        created.id,
    )


    assert result.id == created.id
    assert result.title == "Get Test"


def test_get_work_not_found(db_session):

    service = WorkService()

    with pytest.raises(ValueError):
        service.get_work(
            db_session,
            999999,
        )


