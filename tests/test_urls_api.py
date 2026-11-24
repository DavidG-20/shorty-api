"""End-to-end API tests for shorty-api (shortening, redirects, stats, and rate limiting)."""

from fastapi.testclient import TestClient

from shorty_api.services.rate_limiter import rate_limiter


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_shorten_with_random_code_and_redirect_records_analytics(
    client: TestClient,
) -> None:
    create_resp = client.post(
        "/api/v1/shorten",
        json={"url": "https://docs.python.org/3/"},
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    code = body["short_code"]
    assert len(code) == 6
    assert body["original_url"] == "https://docs.python.org/3/"

    # Simulate two clicks from different devices and referers
    r1 = client.get(
        f"/{code}",
        follow_redirects=False,
        headers={
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile",
            "referer": "https://github.com",
        },
    )
    assert r1.status_code == 307
    assert r1.headers["location"] == "https://docs.python.org/3/"

    r2 = client.get(
        f"/{code}",
        follow_redirects=False,
        headers={"user-agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/128.0"},
    )
    assert r2.status_code == 307

    stats_resp = client.get(f"/api/v1/stats/{code}")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_clicks"] == 2
    assert stats["clicks_by_device"] == {"mobile": 1, "desktop": 1}
    assert stats["top_referers"]["https://github.com"] == 1
    assert stats["top_referers"]["direct"] == 1
    assert stats["last_clicked_at"] is not None


def test_custom_alias_and_duplicate_conflict(client: TestClient) -> None:
    first = client.post(
        "/api/v1/shorten",
        json={"url": "https://github.com/DavidG-20", "custom_alias": "mi-perfil"},
    )
    assert first.status_code == 201
    assert first.json()["short_code"] == "mi-perfil"

    duplicate = client.post(
        "/api/v1/shorten",
        json={"url": "https://example.com", "custom_alias": "mi-perfil"},
    )
    assert duplicate.status_code == 409


def test_reserved_alias_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/shorten",
        json={"url": "https://example.com", "custom_alias": "health"},
    )
    assert response.status_code == 400


def test_invalid_url_rejected_with_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/shorten",
        json={"url": "javascript:alert(1)"},
    )
    assert response.status_code == 422


def test_unknown_code_returns_404(client: TestClient) -> None:
    assert client.get("/no-existe", follow_redirects=False).status_code == 404
    assert client.get("/api/v1/stats/no-existe").status_code == 404


def test_rate_limiter_blocks_excess_requests_with_429(client: TestClient) -> None:
    original_max = rate_limiter.max_requests
    rate_limiter.max_requests = 2
    try:
        for idx in range(2):
            ok_resp = client.post(
                "/api/v1/shorten",
                json={"url": f"https://example.com/{idx}"},
            )
            assert ok_resp.status_code == 201

        blocked = client.post(
            "/api/v1/shorten",
            json={"url": "https://example.com/blocked"},
        )
        assert blocked.status_code == 429
        assert "retry-after" in blocked.headers
    finally:
        rate_limiter.max_requests = original_max
