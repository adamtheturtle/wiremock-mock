|project|
=========

|project| serves WireMock stubs as a mock with `respx`_.

Requires Python |minimum-python-version|\+.

Installation
------------

.. code-block:: shell

   pip install wiremock-mock

Usage
-----

.. code-block:: python

   from http import HTTPStatus

   import httpx
   import respx

   from wiremock_mock import add_wiremock_to_respx

   stubs = {
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
       assert response.status_code == HTTPStatus.OK

This lets you use existing WireMock stub files (e.g. from the WireMock Admin
API import format) without running WireMock in Docker. All HTTP traffic is
mocked at the ``httpx`` level via respx. To load stubs from a JSON file, use
``json.loads(path.read_text())``.

Supported stub features
-----------------------

- **Request matching**: ``method``, ``urlPath`` (exact), ``urlPathPattern`` (regex)
- **Query parameters**: ``queryParameters`` with ``equalTo``
- **Response**: ``status``, ``headers``, ``jsonBody``, ``body``

Reference
---------

.. toctree::
   :maxdepth: 3

   api-reference
   release-process
   changelog
   contributing

.. _respx: https://lundberg.github.io/respx/
