import httpx

from app.exceptions import (
    OpenAlexNotFoundError,
    OpenAlexUnavailableError,
)


class OpenAlexClient:
    BASE_URL = "https://api.openalex.org"

    def get_work(self, openalex_id: str) -> dict:
        try:
            response = httpx.get(
                f"{self.BASE_URL}/works/{openalex_id}",
                timeout=10.0,
            )

        except httpx.TimeoutException:
            raise OpenAlexUnavailableError(
                "OpenAlex request timed out"
            )

        except httpx.RequestError as error:
            print(type(error).__name__)
            print(repr(error))

            raise OpenAlexUnavailableError(
                f"Could not connect to OpenAlex: {error}"
            )

        if response.status_code == 404:
            raise OpenAlexNotFoundError(
                "Work not found in OpenAlex"
            )

        if response.status_code >= 500:
            raise OpenAlexUnavailableError(
                "OpenAlex service is unavailable"
            )

        response.raise_for_status()

        return response.json()