from sqlalchemy.orm import Session

from app.models.work import Work
from app.repositories.work_repository import WorkRepository
from app.schemas.work import WorkCreate, WorkUpdate
from app.clients.openalex import OpenAlexClient

from app.exceptions import (
    OpenAlexNotFoundError,
    OpenAlexUnavailableError,
    WorkAlreadyExistsError,
)

class WorkService:

    def __init__(self):
        self.repository = WorkRepository()
        self.openalex_client = OpenAlexClient()

    def get_works(
        self,
        db: Session,
        publication_year: int | None,
        min_citations: int | None,
        sort_by: str,
        order: str,
        limit: int,
        offset: int,
    ) -> list[Work]:
        return self.repository.get_all(
            db=db,
            publication_year=publication_year,
            min_citations=min_citations,
            sort_by=sort_by,
            order=order,
            limit=limit,
            offset=offset,
        )

    def get_work(
        self,
        db: Session,
        work_id: int,
    ) -> Work:
        work = self.repository.get_by_id(
            db,
            work_id,
        )

        if work is None:
            raise ValueError("Work not found")

        return work

    def create_work(
        self,
        db: Session,
        data: WorkCreate,
    ) -> Work:

        existing = self.repository.get_by_openalex_id(
            db,
            data.openalex_id,
        )

        if existing is not None:
            raise WorkAlreadyExistsError(
                "Work with this OpenAlex ID already exists"
            )

        return self.repository.create(
            db,
            data,
        )

    def update_work(
        self,
        db: Session,
        work_id: int,
        data: WorkUpdate,
    ) -> Work:
        work = self.repository.get_by_id(db, work_id)

        if work is None:
            raise ValueError("Work not found")

        return self.repository.update(
            db,
            work,
            data,
        )
    
    def delete_work(
        self,
        db: Session,
        work_id: int,
    ) -> None:
        work = self.repository.get_by_id(db, work_id)

        if work is None:
            raise ValueError("Work not found")

        self.repository.delete(
            db,
            work,
        )

    def _openalex_to_work(self, data: dict) -> WorkCreate:
        doi = data.get("doi")

        if doi:
            doi = doi.removeprefix("https://doi.org/")

        return WorkCreate(
            openalex_id=data["id"].removeprefix("https://openalex.org/"),
            title=data["title"],
            publication_year=data.get("publication_year"),
            publication_date=data.get("publication_date"),
            cited_by_count=data.get("cited_by_count", 0),
            doi=doi,
        )


    def import_works_batch(
        self,
        db: Session,
        openalex_ids: list[str],
    ):
        imported = []
        errors = []

        # убираем одинаковые ID внутри одного запроса
        unique_ids = list(dict.fromkeys(openalex_ids))

        for openalex_id in unique_ids:
            try:
                work = self.import_work(
                    db,
                    openalex_id,
                )

                imported.append(work)

            except (
                WorkAlreadyExistsError,
                OpenAlexNotFoundError,
                OpenAlexUnavailableError,
            ) as error:
                errors.append({
                    "openalex_id": openalex_id,
                    "error": str(error),
                })

        return {
            "imported": imported,
            "errors": errors,
        }


    def import_work(
        self,
        db: Session,
        openalex_id: str,
    ):
        existing = self.repository.get_by_openalex_id(
            db,
            openalex_id,
        )

        if existing:
            raise WorkAlreadyExistsError(
            "Work with this OpenAlex ID already exists"
            )

        data = self.openalex_client.get_work(openalex_id)

        work_data = self._openalex_to_work(data)

        return self.repository.create(
            db,
            work_data,
        )


    def fetch_work(
        self,
        openalex_id: str,
    ) -> WorkCreate:
        data = self.openalex_client.get_work(
            openalex_id
        )

        return self._openalex_to_work(data)


    def get_existing_openalex_ids(
        self,
        db: Session,
        openalex_ids: list[str],
    ) -> set[str]:
        return self.repository.get_existing_openalex_ids(
            db,
            openalex_ids,
        )


    def save_many(
        self,
        db: Session,
        works_data: list[WorkCreate],
    ) -> None:
        self.repository.create_many(
            db,
            works_data,
        )

    
    def save_one(
        self,
        db: Session,
        work_data: WorkCreate,
    ):
        return self.repository.create(
            db,
            work_data,
        )