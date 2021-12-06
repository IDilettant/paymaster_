"""Fixtures module."""
import os
from typing import AsyncIterator

import httpx
import pytest
from asgi_lifespan import LifespanManager
from asyncpg import Pool
from fastapi import FastAPI
from httpx import AsyncClient
from paymaster.currencies import BASE_CURRENCY
from pytest_httpx import HTTPXMock
from testcontainers.postgres import PostgresContainer
from tests.test_currencies import DATA


@pytest.fixture
async def dsn() -> Pool:
    with PostgresContainer("postgres:12-alpine") as postgres:
        # FIXME: непонятно, почему эта «ненужная часть» вообще там
        # лучше прямо с примерами «как надо» и «как есть» и упомянуть, что
        # это специфика testcontainers

        # delete from db url unnecessary path part
        yield postgres.get_connection_url().replace('+psycopg2', '')


@pytest.fixture
def non_mocked_hosts() -> list:
    return ['testserver']


@pytest.fixture
async def app(httpx_mock: HTTPXMock) -> AsyncIterator[FastAPI]:
    from paymaster.app.main import \
        get_application  # local import for testing purpose

    api_key = os.getenv('API_KEY')
    httpx_mock.add_response(
        method='GET',
        url=f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{BASE_CURRENCY}',
        json=DATA,
        status_code=200,
    )

    yield get_application()


@pytest.fixture
async def initialized_app(app: FastAPI, dsn: str) -> AsyncIterator[FastAPI]:
    os.environ['DSN'] = dsn
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(initialized_app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        app=initialized_app,
        base_url="http://testserver",
    ) as client:
        yield client
