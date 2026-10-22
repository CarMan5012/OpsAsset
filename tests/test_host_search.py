import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Host
from app.services.host_search import host_keyword_filter, split_search_terms


def test_pasted_ips_match_exact_hosts():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            Host(hostname="first", private_ip="10.0.0.1", public_ip="1.1.1.1, 2.2.2.2"),
            Host(hostname="second", private_ip="10.0.0.2"),
            Host(hostname="similar", private_ip="10.0.0.10"),
        ])
        db.commit()
        condition = host_keyword_filter("10.0.0.1\n10.0.0.2，2.2.2.2")
        names = {host.hostname for host in db.query(Host).filter(condition).all()}
        assert names == {"first", "second"}


def test_single_term_remains_fuzzy_and_search_limit_is_enforced():
    assert split_search_terms("web-01, web-01; db-02") == ["web-01", "db-02"]
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Host(hostname="web-01", private_ip="10.0.0.1"))
        db.commit()
        assert db.query(Host).filter(host_keyword_filter("web")).count() == 1
        assert db.query(Host).filter(host_keyword_filter("10.0.0")).count() == 1
    with pytest.raises(ValueError, match="100"):
        host_keyword_filter(",".join(f"item-{i}" for i in range(101)))


def test_list_and_export_share_batch_search_results():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        for name, ip in (("first", "10.0.0.1"), ("second", "10.0.0.2"), ("similar", "10.0.0.10")):
            response = client.post("/api/hosts", json={"hostname": name, "private_ip": ip})
            assert response.status_code == 200
        params = {"keyword": "10.0.0.1\n10.0.0.2"}
        listed = client.get("/api/hosts", params=params)
        assert listed.status_code == 200
        assert {item["hostname"] for item in listed.json()["items"]} == {"first", "second"}
        exported = client.get("/api/assets/export", params={**params, "format": "xlsx", "columns": "hostname"})
        assert exported.status_code == 200
        assert set(pd.read_excel(io.BytesIO(exported.content))["主机名"]) == {"first", "second"}
    finally:
        app.dependency_overrides.pop(get_db, None)
