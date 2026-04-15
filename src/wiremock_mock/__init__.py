"""Package for serving WireMock stubs as a mock with respx."""

import re
from typing import Any

import httpx
import respx
from beartype import beartype


def _build_path_pattern(
    *,
    base_url: str,
    path: str,
    path_pattern: str | None,
    query_params: dict[str, Any] | None,
) -> re.Pattern[str]:
    """Build a URL pattern for matching requests."""
    base = base_url.rstrip("/")
    path_part = path if path.startswith("/") else f"/{path}"

    if path_pattern is not None:
        path_re = path_pattern
    else:
        path_re = re.escape(pattern=path_part)

    full_pattern = f"^{re.escape(pattern=base)}{path_re}"

    if query_params:
        lookaheads: list[str] = []
        for param_name, param_matcher in query_params.items():
            match param_matcher:
                case {"equalTo": eq_val} if eq_val is not None:
                    value = re.escape(pattern=str(object=eq_val))
                    lookaheads.append(
                        f"(?=.*{re.escape(pattern=param_name)}={value})"
                    )
        if lookaheads:
            full_pattern += r"\?" + "".join(lookaheads) + r".*"

    full_pattern += r"(\?.*)?$"
    return re.compile(pattern=full_pattern)


def _build_response(
    *,
    response_raw: dict[str, Any],
) -> httpx.Response:
    """Build an httpx Response from a WireMock response dict."""
    match response_raw.get("status"):
        case int() as status:
            pass
        case _:
            status = 200

    headers_raw = response_raw.get("headers")
    headers: dict[str, str] = (
        headers_raw if isinstance(headers_raw, dict) else {}
    )

    json_body = response_raw.get("jsonBody")
    if json_body is not None:
        return httpx.Response(
            status_code=status,
            headers=headers,
            json=json_body,
        )

    match response_raw.get("body"):
        case bytes() as b:
            return httpx.Response(
                status_code=status,
                headers=headers,
                content=b,
            )
        case str() as s:
            return httpx.Response(
                status_code=status,
                headers=headers,
                content=s.encode(),
            )
        case None:
            return httpx.Response(
                status_code=status,
                headers=headers,
            )
        case other:
            return httpx.Response(
                status_code=status,
                headers=headers,
                content=str(object=other).encode(),
            )


@beartype
def add_wiremock_to_respx(
    *,
    mock_obj: respx.MockRouter | respx.Router,
    stubs: dict[str, Any],
    base_url: str,
) -> None:
    """
    Add mock routes from WireMock stubs to a respx mock/router.

    Supports request matching by:
    - method
    - ``urlPath`` (exact) or ``urlPathPattern`` (regex)
    - ``queryParameters`` with ``equalTo``

    Response uses status, headers, and ``jsonBody`` from each stub.

    :param mock_obj: The respx MockRouter or Router to add routes to.
    :param stubs: WireMock stubs dict with ``mappings`` array (e.g. from
        ``json.loads(path.read_text())``).
    :param base_url: Base URL for all routes. Must match ``respx.mock()``.
    """
    match stubs.get("mappings") or []:
        case list() as raw:
            pass
        case _:
            return

    for item in raw:
        match item:
            case {
                "request": dict() as request_raw,
                "response": dict() as response_raw,
            }:
                pass
            case _:
                continue

        method_raw: object = request_raw.get("method") or "GET"
        if not isinstance(method_raw, str):
            continue
        method = method_raw.upper()

        url_path = request_raw.get("urlPath")
        url_path_pattern = request_raw.get("urlPathPattern")

        query_params: dict[str, Any] | None
        match request_raw.get("queryParameters"):
            case dict() as query_params:
                pass
            case _:
                query_params = None

        if url_path is None and url_path_pattern is None:
            continue

        path = str(object=url_path) if url_path is not None else ""
        path_pattern = (
            str(object=url_path_pattern)
            if url_path_pattern is not None
            else None
        )

        response = _build_response(response_raw=response_raw)

        url_pattern = _build_path_pattern(
            base_url=base_url,
            path=path,
            path_pattern=path_pattern,
            query_params=query_params,
        )

        route = mock_obj.route(method=method, url=url_pattern)
        route.mock(return_value=response)


__all__ = ["add_wiremock_to_respx"]
