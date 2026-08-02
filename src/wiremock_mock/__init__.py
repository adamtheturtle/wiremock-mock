"""Package for serving WireMock stubs with Python HTTP mocking
libraries.
"""

import base64
import json
import re
from collections.abc import Callable
from typing import Any, NamedTuple, Protocol, TypedDict, cast  # noqa: TID251

import httpx
import responses
import respx
from beartype import beartype
from respx.patterns import Match, Pattern


class _QueryParamMatcher(TypedDict, total=False):
    """A WireMock query parameter matcher."""

    equalTo: object


class _RequestSpec(TypedDict, total=False):
    """A WireMock request specification."""

    method: object
    urlPath: object
    urlPathPattern: object
    queryParameters: object
    bodyPatterns: object


class _ResponseSpec(TypedDict, total=False):
    """A WireMock response specification."""

    status: object
    statusMessage: object
    headers: object
    jsonBody: object
    body: object
    base64Body: object


class _RequestWithBody(Protocol):
    """The part of a prepared HTTP request used by body matchers."""

    body: object


class _BodyMatcher(NamedTuple):
    """A backend-neutral request-body matcher."""

    identity: str
    predicate: Callable[[bytes | None], bool]


class _ParsedResponse(NamedTuple):
    """A backend-neutral WireMock response."""

    status: int
    headers: list[tuple[str, str]]
    body: bytes
    status_message: str | None


class _ParsedMapping(NamedTuple):
    """A backend-neutral WireMock mapping."""

    method: str
    url_pattern: re.Pattern[str]
    body_matchers: list[_BodyMatcher]
    response: _ParsedResponse


def _coerce_json(*, value: object) -> object:
    """
    Coerce a WireMock ``equalToJson`` value to a comparable JSON value.

    The value may be given either as a JSON value directly or as a string
    containing JSON. Strings that are not valid JSON are returned unchanged.
    """
    if isinstance(value, str):
        try:
            return json.loads(s=value)
        except json.JSONDecodeError:
            return value
    return value


def _json_values_match(
    *,
    expected: object,
    actual: object,
    ignore_array_order: bool,
    ignore_extra_elements: bool,
) -> bool:
    """Return whether ``actual`` matches ``expected`` JSON, per the
    flags.
    """
    match expected:
        case dict():
            return _json_objects_match(
                expected=cast("dict[object, object]", expected),
                actual=actual,
                ignore_array_order=ignore_array_order,
                ignore_extra_elements=ignore_extra_elements,
            )
        case list():
            return isinstance(actual, list) and _json_arrays_match(
                expected=cast("list[object]", expected),
                actual=cast("list[object]", actual),
                ignore_array_order=ignore_array_order,
                ignore_extra_elements=ignore_extra_elements,
            )
        case _:
            return expected == actual


def _json_objects_match(
    *,
    expected: dict[object, object],
    actual: object,
    ignore_array_order: bool,
    ignore_extra_elements: bool,
) -> bool:
    """Return whether ``actual`` matches the ``expected`` JSON object."""
    if not isinstance(actual, dict):
        return False
    actual_obj = cast("dict[object, object]", actual)
    if not ignore_extra_elements and expected.keys() != actual_obj.keys():
        return False
    for key, expected_value in expected.items():
        if key not in actual_obj:
            return False
        if not _json_values_match(
            expected=expected_value,
            actual=actual_obj[key],
            ignore_array_order=ignore_array_order,
            ignore_extra_elements=ignore_extra_elements,
        ):
            return False
    return True


def _json_arrays_match(
    *,
    expected: list[object],
    actual: list[object],
    ignore_array_order: bool,
    ignore_extra_elements: bool,
) -> bool:
    """Return whether ``actual`` matches the ``expected`` JSON array."""
    if ignore_array_order:
        return _json_arrays_match_unordered(
            expected=expected,
            actual=actual,
            ignore_extra_elements=ignore_extra_elements,
        )
    return _json_arrays_match_ordered(
        expected=expected,
        actual=actual,
        ignore_extra_elements=ignore_extra_elements,
    )


