"""Tests for supported usage patterns."""

from http import HTTPStatus
from typing import Any

import httpx
import respx

from wiremock_mock import add_wiremock_to_respx

_BASE_URL = "http://wiremock.test"
_STUBS: dict[str, Any] = {
    "mappings": [
        {
            "request": {"method": "GET", "urlPath": "/greeting"},
            "response": {"status": 200, "body": "Hello, World!"},
        },
    ],
}


def test_respx_context_manager() -> None:
    """WireMock stubs can be added to a respx context manager."""
    with respx.mock(
        base_url=_BASE_URL,
        assert_all_called=False,
    ) as respx_mock:
        add_wiremock_to_respx(
            mock_obj=respx_mock,
            stubs=_STUBS,
            base_url=_BASE_URL,
        )

        response = httpx.get(url=f"{_BASE_URL}/greeting")

    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello, World!"


@respx.mock(base_url=_BASE_URL, assert_all_called=False)
def test_respx_decorator(respx_mock: respx.MockRouter) -> None:
    """WireMock stubs can be added to a respx decorator's injected
    mock.
    """
    add_wiremock_to_respx(
        mock_obj=respx_mock,
        stubs=_STUBS,
        base_url=_BASE_URL,
    )

    response = httpx.get(url=f"{_BASE_URL}/greeting")

    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello, World!"
