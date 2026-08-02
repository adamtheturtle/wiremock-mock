"""Tests for add_wiremock_to_responses."""

from collections.abc import Iterator
from http import HTTPStatus
from typing import Any

import pytest
import requests
import responses

from wiremock_mock import add_wiremock_to_responses

BASE_URL = "http://notion-mock.test"


def test_add_wiremock_to_responses_returns_configured_response() -> None:
    """Status, JSON, and single or repeated headers are returned."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/v1/pages"},
                "response": {
                    "status": 201,
                    "statusMessage": "Backend does not support this",
                    "headers": {
                        "X-Single": "one",
                        "Set-Cookie": ["first=1", "second=2"],
                    },
                    "jsonBody": {"object": "list", "results": []},
                },
            },
        ],
    }

    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        response = requests.get(url=f"{BASE_URL}/v1/pages", timeout=1)

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {"object": "list", "results": []}
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["X-Single"] == "one"
    assert response.raw.headers.getlist(key="Set-Cookie") == [
        "first=1",
        "second=2",
    ]


@pytest.mark.parametrize(
    argnames=("response_spec", "expected"),
    argvalues=[
        ({"body": "plain text"}, b"plain text"),
        ({"body": b"binary\x00data"}, b"binary\x00data"),
        ({"body": 42}, b"42"),
        ({"base64Body": "YmluYXJ5AGRhdGE="}, b"binary\x00data"),
        ({}, b""),
    ],
)
def test_add_wiremock_to_responses_response_bodies(
    response_spec: dict[str, object], expected: bytes
) -> None:
    """WireMock response body variants are supported."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/body"},
                "response": {"status": 200, **response_spec},
            },
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        response = requests.get(url=f"{BASE_URL}/body", timeout=1)

    assert response.content == expected


@pytest.mark.parametrize(
    argnames="method", argvalues=["POST", "PATCH", "DELETE"]
)
def test_add_wiremock_to_responses_matches_methods(method: str) -> None:
    """HTTP methods are registered with responses."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": method, "urlPath": "/method"},
                "response": {"status": 204},
            },
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        response = requests.request(
            method=method,
            url=f"{BASE_URL}/method",
            timeout=1,
        )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_add_wiremock_to_responses_matches_path_and_query() -> None:
    """Path regexes and equalTo query parameters are supported."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPathPattern": r"/v1/pages/[0-9]+",
                    "queryParameters": {"view": {"equalTo": "summary"}},
                },
                "response": {"status": 200, "body": "matched"},
            },
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        response = requests.get(
            url=f"{BASE_URL}/v1/pages/123",
            params={"view": "summary", "extra": "allowed"},
            timeout=1,
        )

    assert response.text == "matched"


def test_add_wiremock_to_responses_distinguishes_json_bodies() -> None:
    """Two mappings at one URL can differ by their JSON bodies."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/items",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"items": [1, 2]},
                            "ignoreArrayOrder": True,
                            "ignoreExtraElements": True,
                        },
                    ],
                },
                "response": {"jsonBody": {"kind": "numbers"}},
            },
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/items",
                    "bodyPatterns": [
                        {"equalToJson": {"items": ["a", "b"]}},
                    ],
                },
                "response": {"jsonBody": {"kind": "letters"}},
            },
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        number_response = requests.post(
            url=f"{BASE_URL}/items",
            json={"items": [2, 1], "ignored": True},
            timeout=1,
        )
        letter_response = requests.post(
            url=f"{BASE_URL}/items",
            json={"items": ["a", "b"]},
            timeout=1,
        )

    assert number_response.json() == {"kind": "numbers"}
    assert letter_response.json() == {"kind": "letters"}


@pytest.mark.parametrize(
    argnames=("body_patterns", "body"),
    argvalues=[
        ([{"equalTo": "exact body"}], "exact body"),
        ([{"contains": "alpha"}, {"contains": "omega"}], b"alpha omega"),
        ([{"equalTo": ""}], None),
    ],
)
def test_add_wiremock_to_responses_matches_raw_bodies(
    body_patterns: list[dict[str, object]], body: str | bytes | None
) -> None:
    """String and byte request bodies can use raw body matchers."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/raw",
                    "bodyPatterns": body_patterns,
                },
                "response": {"body": "matched"},
            },
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        response = requests.post(
            url=f"{BASE_URL}/raw",
            data=body,
            timeout=1,
        )

    assert response.text == "matched"


@pytest.mark.parametrize(
    argnames="body", argvalues=[b"\xff\xfe", iter([b"needle"])]
)
def test_add_wiremock_to_responses_rejects_unmatchable_bodies(
    body: bytes | Iterator[bytes],
) -> None:
    """Non-text and streamed bodies do not satisfy text matchers."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/raw",
                    "bodyPatterns": [{"contains": "needle"}],
                },
                "response": {"status": 200},
            },
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=False
    ) as mock_obj:
        add_wiremock_to_responses(
            mock_obj=mock_obj,
            stubs=stubs,
            base_url=BASE_URL,
        )
        with pytest.raises(expected_exception=requests.ConnectionError):
            requests.post(
                url=f"{BASE_URL}/raw",
                data=body,
                timeout=1,
            )
