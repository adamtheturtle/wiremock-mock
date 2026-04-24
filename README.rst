|Build Status| |PyPI|

wiremock-mock
=============

Serve WireMock stubs as a mock with `respx`_.

Requires Python |minimum-python-version|\+.

Installation
------------

.. code-block:: console

   uv pip install wiremock-mock

Or with pip:

.. code-block:: console

   pip install wiremock-mock

Usage
-----

.. code-block:: python

   """Example usage of wiremock-mock."""

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

All HTTP traffic is mocked at the ``httpx`` level via respx. To load stubs from
a JSON file, use ``json.loads(path.read_text())``.

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
- **Response**: ``status``, ``headers``, ``jsonBody``, ``body``

Full documentation
------------------

See the `full documentation <https://wiremock-mock.readthedocs.io/en/latest/>`__ for more information including how to contribute.

.. _respx: https://lundberg.github.io/respx/

.. |Build Status| image:: https://github.com/adamtheturtle/wiremock-mock/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/wiremock-mock/actions
.. |PyPI| image:: https://badge.fury.io/py/wiremock-mock.svg
   :target: https://badge.fury.io/py/wiremock-mock
.. |minimum-python-version| replace:: 3.12
