|project|
=========

|project| serves WireMock stubs with HTTPX2, `responses`_ or `respx`_.

Requires Python |minimum-python-version|\+.

Installation
------------

.. code-block:: shell

   pip install wiremock-mock

Usage
-----

requests with responses
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   """Use WireMock stubs with requests and responses."""

   from collections.abc import Mapping
   from http import HTTPStatus

   import requests
   import responses

   from wiremock_mock import add_wiremock_to_responses

   stubs: Mapping[str, object] = {
       "mappings": [
           {
               "request": {"method": "GET", "urlPath": "/v1/pages"},
               "response": {
                   "status": 200,
                   "jsonBody": {
                       "object": "list",
                       "results": list[object](),
                   },
               },
           },
       ],
   }
   with responses.RequestsMock(assert_all_requests_are_fired=False) as m:
       add_wiremock_to_responses(
           mock_obj=m, stubs=stubs, base_url="http://notion-mock.test"
       )
       response = requests.get(url="http://notion-mock.test/v1/pages", timeout=1)
       assert response.status_code == HTTPStatus.OK

The standard responses decorator workflow is also supported by passing ``responses.mock`` while ``@responses.activate`` is active.

httpx with respx
~~~~~~~~~~~~~~~~

.. code-block:: python

   """Use WireMock stubs with httpx and respx."""

   from collections.abc import Mapping
   from http import HTTPStatus

   import httpx
   import respx

   from wiremock_mock import add_wiremock_to_respx

   stubs: Mapping[str, object] = {
       "mappings": [
           {
               "request": {"method": "GET", "urlPath": "/v1/pages"},
               "response": {
                   "status": 200,
                   "jsonBody": {
                       "object": "list",
                       "results": list[object](),
                   },
               },
           },
       ],
   }
   with respx.mock(
       base_url="http://notion-mock.test", assert_all_called=False
   ) as m:
       add_wiremock_to_respx(
           mock_obj=m, stubs=stubs, base_url="http://notion-mock.test"
       )
       response = httpx.get(url="http://notion-mock.test/v1/pages")
       assert response.status_code == HTTPStatus.OK

HTTPX2 with a native mock transport
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   """Use WireMock stubs with HTTPX2."""

   from collections.abc import Mapping
   from http import HTTPStatus

   import httpx2

   from wiremock_mock import create_httpx2_transport

   stubs: Mapping[str, object] = {
       "mappings": [
           {
               "request": {"method": "GET", "urlPath": "/v1/pages"},
               "response": {
                   "status": 200,
                   "jsonBody": {
                       "object": "list",
                       "results": list[object](),
                   },
               },
           },
       ],
   }
   transport = create_httpx2_transport(
       stubs=stubs, base_url="http://notion-mock.test"
   )
   with httpx2.Client(transport=transport) as client:
       response = client.get(url="http://notion-mock.test/v1/pages")
   assert response.status_code == HTTPStatus.OK

These integrations let you use existing WireMock stub files (e.g. from the WireMock Admin API import format) without running WireMock in Docker.
HTTP traffic is mocked through responses for ``requests`` clients, respx for ``httpx`` clients, or a native mock transport for ``httpx2`` clients.
To load stubs from a JSON file, use ``json.loads(path.read_text())``.

Use cases
---------

- Use existing WireMock stub files without running WireMock in Docker
- Test against external APIs (e.g. Notion) without network access
- Reuse stubs exported from WireMock Admin API or recorded mappings
- Run tests in CI without Docker/socket dependencies

Supported stub features
-----------------------

- **Request matching**: ``method``, ``urlPath`` (exact), ``urlPathPattern`` (regex)
- **Query parameters**: ``queryParameters`` with ``equalTo``
- **Request body**: ``bodyPatterns`` with ``equalToJson`` (honouring ``ignoreArrayOrder`` and ``ignoreExtraElements``), ``contains`` and ``equalTo``.
  This lets two requests to the same method and URL return different responses based on their bodies.
- **Response**: ``status``, ``statusMessage``, single- or multi-value ``headers``, ``jsonBody``, ``body``, ``base64Body``

``statusMessage`` is supported by the respx and HTTPX2 integrations.
Responses does not provide a custom reason-phrase hook.

Reference
---------

.. toctree::
   :maxdepth: 3

   api-reference
   release-process
   unreleased
   changelog
   contributing

.. _responses: https://github.com/getsentry/responses
.. _respx: https://lundberg.github.io/respx/
