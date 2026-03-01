wiremock-mock
=============

Serve WireMock stubs as a mock with `respx`_.

.. _respx: https://lundberg.github.io/respx/

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

   from http import HTTPStatus

   import httpx
   import respx

   from wiremock_mock import add_wiremock_to_respx, load_stubs

   stubs = load_stubs("tests/fixtures/minimal-stubs.json")
   with respx.mock(base_url="http://notion-mock.test", assert_all_called=False) as m:
       add_wiremock_to_respx(mock_obj=m, stubs=stubs, base_url="http://notion-mock.test")
       response = httpx.get("http://notion-mock.test/v1/pages")
       assert response.status_code == HTTPStatus.OK

This lets you use existing WireMock stub files (e.g. from the WireMock Admin API
import format) without running WireMock in Docker. All HTTP traffic is mocked at
the ``httpx`` level via respx.

Supported stub features
----------------------

- **Request matching**: ``method``, ``urlPath`` (exact), ``urlPathPattern`` (regex)
- **Query parameters**: ``queryParameters`` with ``equalTo``
- **Response**: ``status``, ``headers``, ``jsonBody``, ``body``
