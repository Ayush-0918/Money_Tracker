from app.services.ai_service import CircuitBreaker, ProviderMetrics


def test_provider_metrics_recording():
    metrics = ProviderMetrics()
    assert metrics.success_count == 0
    assert metrics.failure_count == 0

    metrics.record_success(0.5)
    metrics.record_success(1.5)
    metrics.record_failure()

    assert metrics.success_count == 2
    assert metrics.failure_count == 1

    summary = metrics.get_summary()
    assert summary["success_count"] == 2
    assert summary["failure_count"] == 1
    assert summary["avg_latency_seconds"] == 1.0


def test_circuit_breaker_transitions():
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.1)

    # Initial state
    assert cb.state == "CLOSED"
    assert cb.allow_request() is True

    # Record 2 failures -> should remain closed
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "CLOSED"
    assert cb.allow_request() is True

    # 3rd failure -> should open
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.allow_request() is False

    # Wait for cooldown to expire
    import time

    time.sleep(0.15)

    # Should transition to HALF_OPEN when request allowed
    assert cb.allow_request() is True
    assert cb.state == "HALF_OPEN"

    # Successful request -> close circuit
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.allow_request() is True