def _json_arrays_match_unordered(
    *,
    expected: list[object],
    actual: list[object],
    ignore_extra_elements: bool,
) -> bool:
    """Match arrays as multisets, ignoring element order."""
    used = [False] * len(actual)
    for expected_item in expected:
        for index, actual_item in enumerate(iterable=actual):
            if not used[index] and _json_values_match(
                expected=expected_item,
                actual=actual_item,
                ignore_array_order=True,
                ignore_extra_elements=ignore_extra_elements,
            ):
                used[index] = True
                break
        else:
            return False
    return ignore_extra_elements or all(used)


def _json_arrays_match_ordered(
    *,
    expected: list[object],
    actual: list[object],
    ignore_extra_elements: bool,
) -> bool:
    """Match arrays positionally, preserving element order."""
    if not ignore_extra_elements and len(expected) != len(actual):
        return False
    actual_iter = iter(actual)
    for expected_item in expected:
        for actual_item in actual_iter:
            if _json_values_match(
                expected=expected_item,
                actual=actual_item,
                ignore_array_order=False,
                ignore_extra_elements=ignore_extra_elements,
            ):
                break
        else:
            return False
    return True


def _request_text(*, content: bytes | None) -> str | None:
    """Return request content as text, or ``None`` if it is not text."""
    if content is None:
        return None
    try:
        return content.decode()
    except UnicodeDecodeError:
        return None


def _equal_to_predicate(
    *,
    expected: str,
) -> Callable[[bytes | None], bool]:
    """Build a predicate matching the raw request body exactly."""

    def predicate(content: bytes | None) -> bool:
        """Return whether the request body equals ``expected``."""
        return _request_text(content=content) == expected

    return predicate


def _contains_predicate(
    *,
    substring: str,
) -> Callable[[bytes | None], bool]:
    """Build a predicate matching a substring of the raw request body."""

    def predicate(content: bytes | None) -> bool:
        """Return whether the request body contains ``substring``."""
        text = _request_text(content=content)
        return text is not None and substring in text

    return predicate


def _equal_to_json_predicate(
    *,
    expected: object,
    ignore_array_order: bool,
    ignore_extra_elements: bool,
) -> Callable[[bytes | None], bool]:
    """Build a predicate matching the request body as JSON."""

    def predicate(content: bytes | None) -> bool:
        """Return whether the request body matches ``expected`` as
        JSON.
        """
        text = _request_text(content=content)
        if text is None:
            return False
        try:
            actual = json.loads(s=text)
        except json.JSONDecodeError:
            return False
        return _json_values_match(
            expected=expected,
            actual=actual,
            ignore_array_order=ignore_array_order,
            ignore_extra_elements=ignore_extra_elements,
        )

    return predicate


class _BodyPattern(Pattern):
    """A WireMock request-body matcher expressed as a respx pattern."""

    key = "wiremock_body"

    def __init__(
        self,
        *,
        identity: str,
        predicate: Callable[[bytes | None], bool],
    ) -> None:
        """
        :param identity: A stable string identifying this matcher, used
        so
            that distinct body matchers produce distinct respx routes.
        :param predicate: Returns whether a request body matches.
        """
        super().__init__(value=identity)
        self._predicate = predicate

    def match(self, request: httpx.Request) -> Match:
        """Return whether ``request`` matches this body pattern."""
        return Match(matches=self._predicate(request.read()))


def _build_body_matcher(*, matcher: dict[str, object]) -> _BodyMatcher | None:
    """Build a backend-neutral WireMock request-body matcher."""
    identity = json.dumps(obj=matcher, sort_keys=True, default=str)
    ignore_array_order = matcher.get("ignoreArrayOrder") is True
    ignore_extra_elements = matcher.get("ignoreExtraElements") is True

    match matcher:
        case {"equalToJson": equal_to_json}:
            predicate = _equal_to_json_predicate(
                expected=_coerce_json(value=equal_to_json),
                ignore_array_order=ignore_array_order,
                ignore_extra_elements=ignore_extra_elements,
            )
        case {"equalTo": str() as equal_to}:
            predicate = _equal_to_predicate(expected=equal_to)
        case {"contains": str() as contains}:
            predicate = _contains_predicate(substring=contains)
        case _:
            return None

    return _BodyMatcher(identity=identity, predicate=predicate)


