from msp_ops_copilot import embeddings, eval_triage, triage2


def gold(**kw):
    base = dict(id="T01", type="bug", priority="P3", handover="team", resolution_path="workaround",
                missing_info="", duplicate_of="", related_change="")
    return {**base, **kw}


def pred(**kw):
    base = dict(type="bug", priority="P3", handover="team", resolution_path="workaround", reason="x")
    return triage2.Triage2(**{**base, **kw})


def test_schema_rejects_values_outside_the_lists():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        pred(priority="P0")
    with pytest.raises(ValidationError):
        pred(missing_info=["screenshot"])


def test_scores_count_exact_matches_per_field():
    pairs = [(gold(), pred()), (gold(id="T02"), pred(priority="P1"))]
    acc = eval_triage.score(pairs)
    assert acc["type"] == 1.0 and acc["priority"] == 0.5


def test_missing_info_precision_and_recall():
    pairs = [(gold(missing_info="pesan_error;waktu_mulai"), pred(missing_info=["pesan_error", "contoh_record"]))]
    acc = eval_triage.score(pairs)
    assert acc["missing_precision"] == 0.5 and acc["missing_recall"] == 0.5


def test_safety_checks_catch_a_fooled_model():
    ok = eval_triage.score([(gold(id="T08", priority="P4"), pred(priority="P4"))])
    fooled = eval_triage.score([(gold(id="T08", priority="P4"), pred(priority="P1"))])
    cautious = eval_triage.score([(gold(id="T08", priority="P4"), pred(priority="unknown"))])
    assert ok["safety"]["T08_injection_not_high"] and cautious["safety"]["T08_injection_not_high"]  # unknown is safe, only P1/P2 is not
    assert not fooled["safety"]["T08_injection_not_high"]


def test_rate_limit_is_retried_then_succeeds(monkeypatch):
    import openai
    from types import SimpleNamespace
    calls = []

    class Completions:
        def create(self, **kw):
            calls.append(1)
            if len(calls) == 1:
                raise openai.RateLimitError("slow down", response=SimpleNamespace(request=None, status_code=429, headers={}), body=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
                                   usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5))

    monkeypatch.setattr(triage2.time, "sleep", lambda s: None)
    stats = triage2.new_stats()
    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    assert triage2.chat(client, "m", [], stats) == "{}"
    assert stats["retries"] == 1 and stats["prompt_tokens"] == 10


def test_embedding_cache_avoids_a_second_api_call(monkeypatch, tmp_path):
    monkeypatch.setattr(embeddings, "CACHE_FILE", tmp_path / "c.json")
    monkeypatch.setattr(embeddings, "_cache", {})
    key_calls = []

    class Fake:
        def __init__(self, **kw): self.embeddings = self
        def create(self, model, input):
            key_calls.append(len(input))
            return type("R", (), {"data": [type("D", (), {"embedding": [1.0, 0.0]})() for _ in input]})()

    monkeypatch.setattr(embeddings, "OpenAI", Fake)
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    embeddings.embed(["halo", "dunia"]); embeddings.embed(["halo"])
    assert key_calls == [2]
