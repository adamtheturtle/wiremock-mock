=========
Changelog
=========

.. towncrier release notes start

2026.08.16
----------

- Add a public ``add_wiremock_to_responses`` integration for using WireMock
  stubs with requests clients mocked by responses.

- Add support for Base64-encoded response bodies, custom status messages and
  multi-value response headers in WireMock stubs.

2026.06.22
----------

- Added support for matching requests on their body with WireMock ``bodyPatterns``: ``equalToJson`` (honouring ``ignoreArrayOrder`` and ``ignoreExtraElements``), ``contains`` and ``equalTo``.

2026.03.02.1
------------


2026.03.02
----------
