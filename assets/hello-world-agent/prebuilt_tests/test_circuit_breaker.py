"""Tests for the per-model circuit breaker and the breaker-aware fallback chain."""
# pyright: reportMissingImports=false

import pytest

pytestmark = pytest.mark.structure


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class TestCircuitBreaker:
    async def test_unknown_model_is_allowed(self, add_agent_to_path):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker()
        assert await breaker.allows("m") is True

    async def test_opens_only_at_threshold(self, add_agent_to_path):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        await breaker.record_failure("m")
        await breaker.record_failure("m")
        assert await breaker.allows("m") is True
        await breaker.record_failure("m")
        assert await breaker.allows("m") is False

    async def test_success_resets_failure_streak(self, add_agent_to_path):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        await breaker.record_failure("m")
        await breaker.record_failure("m")
        await breaker.record_success("m")
        await breaker.record_failure("m")
        await breaker.record_failure("m")
        assert await breaker.allows("m") is True

    async def test_cooldown_elapses_to_half_open_probe(self, add_agent_to_path):
        from circuit_breaker import CircuitBreaker
        clock = _Clock()
        breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=30, time_fn=clock)
        await breaker.record_failure("m")
        assert await breaker.allows("m") is False
        clock.advance(29)
        assert await breaker.allows("m") is False
        clock.advance(1)
        assert await breaker.allows("m") is True

    async def test_models_are_independent(self, add_agent_to_path):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=30)
        await breaker.record_failure("m1")
        assert await breaker.allows("m1") is False
        assert await breaker.allows("m2") is True


class _Transient(Exception):
    pass


class _Fatal(Exception):
    pass


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeGraph:
    def __init__(self, outcomes: list) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    async def ainvoke(self, messages, config):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return {"messages": [_FakeMessage(outcome)]}


def _make_agent(agent_mod, graphs_by_model: dict, breaker):
    inst = object.__new__(agent_mod.SampleAgent)
    chain = list(graphs_by_model.keys())
    inst._primary_model = chain[0]
    inst._breaker = breaker
    inst._model_chain = [(name, name) for name in chain]

    def _create_graph(llm, tools, system_prompt):
        return graphs_by_model[llm]

    inst._create_graph = _create_graph
    return inst


async def _invoke(inst):
    return await inst._invoke_with_fallback(tools=[], system_prompt="sys", query="hi", context_id="c1")


@pytest.fixture
def agent_mod(add_agent_to_path, monkeypatch):
    import agent as agent_mod
    monkeypatch.setattr(agent_mod, "RETRYABLE_ERRORS", (_Transient,))
    monkeypatch.setattr(agent_mod, "get_user_sub", lambda: "user-1")
    return agent_mod


class TestInvokeWithFallbackChain:
    async def test_primary_success_skips_fallbacks(self, agent_mod):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        graphs = {"m0": _FakeGraph(["primary-ok"]), "m1": _FakeGraph(["unused"])}
        inst = _make_agent(agent_mod, graphs, breaker)
        result = await _invoke(inst)
        assert result["messages"][-1].content == "primary-ok"
        assert graphs["m1"].calls == 0

    async def test_transient_failure_advances_to_fallback(self, agent_mod):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        graphs = {"m0": _FakeGraph([_Transient()]), "m1": _FakeGraph(["fallback-ok"])}
        inst = _make_agent(agent_mod, graphs, breaker)
        result = await _invoke(inst)
        assert result["messages"][-1].content == "fallback-ok"

    async def test_non_transient_error_propagates_without_fallback(self, agent_mod):
        from circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
        graphs = {"m0": _FakeGraph([_Fatal()]), "m1": _FakeGraph(["unused"])}
        inst = _make_agent(agent_mod, graphs, breaker)
        with pytest.raises(_Fatal):
            await _invoke(inst)
        assert graphs["m1"].calls == 0
