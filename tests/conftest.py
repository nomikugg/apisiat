from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - registra todas las tablas en Base.metadata
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import requerir_api_key
from app.main import app
from app.models.integration import ApiKey


def _test_database_url() -> str:
    base_url, _, db_name = settings.database_url.rpartition("/")
    return f"{base_url}/{db_name}_test"


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    test_url = _test_database_url()
    admin_url, _, db_name = test_url.rpartition("/")

    admin_engine = create_engine(f"{admin_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()

    test_engine = create_engine(test_url)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


_FAKE_API_KEY = ApiKey(nombre="test-key", prefijo="sk_test____", clave_hash="", activa=True)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def _override_auth() -> ApiKey:
        return _FAKE_API_KEY

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[requerir_api_key] = _override_auth
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(requerir_api_key, None)
