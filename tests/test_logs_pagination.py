import unittest
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models import LogSistema, TipoLogEnum
from app.routes.publicEndpoints import router


class LogsPaginationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        LogSistema.__table__.create(self.engine)
        with Session(self.engine) as db:
            db.add_all([
                LogSistema(
                    log_id=i, tipo=TipoLogEnum.error if i % 2 == 0 else TipoLogEnum.info,
                    mensaje=f"Log {i}", hora_log=datetime(2026, 9, 24 if i <= 55 else 23, 12),
                ) for i in range(1, 61)
            ])
            db.commit()

        def test_db():
            with Session(self.engine) as db:
                yield db

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_default_page_and_tied_timestamps(self):
        response = self.client.get("/logs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 50)
        self.assertEqual([row["log_id"] for row in response.json()], list(range(55, 5, -1)))

    def test_second_page_and_empty_page(self):
        first = self.client.get("/logs?limit=10").json()
        second = self.client.get("/logs?skip=10&limit=10").json()
        self.assertEqual([row["log_id"] for row in second], list(range(45, 35, -1)))
        self.assertFalse({row["log_id"] for row in first} & {row["log_id"] for row in second})
        self.assertEqual(self.client.get("/logs?skip=60").json(), [])

    def test_filters_apply_before_pagination(self):
        response = self.client.get("/logs?fecha=2026-09-23&tipo=error&skip=1&limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["log_id"] for row in response.json()], [58, 56])

    def test_invalid_pagination(self):
        for query in ("skip=-1", "limit=0", "limit=501", "limit=abc"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"/logs?{query}").status_code, 422)


if __name__ == "__main__":
    unittest.main()