def _build_body_matchers(*, body_patterns: object) -> list[_BodyMatcher]:
    """Build matchers from a WireMock ``bodyPatterns`` list."""
    if not isinstance(body_patterns, list):
        return []
    patterns: list[_BodyMatcher] = []
    for matcher in cast("list[object]", body_patterns):
        if not isinstance(matcher, dict):
            continue
        pattern = _build_body_matcher(
            matcher=cast("dict[str, object]", matcher)
        )
        if pattern is not None:
            patterns.append(pattern)
    return patterns


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
            eq_matcher = cast("_QueryParamMatcher", param_matcher)
            match eq_matcher:
                case {"equalTo": eq_val} if eq_val is not None:
                    value = re.escape(pattern=str(object=eq_val))
                    lookaheads.append(
                        f"(?=.*{re.escape(pattern=param_name)}={value})"
                    )
                case _:
                    pass
        if lookaheads:
            full_pattern += r"\?" + "".join(lookaheads) + r".*"

    full_pattern += r"(\?.*)?$"
    return re.compile(pattern=full_pattern)


def _build_response_headers(*, headers_raw: object) -> list[tuple[str, str]]:
    """Build HTTPX headers from a WireMock response header mapping."""
    headers: list[tuple[str, str]] = []
    if not isinstance(headers_raw, dict):
        return headers
    for name, value in cast("dict[object, object]", headers_raw).items():
        if not isinstance(name, str):
            continue
        match value:
            case str() as header_value:
                headers.append((name, header_value))
            case list():
                headers.extend(
                    (name, header_value)
                    for header_value in cast("list[object]", value)
                    if isinstance(header_value, str)
                )
            case _:
                pass
    return headers


def _build_response_extensions(*, status_message: object) -> dict[str, object]:
    """Build HTTPX extensions for WireMock response metadata."""
    if isinstance(status_message, str):
        return {"reason_phrase": status_message.encode()}
    return {}


def _build_response(*, parsed: _ParsedResponse) -> httpx.Response:
    """Build an httpx response from a parsed WireMock response."""
    extensions = _build_response_extensions(
        status_message=parsed.status_message
    )
    return httpx.Response(
        status_code=parsed.status,
        headers=parsed.headers,
        content=parsed.body,
        extensions=extensions,
    )


