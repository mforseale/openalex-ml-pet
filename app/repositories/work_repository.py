from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.work import Work
from app.schemas.work import WorkCreate, WorkUpdate


class WorkRepository:

    def get_all(
        self,
        db: Session,
        publication_year: int | None,
        min_citations: int | None,
        sort_by: str,
        order: str,
        limit: int,
        offset: int,
    ) -> list[Work]:

        query = db.query(Work)

        if publication_year is not None:
            query = query.filter(
                Work.publication_year == publication_year
            )

        if min_citations is not None:
            query = query.filter(
                Work.cited_by_count >= min_citations
            )

        sort_columns = {
            "id": Work.id,
            "publication_year": Work.publication_year,
            "cited_by_count": Work.cited_by_count,
            "created_at": Work.created_at,
        }

        sort_column = sort_columns[sort_by]

        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return (
            query
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_id(
        self,
        db: Session,
        work_id: int,
    ) -> Work | None:
        return db.get(Work, work_id)
        
    def get_by_openalex_id(
        self,
        db: Session,
        openalex_id: str,
    ) -> Work | None:

        stmt = select(Work).where(
            Work.openalex_id == openalex_id
        )

        return db.scalar(stmt)

    def create(
        self,
        db: Session,
        data: WorkCreate,
    ) -> Work:

        work = Work(
            **data.model_dump()
        )

        db.add(work)
        db.commit()
        db.refresh(work)

        return work

    def update(
        self,
        db: Session,
        work: Work,
        data: WorkUpdate,
    ) -> Work:
        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(work, field, value)

        db.commit()
        db.refresh(work)

        return work

    def delete(
        self,
        db: Session,
        work: Work,
    ) -> None:
        db.delete(work)
        db.commit()
    

    def create_many(
        self,
        db: Session,
        works_data: list[WorkCreate],
    ) -> None:
        works = [
            Work(**data.model_dump())
            for data in works_data
        ]

        db.add_all(works)
        db.commit()
    
    
    def get_existing_openalex_ids(
        self,
        db: Session,
        openalex_ids: list[str],
    ) -> set[str]:
        stmt = (
            select(Work.openalex_id)
            .where(Work.openalex_id.in_(openalex_ids))
        )

        return set(
            db.scalars(stmt).all()
        )