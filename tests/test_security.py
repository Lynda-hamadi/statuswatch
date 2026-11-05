import socket

import pytest
from fastapi.testclient import TestClient

from app import checker, security
from app.main import app
from app.models import Target

client = TestClient(app)


def resolver_to(ip, family=socket.AF_INET):
    address = (ip, 0) if family == socket.AF_INET else (ip, 0, 0, 0)
    return lambda host, port, *a, **k: [(family, socket.SOCK_STREAM, 6, "", address)]


@pytest.mark.parametrize(
    "ip", ["127.0.0.1", "10.0.0.5", "192.168.1.10", "172.16.0.1", "169.254.169.254"]
)
def test_adresses_internes_refusees(monkeypatch, ip):
    monkeypatch.setattr(security.socket, "getaddrinfo", resolver_to(ip))
    with pytest.raises(security.UnsafeTarget):
        security.assert_public_url("http://exemple.test")


def test_adresse_publique_acceptee(monkeypatch):
    monkeypatch.setattr(security.socket, "getaddrinfo", resolver_to("93.184.216.34"))
    security.assert_public_url("http://exemple.test")


def test_ipv6_cachant_une_adresse_interne_refusee(monkeypatch):
    monkeypatch.setattr(
        security.socket, "getaddrinfo", resolver_to("::ffff:127.0.0.1", socket.AF_INET6)
    )
    with pytest.raises(security.UnsafeTarget):
        security.assert_public_url("http://exemple.test")


def test_api_refuse_une_cible_interne(db, monkeypatch):
    monkeypatch.setattr(security.socket, "getaddrinfo", resolver_to("169.254.169.254"))
    response = client.post(
        "/targets", json={"name": "Metadata", "url": "http://exemple.test/latest"}
    )
    assert response.status_code == 422


def test_le_verificateur_ne_contacte_pas_une_cible_interne(db, monkeypatch):
    monkeypatch.setattr(security.socket, "getaddrinfo", resolver_to("127.0.0.1"))

    def must_not_be_called(*args, **kwargs):
        raise AssertionError("requête réseau envoyée vers une cible interne")

    monkeypatch.setattr(checker.httpx, "get", must_not_be_called)

    target = Target(name="Interne", url="http://localhost:9999", interval_seconds=60)
    db.add(target)
    db.commit()
    db.refresh(target)

    check = checker.run_check(db, target)
    assert check.is_up is False
    assert "refusée" in check.error