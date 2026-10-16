from msp_ops_copilot import rag, triage


def test_chunks_split_at_headings_and_keep_the_document_title():
    chunks = rag.chunk(rag.KB_DIR / "runbook-vpn.md")
    assert len(chunks) == 2
    assert all(text.startswith("VPN Troubleshooting Runbook / ") for _, text in chunks)


def test_search_finds_the_right_runbook_and_ranks_irrelevant_far_away():
    rag.ingest()
    best = rag.search("VPN authentication failed for several users", k=1)[0]
    assert best["source"] == "runbook-vpn.md" and best["distance"] < triage.MAX_DISTANCE
    assert rag.search("what is the lunch menu", k=1)[0]["distance"] > triage.MAX_DISTANCE


def test_policy_for_always_includes_the_triage_policy():
    hits = triage.policy_for({"subject": "Cannot connect to VPN", "description": "auth failed"})
    assert any(h["source"] == "triage-policy.md" for h in hits)
