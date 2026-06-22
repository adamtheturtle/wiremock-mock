"""Tests for add_wiremock_to_respx."""

from http import HTTPStatus
from typing import Any

import httpx
import pytest
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


def test_add_wiremock_to_respx_body_bytes_response() -> None:
    """Add_wiremock_to_respx supports bytes body response."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/v1/bin"},
                "response": {"status": 200, "body": b"binary data"},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/bin")
        assert response.status_code == HTTPStatus.OK
        assert response.content == b"binary data"


def test_add_wiremock_to_respx_body_non_string_response() -> None:
    """Add_wiremock_to_respx converts non-str/bytes body via str()."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {"method": "GET", "urlPath": "/v1/num"},
                "response": {"status": 200, "body": 42},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/num")
        assert response.status_code == HTTPStatus.OK
        assert response.text == "42"


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


def test_add_wiremock_to_respx_body_equal_to_json() -> None:
    """Two stubs at the same URL differ by ``equalToJson`` body."""
    url = f"{BASE_URL}/v1/blocks/{_PAGE_ID}/children"
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "PATCH",
                    "urlPath": f"/v1/blocks/{_PAGE_ID}/children",
                    "bodyPatterns": [
                        {
                            "equalToJson": {
                                "children": [{"type": "image"}],
                            },
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"type": "image"}},
            },
            {
                "request": {
                    "method": "PATCH",
                    "urlPath": f"/v1/blocks/{_PAGE_ID}/children",
                    "bodyPatterns": [
                        {
                            "equalToJson": {
                                "children": [{"type": "paragraph"}],
                            },
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"type": "paragraph"}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        image_response = httpx.patch(
            url=url,
            json={"children": [{"type": "image"}]},
        )
        paragraph_response = httpx.patch(
            url=url,
            json={"children": [{"type": "paragraph"}]},
        )
        assert image_response.json() == {"type": "image"}
        assert paragraph_response.json() == {"type": "paragraph"}


def test_add_wiremock_to_respx_body_equal_to_json_no_match() -> None:
    """A request whose body matches no ``equalToJson`` stub is
    unhandled.
    """
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": {"a": 1}}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"a": 2})


def test_add_wiremock_to_respx_body_equal_to_json_from_string() -> None:
    """``equalToJson`` may be given as a JSON string."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": '{"a": 1}'}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(url=f"{BASE_URL}/v1/pages", json={"a": 1})
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_equal_to_json_invalid_string() -> None:
    """A non-JSON ``equalToJson`` string is compared as raw text."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": "not json"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"a": 1})


def test_add_wiremock_to_respx_body_equal_to_json_not_json_body() -> None:
    """A non-JSON request body does not match ``equalToJson``."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": {"a": 1}}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", content=b"not json")


def test_add_wiremock_to_respx_body_ignore_extra_elements() -> None:
    """``ignoreExtraElements`` matches a subset of object keys."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"a": 1},
                            "ignoreExtraElements": True,
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(
            url=f"{BASE_URL}/v1/pages",
            json={"a": 1, "b": 2},
        )
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_extra_elements_not_ignored() -> None:
    """Without ``ignoreExtraElements``, extra object keys do not match."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": {"a": 1}}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"a": 1, "b": 2})


def test_add_wiremock_to_respx_body_ignore_array_order() -> None:
    """``ignoreArrayOrder`` matches arrays regardless of element order."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"items": [1, 2, 3]},
                            "ignoreArrayOrder": True,
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(
            url=f"{BASE_URL}/v1/pages",
            json={"items": [3, 1, 2]},
        )
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_array_order_enforced() -> None:
    """Without ``ignoreArrayOrder``, array element order must match."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": {"items": [1, 2, 3]}}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"items": [3, 1, 2]})


def test_add_wiremock_to_respx_body_array_length_mismatch() -> None:
    """An array of a different length does not match without flags."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": {"items": [1, 2]}}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"items": [1, 2, 3]})


def test_add_wiremock_to_respx_body_array_ignore_extra_ordered() -> None:
    """``ignoreExtraElements`` matches an in-order subsequence of an array."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"items": [1, 3]},
                            "ignoreExtraElements": True,
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(
            url=f"{BASE_URL}/v1/pages",
            json={"items": [1, 2, 3]},
        )
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_array_ignore_extra_missing() -> None:
    """An ordered subsequence match fails when an element is missing."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"items": [1, 4]},
                            "ignoreExtraElements": True,
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"items": [1, 2, 3]})


def test_add_wiremock_to_respx_body_array_unordered_missing() -> None:
    """An unordered array match fails when an expected element is
    absent.
    """
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"items": [1, 9]},
                            "ignoreArrayOrder": True,
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"items": [1, 2, 3]})


def test_add_wiremock_to_respx_body_object_vs_array() -> None:
    """An object expectation does not match an array body."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": {"a": 1}}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json=[1, 2])


def test_add_wiremock_to_respx_body_array_vs_object() -> None:
    """An array expectation does not match an object body."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalToJson": [1, 2]}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"a": 1})


def test_add_wiremock_to_respx_body_missing_key() -> None:
    """An expected object key absent from the body does not match."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {
                            "equalToJson": {"a": 1, "b": 2},
                            "ignoreExtraElements": True,
                        },
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", json={"a": 1})


def test_add_wiremock_to_respx_body_contains() -> None:
    """``contains`` matches a substring of the raw request body."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"contains": "needle"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(
            url=f"{BASE_URL}/v1/pages",
            content=b"a needle in a haystack",
        )
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_contains_non_utf8() -> None:
    """``contains`` does not match a non-UTF-8 request body."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"contains": "needle"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", content=b"\xff\xfe")


def test_add_wiremock_to_respx_body_equal_to() -> None:
    """``equalTo`` matches the raw request body exactly."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalTo": "exact body"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(
            url=f"{BASE_URL}/v1/pages",
            content=b"exact body",
        )
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_equal_to_no_match() -> None:
    """``equalTo`` does not match a different raw request body."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"equalTo": "exact body"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", content=b"different")


def test_add_wiremock_to_respx_body_multiple_patterns() -> None:
    """All ``bodyPatterns`` on a stub must match together."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [
                        {"contains": "alpha"},
                        {"contains": "omega"},
                    ],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        with pytest.raises(expected_exception=AssertionError):
            httpx.post(url=f"{BASE_URL}/v1/pages", content=b"only alpha")
        response = httpx.post(
            url=f"{BASE_URL}/v1/pages",
            content=b"alpha and omega",
        )
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_patterns_not_list() -> None:
    """A non-list ``bodyPatterns`` is ignored."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "GET",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": "not-a-list",
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.get(url=f"{BASE_URL}/v1/pages")
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_pattern_non_dict() -> None:
    """A non-dict body matcher entry is skipped."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": ["not-a-dict", {"contains": "x"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(url=f"{BASE_URL}/v1/pages", content=b"xyz")
        assert response.json() == {"ok": True}


def test_add_wiremock_to_respx_body_pattern_unsupported() -> None:
    """An unsupported body matcher is ignored, matching any body."""
    stubs: dict[str, Any] = {
        "mappings": [
            {
                "request": {
                    "method": "POST",
                    "urlPath": "/v1/pages",
                    "bodyPatterns": [{"matches": ".*"}],
                },
                "response": {"status": 200, "jsonBody": {"ok": True}},
            },
        ],
    }
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url=BASE_URL)
        response = httpx.post(url=f"{BASE_URL}/v1/pages", json={"any": True})
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
