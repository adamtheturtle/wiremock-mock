"""Tests for add_wiremock_to_respx."""

from http import HTTPStatus
from typing import Any

import httpx
import respx

from wiremock_mock import add_wiremock_to_respx

BASE_URL = "http://notion-mock.test"

_PAGE_ID = "59833787-2cf9-4fdf-8782-e53db20768a5"


def test_add_wiremock_to_respx_simple_get() -> None:
    """Add_wiremock_to_respx adds a simple GET stub."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/v1/pages"},
                "response": {
                    "status": 200,
                    "headers": {"Content-Type": "application/json"},
                    "jsonBody": {"object": "list", "results": []},
                },
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/pages")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"object": "list", "results": []}


def test_add_wiremock_to_respx_post() -> None:
    """Add_wiremock_to_respx adds a POST stub."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "POST", "urlPath": "/v1/pages"},
                "response": {
                    "status": 200,
                    "jsonBody": {"object": "page", "id": "abc-123"},
                },
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(url=f"{BASE_URL}/v1/pages", json={"parent": {}})
        assert response.status_code == HTTPStatus.OK
        assert response.json()["id"] == "abc-123"


def test_add_wiremock_to_respx_patch() -> None:
    """Add_wiremock_to_respx adds a PATCH stub."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "PATCH",
                    "urlPath": f"/v1/pages/{_PAGE_ID}",
                },
                "response": {
                    "status": 200,
                    "jsonBody": {"object": "page", "id": _PAGE_ID},
                },
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.patch(
            url=f"{BASE_URL}/v1/pages/{_PAGE_ID}",
            json={"properties": {}},
        )
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_delete() -> None:
    """Add_wiremock_to_respx adds a DELETE stub."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "DELETE",
                    "urlPath": "/v1/blocks/block-123",
                },
                "response": {"status": 200},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.delete(url=f"{BASE_URL}/v1/blocks/block-123")
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_with_query_parameters() -> None:
    """Add_wiremock_to_respx matches query parameters with equalTo."""
    _block_id = "cccc0000-0000-0000-0000-000000000010"
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPath": "/v1/comments",
                    "queryParameters": {
                        "block_id": {"equalTo": _block_id},
                    },
                },
                "response": {
                    "status": 200,
                    "jsonBody": {"object": "list", "results": []},
                },
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(
            url=f"{BASE_URL}/v1/comments",
            params={"block_id": _block_id},
        )
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_url_path_pattern() -> None:
    """Add_wiremock_to_respx supports urlPathPattern regex."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPathPattern": r"/v1/pages/[0-9a-f-]+",
                },
                "response": {
                    "status": 200,
                    "jsonBody": {"object": "page"},
                },
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/pages/{_PAGE_ID}")
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_empty_mappings() -> None:
    """Add_wiremock_to_respx handles empty mappings without error."""
    stubs: dict[str, Any] = {"mappings": []}
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)


def test_add_wiremock_to_respx_mappings_not_list() -> None:
    """Add_wiremock_to_respx returns early when mappings is not a list."""
    stubs: dict[str, Any] = {"mappings": "not-a-list"}
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)


def test_add_wiremock_to_respx_url_path_pattern_only() -> None:
    """Add_wiremock_to_respx supports urlPathPattern without urlPath."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPathPattern": r"/v1/blocks/.+",
                },
                "response": {"status": 200, "jsonBody": {"object": "block"}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/blocks/abc-123")
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_body_response() -> None:
    """Add_wiremock_to_respx supports body (non-JSON) response."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/v1/raw"},
                "response": {"status": 200, "body": "plain text"},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/raw")
        assert response.status_code == HTTPStatus.OK
        assert response.text == "plain text"


def test_add_wiremock_to_respx_path_without_leading_slash() -> None:
    """Add_wiremock_to_respx adds leading slash when urlPath lacks it."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "v1/pages"},
                "response": {"status": 200, "jsonBody": {}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/pages")
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_skips_invalid_mapping() -> None:
    """Add_wiremock_to_respx skips mappings with invalid structure."""
    stubs: dict[str, Any] = {
        "mappings": [
            "not-a-dict",
            {"request": "invalid", "response": {"status": 200}},
            {
                "request": {"method": "GET", "urlPath": "/ok"},
                "response": "invalid",
            },
            {
                "request": {"method": 123, "urlPath": "/ok"},
                "response": {"status": 200},
            },
            {"request": {}, "response": {"status": 200}},
            {
                "request": {"method": "GET", "urlPath": "/valid"},
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/valid")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_query_param_without_equal_to() -> None:
    """Add_wiremock_to_respx ignores query params without equalTo."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPath": "/v1/comments",
                    "queryParameters": {"block_id": {"matches": ".*"}},
                },
                "response": {"status": 200, "jsonBody": {}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/comments")
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_query_param_non_dict_matcher() -> None:
    """Add_wiremock_to_respx skips query params with non-dict matcher
    values.
    """
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPath": "/v1/comments",
                    "queryParameters": {"block_id": "not-a-dict"},
                },
                "response": {"status": 200, "jsonBody": {}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/comments")
        assert response.status_code == HTTPStatus.OK


def test_add_wiremock_to_respx_url_path_with_extra_query_params() -> None:
    """UrlPath without queryParameters matches requests with query
    params.
    """
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPath": "/v1/blocks/test/children",
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(
            url=f"{BASE_URL}/v1/blocks/test/children",
            params={"page_size": 100},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_invalid_status_and_headers() -> None:
    """Add_wiremock_to_respx uses defaults for invalid status and
    headers.
    """
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/v1/edge"},
                "response": {
                    "status": "invalid",
                    "headers": "not-a-dict",
                    "jsonBody": {"ok": True},
                },
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/edge")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"ok": True}