def _parse_response(*, response_spec: _ResponseSpec) -> _ParsedResponse:
    """Parse a backend-neutral response from a WireMock response dict."""
    match response_spec.get("status"):
        case int() as status:
            pass
        case _:
            status = 200

    headers = _build_response_headers(headers_raw=response_spec.get("headers"))
    status_message_raw = response_spec.get("statusMessage")
    status_message = (
        status_message_raw if isinstance(status_message_raw, str) else None
    )

    json_body = response_spec.get("jsonBody")
    if json_body is not None:
        body = json.dumps(
            obj=json_body,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        if not any(name.lower() == "content-type" for name, _ in headers):
            headers.append(("Content-Type", "application/json"))
        return _ParsedResponse(
            status=status,
            headers=headers,
            body=body,
            status_message=status_message,
        )

    match response_spec.get("base64Body"):
        case str() as base64_body:
            return _ParsedResponse(
                status=status,
                headers=headers,
                body=base64.b64decode(s=base64_body, validate=True),
                status_message=status_message,
            )
        case _:
            pass

    match response_spec.get("body"):
        case bytes() as b:
            body = b
        case str() as s:
            body = s.encode()
        case None:
            body = b""
        case other:
            body = str(object=other).encode()
    return _ParsedResponse(
        status=status,
        headers=headers,
        body=body,
        status_message=status_message,
    )


def _parse_mappings(
    *, stubs: dict[str, Any], base_url: str
) -> list[_ParsedMapping]:
    """Parse valid mappings into a representation shared by backends."""
    raw: object = stubs.get("mappings") or []
    if not isinstance(raw, list):
        return []
    mappings = cast("list[object]", raw)
    parsed_mappings: list[_ParsedMapping] = []

    for item in mappings:
        if not isinstance(item, dict):
            continue
        mapping = cast("dict[str, object]", item)
        match mapping:
            case {
                "request": dict(),
                "response": dict(),
            }:
                request_spec = cast("_RequestSpec", mapping["request"])
                response_spec = cast("_ResponseSpec", mapping["response"])
            case _:
                continue

        method_raw: object = request_spec.get("method") or "GET"
        if not isinstance(method_raw, str):
            continue
        method = method_raw.upper()

        url_path = request_spec.get("urlPath")
        url_path_pattern = request_spec.get("urlPathPattern")
        query_params_raw = request_spec.get("queryParameters")
        query_params: dict[str, object] | None
        match query_params_raw:
            case dict():
                query_params = cast("dict[str, object]", query_params_raw)
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
        parsed_mappings.append(
            _ParsedMapping(
                method=method,
                url_pattern=_build_path_pattern(
                    base_url=base_url,
                    path=path,
                    path_pattern=path_pattern,
                    query_params=query_params,
                ),
                body_matchers=_build_body_matchers(
                    body_patterns=request_spec.get("bodyPatterns"),
                ),
                response=_parse_response(response_spec=response_spec),
            )
        )
    return parsed_mappings


def _responses_request_content(*, body: object) -> bytes | None:
    """Convert a requests body into content accepted by our matchers."""
    match body:
        case bytes() as content:
            return content
        case str() as content:
            return content.encode()
        case None:
            return b""
        case _:
            return None


def _build_responses_matcher(
    *, body_matcher: _BodyMatcher
) -> Callable[[_RequestWithBody], tuple[bool, str]]:
    """Adapt a backend-neutral body matcher for responses."""

    def matcher(request: _RequestWithBody) -> tuple[bool, str]:
        """Return whether a requests request body matches."""
        matches = body_matcher.predicate(
            _responses_request_content(body=request.body)
        )
        reason = (
            f"WireMock body pattern did not match: {body_matcher.identity}"
        )
        return matches, reason

    return matcher


def _build_responses_callback(
    *, parsed: _ParsedResponse
) -> Callable[[object], tuple[int, list[tuple[str, str]], bytes]]:
    """Build a responses callback returning a parsed WireMock response."""

    def callback(
        _request: object,
    ) -> tuple[int, list[tuple[str, str]], bytes]:
        """Return the configured status, headers and body."""
        return parsed.status, parsed.headers, parsed.body

    return callback


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
    - ``bodyPatterns`` (``equalToJson``, ``contains``, ``equalTo``)

    ``equalToJson`` supports the ``ignoreArrayOrder`` and
    ``ignoreExtraElements`` options. Multiple ``bodyPatterns`` on a single
    stub must all match, letting two requests to the same method and URL
    return different responses based on their bodies.

    Response supports ``status``, ``statusMessage``, ``headers``,
    ``jsonBody``, ``body`` and ``base64Body`` from each stub.

    :param mock_obj: The respx MockRouter or Router to add routes to.
    :param stubs: WireMock stubs dict with ``mappings`` array (e.g. from
        ``json.loads(path.read_text())``).
    :param base_url: Base URL for all routes. Must match ``respx.mock()``.
    """
    for mapping in _parse_mappings(stubs=stubs, base_url=base_url):
        body_patterns = [
            _BodyPattern(
                identity=matcher.identity,
                predicate=matcher.predicate,
            )
            for matcher in mapping.body_matchers
        ]
        route = mock_obj.route(
            *body_patterns,
            method=mapping.method,
            url=mapping.url_pattern,
        )
        route.mock(return_value=_build_response(parsed=mapping.response))


@beartype
def add_wiremock_to_responses(
    *,
    mock_obj: responses.RequestsMock,
    stubs: dict[str, Any],
    base_url: str,
) -> None:
    """
    Add mock routes from WireMock stubs to a responses mock.

    Request matching and response fields are the same as for
    :func:`add_wiremock_to_respx`, except that custom ``statusMessage`` values
    are not supported by responses.

    :param mock_obj: The responses RequestsMock to add routes to.
    :param stubs: WireMock stubs dict with ``mappings`` array (e.g. from
        ``json.loads(path.read_text())``).
    :param base_url: Base URL for all routes.
    """
    for mapping in _parse_mappings(stubs=stubs, base_url=base_url):
        matchers = tuple(
            _build_responses_matcher(body_matcher=body_matcher)
            for body_matcher in mapping.body_matchers
        )
        response = responses.CallbackResponse(
            method=mapping.method,
            url=mapping.url_pattern,
            callback=_build_responses_callback(parsed=mapping.response),
            content_type=None,
            match=matchers,
        )
        mock_obj.add(response)


__all__ = ["add_wiremock_to_responses", "add_wiremock_to_respx"]
