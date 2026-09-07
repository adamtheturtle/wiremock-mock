"""Tests for the native HTTPX2 transport."""

import asyncio
import base64
from http import HTTPStatus
from typing import Any

import httpx2
import pytest

from wiremock_mock import create_httpx2_transport

BASE_URL = "http://wiremock.test"


def _transport(*, stubs: dict[str, Any]) -> httpx2.MockTransport:
    """Create a transport for the test base URL."""
    return create_httpx2_transport(stubs=stubs, base_url=BASE_URL)


def test_sync_client_uses_native_httpx2_objects() -> None:
    """The synchronous path uses HTTPX2 requests and responses."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/greeting"},
                "response": {"status": 200, "body": "Hello, World!"},
            },
        ],
    }

    with httpx2.Client(transport=_transport(stubs=stubs)) as client:
        response = client.get(url=f"{BASE_URL}/greeting")

    assert isinstance(response, httpx2.Response)
    assert isinstance(response.request, httpx2.Request)
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello, World!"


def test_async_client_uses_transport() -> None:
    """The same transport supports the asynchronous HTTPX2 client."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/greeting"},
                "response": {"status": 200, "body": "Hello, async!"},
            },
        ],
    }

    async def request() -> httpx2.Response:
        """Make an asynchronous request through the transport."""
        async with httpx2.AsyncClient(
            transport=_transport(stubs=stubs)
        ) as client:
            return await client.get(url=f"{BASE_URL}/greeting")

    response = asyncio.run(main=request())

    assert isinstance(response, httpx2.Response)
    assert response.text == "Hello, async!"


def test_matches_url_query_body_and_builds_response_metadata() -> None:
    """The HTTPX2 backend supports shared request and response fields."""
    encoded_body = base64.b64encode(s=b"created").decode()
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPathPattern": "/items/[0-9]+",
                    "queryParameters": {"token": {"equalTo": "secret"}},
                    "bodyPatterns": [
                        {
                            "equalToJson": {"items": [1, 2]},
                            "ignoreArrayOrder": True,
                            "ignoreExtraElements": True,
                        },
                    ],
                },
                "response": {
                    "status": 201,
                    "statusMessage": "Created by WireMock",
                    "headers": {"X-Result": ["one", "two"]},
                    "base64Body": encoded_body,
                },
            },
        ],
    }

    with httpx2.Client(transport=_transport(stubs=stubs)) as client:
        response = client.post(
            url=f"{BASE_URL}/items/42?token=secret&extra=value",
            json={"items": [2, 1], "extra": True},
        )

    assert response.status_code == HTTPStatus.CREATED
    assert response.headers.get_list(key="X-Result") == ["one", "two"]
    assert response.content == b"created"
    assert response.extensions["reason_phrase"] == b"Created by WireMock"


@pytest.mark.parametrize(
    argnames=("method", "path", "content"),
    argvalues=[
        ("GET", "/items/42?token=secret", b'"expected"'),
        ("POST", "/other?token=secret", b'"expected"'),
        ("POST", "/items/42?token=secret", b'"different"'),
    ],
)
def test_unmatched_request_never_reaches_network(
    *, method: str, path: str, content: bytes
) -> None:
    """Method, URL, and body mismatches raise instead of using the network."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/items/42",
                    "queryParameters": {"token": {"equalTo": "secret"}},
                    "bodyPatterns": [{"equalTo": '"expected"'}],
                },
                "response": {"status": 200},
            },
        ],
    }

    with (
        httpx2.Client(transport=_transport(stubs=stubs)) as client,
        pytest.raises(
            expected_exception=httpx2.ConnectError,
            match="No WireMock mapping matched",
        ),
    ):
        client.request(method=method, url=f"{BASE_URL}{path}", content=content)


def test_empty_mappings_never_reach_network() -> None:
    """A transport without mappings rejects every request locally."""
    with (
        httpx2.Client(transport=_transport(stubs={})) as client,
        pytest.raises(
            expected_exception=httpx2.ConnectError,
            match="No WireMock mapping matched",
        ),
    ):
        client.get(url=f"{BASE_URL}/missing")
