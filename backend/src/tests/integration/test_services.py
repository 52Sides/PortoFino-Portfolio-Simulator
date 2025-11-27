import httpx
import pytest
import socket


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint(async_client):
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}"
    assert "http_requests_total" in resp.text or "http_server_requests_total" in resp.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prometheus_available():
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.get("http://prometheus:9090/api/v1/status/config")
        except Exception as e:
            pytest.skip(f"Prometheus not reachable: {e}")
        else:
            assert resp.status_code == 200
            assert "data" in resp.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_and_kafka_ports_open():
    for host, port in [("redis", 6379), ("kafka", 9092)]:
        try:
            s = socket.create_connection((host, port), timeout=2)
            s.close()
        except OSError:
            pytest.skip(f"{host}:{port} not available in current test env")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health(test_client):
    r = await test_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
