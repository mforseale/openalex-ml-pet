from app.repositories.work_repository import WorkRepository
from app.schemas.work import (
    WorkCreate,
    WorkUpdate,
)


def create_test_work(repository, db_session):
    data = WorkCreate(
        openalex_id="W_TEST_1",
        title="Test Article",
        publication_year=2026,
        cited_by_count=10,
    )

    return repository.create(
        db_session,
        data,
    )


def test_create_work(db_session):

    repository = WorkRepository()

    work = create_test_work(
        repository,
        db_session,
    )

    assert work.id is not None
    assert work.openalex_id == "W_TEST_1"



def test_get_work_by_id(db_session):

    repository = WorkRepository()

    work = create_test_work(
        repository,
        db_session,
    )

    result = repository.get_by_id(
        db_session,
        work.id,
    )

    assert result is not None
    assert result.title == "Test Article"



def test_get_works(db_session):

    repository = WorkRepository()

    create_test_work(
        repository,
        db_session,
    )

    works = repository.get_all(
        db_session,
        publication_year=None,
        min_citations=None,
        sort_by="id",
        order="desc",
        limit=100,
        offset=0,
    )

    assert len(works) == 1


def test_update_work(db_session):

    repository = WorkRepository()

    work = create_test_work(
        repository,
        db_session,
    )

    update_data = WorkUpdate(
        title="Updated title"
    )

    updated = repository.update(
        db_session,
        work,
        update_data,
    )

    assert updated.title == "Updated title"

def test_delete_work(db_session):

    repository = WorkRepository()

    work = create_test_work(
        repository,
        db_session,
    )

    repository.delete(
        db_session,
        work,
    )

    result = repository.get_by_id(
        db_session,
        work.id,
    )

    assert result is None