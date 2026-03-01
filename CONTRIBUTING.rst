Contributing
============

Development setup
----------------

.. code-block:: console

   uv sync --extra dev

Running tests
-------------

.. code-block:: console

   uv run pytest

Linting
-------

.. code-block:: console

   uv run ruff check .
   uv run ruff format --check .

Type checking
-------------

.. code-block:: console

   uv run mypy src/
