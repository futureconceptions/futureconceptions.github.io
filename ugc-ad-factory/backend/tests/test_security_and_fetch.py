import socket

import httpx
import pytest
import respx

from app.core.security import sign_path, verify_signed_path, webhook_token
from app.services.safe_fetch import UnsafeURLError, robots_allows, safe_get, validate_url
from app.services.storage import LocalStorage


def fake_resolver(ip):
    def _r(host, port, proto=None):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]
    return _r


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/x", "http://user:pw@example.com/",
                                 "http://example.com:22/"])
def test_validate_url_rejects_bad_schemes_and_ports(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url, resolver=fake_resolver("93.184.216.34"))


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "100.64.1.1", "::1",
                                "0.0.0.0"])
def test_validate_url_blocks_private_addresses(ip):
    with pytest.raises(UnsafeURLError):
        validate_url("http://internal.example/", resolver=fake_resolver(ip))


def test_validate_url_allows_public():
    assert validate_url("https://shop.example.com/p", resolver=fake_resolver("93.184.216.34"))


@respx.mock
def test_redirect_to_private_host_is_blocked(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda h, p, proto=None: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1" if h == "evil.local" else "93.184.216.34", p))])
    respx.get("https://shop.example.com/p").mock(return_value=httpx.Response(302, headers={"location": "http://evil.local/admin"}))
    with pytest.raises(UnsafeURLError):
        safe_get("https://shop.example.com/p")


@respx.mock
def test_robots_disallow(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda h, p, proto=None: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", p))])
    respx.get("https://shop.example.com/robots.txt").mock(return_value=httpx.Response(
        200, text="User-agent: *\nDisallow: /private/\n"))
    assert robots_allows("https://shop.example.com/products/a")
    assert not robots_allows("https://shop.example.com/private/a")


@respx.mock
def test_missing_robots_is_allowed_server_error_is_not(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda h, p, proto=None: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", p))])
    respx.get("https://a.example.com/robots.txt").mock(return_value=httpx.Response(404))
    respx.get("https://b.example.com/robots.txt").mock(return_value=httpx.Response(503))
    assert robots_allows("https://a.example.com/x")
    assert not robots_allows("https://b.example.com/x")


def test_signed_paths_and_traversal(tmp_path):
    exp, sig = sign_path("projects/a.mp4", ttl=60)
    assert verify_signed_path("projects/a.mp4", exp, sig)
    assert not verify_signed_path("projects/b.mp4", exp, sig)
    assert not verify_signed_path("projects/a.mp4", exp - 120, sig)
    st = LocalStorage(str(tmp_path))
    with pytest.raises(ValueError):
        st.put_bytes("../../etc/x", b"1")
    assert webhook_token("job1") != webhook_token("job2")


def test_signed_file_endpoint(client):
    from app.services.storage import get_storage
    st = get_storage()
    st.put_bytes("projects/p/x.txt", b"hello")
    url = st.signed_url("projects/p/x.txt").replace("http://testserver", "")
    assert client.get(url).content == b"hello"
    assert client.get(url.replace("sig=", "sig=0")).status_code == 403
    assert client.get("/api/files/projects/p/x.txt?exp=1&sig=abc").status_code == 403


def test_endpoints_require_auth(client):
    for path in ("/api/projects", "/api/dashboard", "/api/creators", "/api/exports", "/api/settings"):
        assert client.get(path).status_code == 401


def test_viewer_cannot_write(client, auth):
    client.post("/api/users", headers=auth, json={"email": "v@example.com", "password": "viewer123", "role": "viewer"})
    tok = client.post("/api/auth/login", json={"email": "v@example.com", "password": "viewer123"}).json()["access_token"]
    r = client.post("/api/creators", headers={"Authorization": f"Bearer {tok}"}, json={"name": "x"})
    assert r.status_code == 403


def test_settings_never_expose_secrets(client, auth):
    body = client.get("/api/settings", headers=auth).json()
    flat = str(body).lower()
    assert "api_key" not in flat and "secret" not in flat
    assert body["effective"]["letzai_configured"] is False
