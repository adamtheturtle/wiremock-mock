|Build Status| |PyPI|

wiremock-mock
=============

Serve WireMock stubs with `responses`_ or `respx`_.

Requires Python |minimum-python-version|\+.

.. contents::
   :local:

Installation
------------

.. code-block:: console

   uv pip install wiremock-mock

Or with pip:

.. code-block:: console

   pip install wiremock-mock

Usage
-----

requests with responses
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   """Use WireMock stubs with requests and responses."""

   from http import HTTPStatus
   from typing import Any

   import requests
   import responses

   from wiremock_mock import add_wiremock_to_responses

   stubs: dict[str, Any] = {
       "mappings": [
           {
               "request": {"method": "GET", "urlPath": "/v1/pages"},
               "response": {
                   "status": 200,
                   "jsonBody": {"object": "list", "results": []},
               },
           },
       ],
   }
   with responses.RequestsMock(assert_all_requests_are_fired=False) as m:
       add_wiremock_to_responses(
           mock_obj=m, stubs=stubs, base_url="http://notion-mock.test"
       )
       response = requests.get(url="http://notion-mock.test/v1/pages", timeout=1)
       assert response.status_code == HTTPStatus.OK  # noqa: S101

The standard responses decorator workflow is also supported by passing
``responses.mock`` while ``@responses.activate`` is active.

httpx with respx
~~~~~~~~~~~~~~~~

.. code-block:: python

   """Use WireMock stubs with httpx and respx."""

   from http import HTTPStatus
   from typing import Any

   import httpx
   import respx

   from wiremock_mock import add_wiremock_to_respx

   stubs: dict[str, Any] = {
       "mappings": [
           {
               "request": {"method": "GET", "urlPath": "/v1/pages"},
               "response": {
                   "status": 200,
                   "jsonBody": {"object": "list", "results": []},
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
       assert response.status_code == HTTPStatus.OK  # noqa: S101

These integrations let you use existing WireMock stub files (e.g. from the
WireMock Admin API import format) without running WireMock in Docker. HTTP
traffic is mocked through responses for ``requests`` clients or respx for
``httpx`` clients. To load stubs from a JSON file, use
``json.loads(path.read_text())``.

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
- **Request body**: ``bodyPatterns`` with ``equalToJson`` (honouring
  ``ignoreArrayOrder`` and ``ignoreExtraElements``), ``contains`` and
  ``equalTo``. This lets two requests to the same method and URL return
  different responses based on their bodies.
- **Response**: ``status``, ``statusMessage``, single- or multi-value
  ``headers``, ``jsonBody``, ``body``, ``base64Body``

``statusMessage`` is supported by the respx integration; responses does not
provide a custom reason-phrase hook.

Full documentation
------------------

See the `full documentation <https://wiremock-mock.readthedocs.io/en/latest/>`__ for more information including how to contribute.

.. _responses: https://github.com/getsentry/responses
.. _respx: https://lundberg.github.io/respx/

.. |Build Status| image:: https://github.com/adamtheturtle/wiremock-mock/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/wiremock-mock/actions
.. |PyPI| image:: https://badge.fury.io/py/wiremock-mock.svg
   :target: https://badge.fury.io/py/wiremock-mock
.. |minimum-python-version| replace:: 3.12
