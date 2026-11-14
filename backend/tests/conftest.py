import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = "sqlite:///./test_queuelens.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    from app.database import Base, get_db
    from app.main import app
    from app.seed import seed_database

    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    seed_database(db)
    from app.seed import run_initial_optimization
    run_initial_optimization(db)
    db.close()

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    try:
        if os.path.exists("./test_queuelens.db"):
            os.remove("./test_queuelens.db")
    except OSError:
        pass


@pytest.fixture
def db_session(client):
    from app.seed import reset_scenario
    db = TestingSessionLocal()
    reset_scenario(db)
    try:
        yield db
    finally:
        db.close()
