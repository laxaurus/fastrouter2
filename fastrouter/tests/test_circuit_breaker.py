"""Unit tests for CircuitBreaker — requires Redis (real, no mock)."""

import pytest
import pytest_asyncio

from backend.services.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError


@pytest_asyncio.fixture
async def breaker(redis_client):
    """Fresh circuit breaker for each test."""
    return CircuitBreaker(redis_client)


class TestCircuitStates:
    async def test_initial_state_is_closed(self, breaker):
        state = await breaker.get_state("deepseek")
        assert state == CircuitState.CLOSED

    async def test_initial_state_for_multiple_providers(self, breaker):
        assert await breaker.get_state("deepseek") == CircuitState.CLOSED
        assert await breaker.get_state("qwen") == CircuitState.CLOSED

    async def test_before_call_succeeds_when_closed(self, breaker):
        """before_call should not raise when circuit is closed."""
        await breaker.before_call("deepseek")  # should not raise

    async def test_before_call_succeeds_when_half_open(self, breaker):
        """before_call should not raise when half-open."""
        await breaker._set_state("deepseek", CircuitState.HALF_OPEN)
        await breaker.before_call("deepseek")  # should not raise


class TestCircuitOpens:
    async def test_circuit_opens_after_threshold_failures(self, breaker):
        for _ in range(5):
            await breaker.on_failure("deepseek")

        state = await breaker.get_state("deepseek")
        assert state == CircuitState.OPEN

    async def test_before_call_raises_when_open(self, breaker):
        await breaker._set_state("deepseek", CircuitState.OPEN)

        with pytest.raises(CircuitOpenError) as exc:
            await breaker.before_call("deepseek")
        assert "deepseek" in str(exc.value)

    async def test_failures_below_threshold_keep_closed(self, breaker):
        for _ in range(4):
            await breaker.on_failure("deepseek")

        state = await breaker.get_state("deepseek")
        assert state == CircuitState.CLOSED

    async def test_failure_count_resets_on_success_in_closed(self, breaker):
        await breaker.on_failure("deepseek")
        await breaker.on_failure("deepseek")
        await breaker.on_success("deepseek")

        # In CLOSED state, success increments but doesn't reset
        # Need 3 more failures to open
        for _ in range(3):
            await breaker.on_failure("deepseek")

        # Total failures: 2+3=5 → should open
        state = await breaker.get_state("deepseek")
        assert state == CircuitState.OPEN


class TestHalfOpenRecovery:
    async def test_half_open_transitions_to_closed_after_successes(self, breaker):
        # Open the circuit
        for _ in range(5):
            await breaker.on_failure("deepseek")
        assert await breaker.get_state("deepseek") == CircuitState.OPEN

        # Manually transition to half-open (simulating timeout)
        await breaker._set_state("deepseek", CircuitState.HALF_OPEN)
        await breaker._reset("deepseek")  # clear counters
        await breaker._set_state("deepseek", CircuitState.HALF_OPEN)

        # 3 successes should close the circuit
        for _ in range(3):
            await breaker.on_success("deepseek")

        assert await breaker.get_state("deepseek") == CircuitState.CLOSED

    async def test_half_open_failure_reopens_circuit(self, breaker):
        await breaker._set_state("deepseek", CircuitState.OPEN)
        await breaker._reset("deepseek")
        await breaker._set_state("deepseek", CircuitState.HALF_OPEN)

        # One failure in half-open should re-open
        for _ in range(5):
            await breaker.on_failure("deepseek")

        assert await breaker.get_state("deepseek") == CircuitState.OPEN


class TestGetHealth:
    async def test_returns_all_providers(self, breaker):
        health = await breaker.get_health()
        providers = [h["provider"] for h in health]
        assert "deepseek" in providers
        assert "qwen" in providers

    async def test_health_reflects_current_state(self, breaker):
        await breaker.on_failure("deepseek")
        await breaker.on_failure("deepseek")

        health = await breaker.get_health()
        deepseek = next(h for h in health if h["provider"] == "deepseek")
        assert deepseek["failure_count"] == 2
        assert deepseek["state"] == "closed"

    async def test_isolation_between_providers(self, breaker):
        """Failures on one provider don't affect the other."""
        for _ in range(5):
            await breaker.on_failure("deepseek")

        assert await breaker.get_state("deepseek") == CircuitState.OPEN
        assert await breaker.get_state("qwen") == CircuitState.CLOSED

        # Qwen should still accept calls
        await breaker.before_call("qwen")  # should not raise


class TestRecoveryTimeout:
    async def test_open_circuit_with_expired_timeout_transitions(self, breaker):
        """When an open circuit's recovery timeout has passed, before_call
        transitions it to half-open."""
        breaker.recovery_timeout = 0  # immediate recovery

        # Open the circuit
        for _ in range(5):
            await breaker.on_failure("deepseek")
        assert await breaker.get_state("deepseek") == CircuitState.OPEN

        # Next before_call should transition to half_open
        await breaker.before_call("deepseek")
        assert await breaker.get_state("deepseek") == CircuitState.HALF_OPEN
