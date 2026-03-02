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
    query_params: dict[str, object] | None,
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
            if not isinstance(param_matcher, dict):
                continue
            eq_val = param_matcher.get("equalTo")
            if eq_val is not None:
                value = re.escape(pattern=str(object=eq_val))
                lookaheads.append(
                    f"(?=.*{re.escape(pattern=param_name)}={value})"
                )
        if lookaheads:
            full_pattern += r"\?" + "".join(lookaheads) + r".*"

    full_pattern += r"$"
    return re.compile(pattern=full_pattern)


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
    raw: object = stubs.get("mappings") or []
    if not isinstance(raw, list):
        return
    mappings = raw

    for item in mappings:
        if not isinstance(item, dict):
            continue

        request_raw = item.get("request")
        response_raw = item.get("response")
        if not isinstance(request_raw, dict) or not isinstance(
            response_raw, dict
        ):
            continue

        method_raw: object = request_raw.get("method") or "GET"
        if not isinstance(method_raw, str):
            continue
        method = method_raw.upper()

        url_path = request_raw.get("urlPath")
        url_path_pattern = request_raw.get("urlPathPattern")
        query_params_raw = request_raw.get("queryParameters")
        query_params: dict[str, object] | None = (
            query_params_raw if isinstance(query_params_raw, dict) else None
        )

        if url_path is None and url_path_pattern is None:
            continue

        path = str(object=url_path) if url_path is not None else ""
        path_pattern = (
            str(object=url_path_pattern)
            if url_path_pattern is not None
            else None
        )

        status_raw = response_raw.get("status")
        status = status_raw if isinstance(status_raw, int) else 200

        headers_raw = response_raw.get("headers")
        headers: dict[str, str] = (
            headers_raw if isinstance(headers_raw, dict) else {}
        )

        json_body = response_raw.get("jsonBody")
        body = response_raw.get("body")

        if json_body is not None:
            response = httpx.Response(
                status_code=status,
                headers=headers,
                json=json_body,
            )
        elif body is not None:
            response = httpx.Response(
                status_code=status,
                headers=headers,
                content=(
                    body
                    if isinstance(body, bytes)
                    else str(object=body).encode()
                ),
            )
        else:
            response = httpx.Response(
                status_code=status,
                headers=headers,
            )

        url_pattern = _build_path_pattern(
            base_url=base_url,
            path=path,
            path_pattern=path_pattern,
            query_params=query_params,
        )

        route = mock_obj.route(method=method, url=url_pattern)
        route.mock(return_value=response)


__all__ = ["add_wiremock_to_respx"]
