"""Package for serving WireMock stubs as a mock with respx."""

import json
import re
from pathlib import Path
from typing import Any, cast

import httpx
import respx
from beartype import beartype


@beartype
def load_stubs(path: str | Path) -> dict[str, Any]:
    """
    Load WireMock stubs from a JSON file.

    Supports the WireMock Admin API import format with a ``mappings`` array.

    :param path: Path to the stubs file (``.json``).
    :return: Stubs as a dict with ``mappings`` key.
    """
    path = Path(path)
    text = path.read_text()
    result: Any = json.loads(s=text)
    if not isinstance(result, dict):
        raise ValueError("Stubs file must contain a JSON object")
    return cast(dict[str, Any], result)


def _build_path_pattern(
    *,
    base_url: str,
    path: str,
    path_pattern: str | None,
    query_params: dict[str, Any] | None,
) -> re.Pattern[str]:
    base = base_url.rstrip("/")
    path_part = path if path.startswith("/") else f"/{path}"

    if path_pattern is not None:
        path_re = path_pattern
    else:
        path_re = re.escape(pattern=path_part)

    full_pattern = f"^{re.escape(pattern=base)}{path_re}"

    if query_params:
        lookaheads = []
        for param_name, param_matcher in query_params.items():
            if isinstance(param_matcher, dict) and "equalTo" in param_matcher:
                value = re.escape(pattern=str(object=param_matcher["equalTo"]))
                lookaheads.append(f"(?=.*{re.escape(pattern=param_name)}={value})")
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
    - urlPath (exact) or urlPathPattern (regex)
    - queryParameters with equalTo

    Response uses status, headers, and jsonBody from each stub.

    :param mock_obj: The respx MockRouter or Router to add routes to.
    :param stubs: WireMock stubs dict (from ``load_stubs`` or JSON with
        ``mappings`` array).
    :param base_url: Base URL for all routes. Must match ``respx.mock()``.
    """
    mappings = stubs.get("mappings") or []
    if not isinstance(mappings, list):
        return

    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        request_spec = mapping.get("request")
        response_spec = mapping.get("response")
        if not isinstance(request_spec, dict) or not isinstance(response_spec, dict):
            continue

        method = request_spec.get("method", "GET")
        if isinstance(method, str):
            method = method.upper()
        else:
            continue

        url_path = request_spec.get("urlPath")
        url_path_pattern = request_spec.get("urlPathPattern")
        query_params = request_spec.get("queryParameters")
        if isinstance(query_params, dict) is False:
            query_params = None

        if url_path is None and url_path_pattern is None:
            continue

        path = str(object=url_path) if url_path is not None else ""
        path_pattern = str(object=url_path_pattern) if url_path_pattern is not None else None

        status = response_spec.get("status", 200)
        if not isinstance(status, int):
            status = 200
        headers = response_spec.get("headers") or {}
        if isinstance(headers, dict) is False:
            headers = {}
        json_body = response_spec.get("jsonBody")
        body = response_spec.get("body")

        if json_body is not None:
            response = httpx.Response(
                status_code=status,
                headers=dict(headers),
                json=json_body,
            )
        elif body is not None:
            response = httpx.Response(
                status_code=status,
                headers=dict(headers),
                content=body if isinstance(body, bytes) else str(object=body).encode(),
            )
        else:
            response = httpx.Response(
                status_code=status,
                headers=dict(headers),
            )

        url_pattern = _build_path_pattern(
            base_url=base_url,
            path=path,
            path_pattern=path_pattern,
            query_params=query_params,
        )

        mock_obj.route(method=method, url=url_pattern).mock(return_value=response)


__all__ = ["add_wiremock_to_respx", "load_stubs"]
