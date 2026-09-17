import json
import time
from sqlalchemy.exc import DataError, IntegrityError
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from app.database import SessionLocal
from app.exceptions import (
    OpenAlexNotFoundError,
    OpenAlexUnavailableError,
)
from app.services.work_service import WorkService


INPUT_FILE = "etl/openalex_ids.txt"
CHECKPOINT_FILE = "etl/processed_ids.txt"
ERROR_FILE = "etl/errors.jsonl"

MAX_WORKERS = 5

CHUNK_SIZE = 50
CHUNK_DELAY = 1

MAX_RETRIES = 3
RETRY_DELAY = 2


def load_processed_ids(path: str) -> set[str]:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return {
                line.strip()
                for line in file
                if line.strip()
            }

    except FileNotFoundError:
        return set()


def mark_processed(
    path: str,
    openalex_id: str,
):
    with open(path, "a", encoding="utf-8") as file:
        file.write(openalex_id + "\n")


def log_error(
    openalex_id: str,
    error: str,
    error_type: str,
):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "openalex_id": openalex_id,
        "error_type": error_type,
        "error": error,
    }

    with open(ERROR_FILE, "a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def load_ids(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as file:
        return [
            line.strip()
            for line in file
            if line.strip()
        ]


def chunked(
    items: list[str],
    size: int,
):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def fetch_with_retry(
    service: WorkService,
    openalex_id: str,
):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            work_data = service.fetch_work(
                openalex_id
            )

            return work_data, None, None

        except OpenAlexNotFoundError as error:
            return (
                None,
                str(error),
                "not_found",
            )

        except OpenAlexUnavailableError as error:
            if attempt == MAX_RETRIES:
                return (
                    None,
                    str(error),
                    "temporary",
                )

            print(
                f"[RETRY] {openalex_id} "
                f"attempt {attempt}/{MAX_RETRIES}"
            )

            time.sleep(RETRY_DELAY)


def process_work(openalex_id: str):
    """
    Worker.

    Работает только с OpenAlex.
    С PostgreSQL здесь больше не работаем.
    """

    service = WorkService()

    work_data, error, error_type = fetch_with_retry(
        service,
        openalex_id,
    )

    return (
        openalex_id,
        work_data,
        error,
        error_type,
    )


def save_with_fallback(
    db,
    service: WorkService,
    works_to_save: list,
):
    try:
        # Сначала пытаемся сохранить весь chunk одной транзакцией.
        service.save_many(
            db,
            [
                work_data
                for _, work_data in works_to_save
            ],
        )

        return works_to_save, []

    except (IntegrityError, DataError) as error:
        print(
            f"[BULK ERROR] "
            f"Chunk could not be saved: {error}"
        )

        # Bulk-транзакция сломалась.
        # Нужно обязательно вернуть Session
        # в рабочее состояние.
        db.rollback()

    # ---------------------------------
    # Fallback: сохраняем по одной
    # ---------------------------------

    saved = []
    failed = []

    for openalex_id, work_data in works_to_save:
        try:
            service.save_one(
                db,
                work_data,
            )

            saved.append(
                (openalex_id, work_data)
            )

        except (IntegrityError, DataError) as error:
            # Транзакция конкретной записи сломалась.
            db.rollback()

            failed.append(
                (
                    openalex_id,
                    str(error),
                )
            )

    return saved, failed

def main():
    openalex_ids = load_ids(INPUT_FILE)

    # Убираем дубликаты во входном файле
    openalex_ids = list(dict.fromkeys(openalex_ids))

    # Убираем уже обработанные ID
    processed_ids = load_processed_ids(CHECKPOINT_FILE)

    openalex_ids = [
        openalex_id
        for openalex_id in openalex_ids
        if openalex_id not in processed_ids
    ]

    total = len(openalex_ids)

    if total == 0:
        print(
            "Nothing to import. "
            "All IDs are already processed."
        )
        return

    imported = 0
    errors = 0
    processed = 0

    for chunk_number, chunk in enumerate(
        chunked(openalex_ids, CHUNK_SIZE),
        start=1,
    ):
        chunk_imported = 0
        chunk_errors = 0

        print(
            f"\n--- Chunk {chunk_number} "
            f"({len(chunk)} works) ---"
        )

        service = WorkService()

        # ==================================
        # 1. Короткая DB Session для SELECT
        # ==================================

        db = SessionLocal()

        try:
            existing_ids = (
                service.get_existing_openalex_ids(
                    db,
                    chunk,
                )
            )
        finally:
            db.close()

        # Здесь Session уже закрыта.
        # Пока ходим в OpenAlex, DB-транзакции нет.

        ids_to_fetch = []

        for openalex_id in chunk:
            if openalex_id in existing_ids:
                errors += 1
                chunk_errors += 1
                processed += 1

                error = (
                    "Work with this OpenAlex ID "
                    "already exists"
                )

                log_error(
                    openalex_id,
                    error,
                    "duplicate",
                )

                mark_processed(
                    CHECKPOINT_FILE,
                    openalex_id,
                )

                print(
                    f"[ERROR] "
                    f"{processed}/{total} "
                    f"{openalex_id} — {error}"
                )

            else:
                ids_to_fetch.append(openalex_id)

        # ==================================
        # 2. Параллельные HTTP-запросы
        # ==================================

        works_to_save = []

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS,
        ) as executor:

            futures = {
                executor.submit(
                    process_work,
                    openalex_id,
                ): openalex_id
                for openalex_id in ids_to_fetch
            }

            for future in as_completed(futures):
                (
                    openalex_id,
                    work_data,
                    error,
                    error_type,
                ) = future.result()

                if work_data:
                    works_to_save.append(
                        (
                            openalex_id,
                            work_data,
                        )
                    )

                else:
                    errors += 1
                    chunk_errors += 1
                    processed += 1

                    log_error(
                        openalex_id,
                        error,
                        error_type,
                    )

                    print(
                        f"[ERROR] "
                        f"{processed}/{total} "
                        f"{openalex_id} — {error}"
                    )

                    # temporary попробуем ещё раз
                    # при следующем запуске.
                    if error_type != "temporary":
                        mark_processed(
                            CHECKPOINT_FILE,
                            openalex_id,
                        )

        # ==================================
        # 3. Новая короткая Session для INSERT
        # ==================================

        if works_to_save:
            db = SessionLocal()

            try:
                saved_works, failed_works = (
                    save_with_fallback(
                        db,
                        service,
                        works_to_save,
                    )
                )
            finally:
                db.close()

            for openalex_id, work_data in saved_works:
                imported += 1
                chunk_imported += 1
                processed += 1

                mark_processed(
                    CHECKPOINT_FILE,
                    openalex_id,
                )

                print(
                    f"[OK] "
                    f"{processed}/{total} "
                    f"{openalex_id} "
                    f"— {work_data.title}"
                )

            for openalex_id, error in failed_works:
                errors += 1
                chunk_errors += 1
                processed += 1

                log_error(
                    openalex_id,
                    error,
                    "database_error",
                )

                print(
                    f"[DB ERROR] "
                    f"{processed}/{total} "
                    f"{openalex_id} — {error}"
                )

        # ==================================
        # Chunk закончен
        # ==================================

        print(
            f"Chunk {chunk_number} finished: "
            f"imported={chunk_imported}, "
            f"errors={chunk_errors}"
        )

        print(
            f"Progress: "
            f"{processed}/{total} "
            f"({processed / total * 100:.1f}%)"
        )

        if processed < total:
            time.sleep(CHUNK_DELAY)

    # ==================================
    # Весь ETL закончен
    # ==================================

    print("\n=== Finished ===")
    print(f"Imported: {imported}")
    print(f"Errors: {errors}")
    print(f"Total: {total}")


if __name__ == "__main__":
    main()