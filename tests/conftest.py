"""Shared fakes. No test here talks to a real LLM or to Odoo."""

from types import SimpleNamespace

import pytest


class FakeLLM:
    """Stands in for the OpenAI client. Replies come from a scripted list, one per call."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Copy the messages: the caller keeps appending to the same list afterwards.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        message = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def text_reply(content):
    return SimpleNamespace(content=content, tool_calls=None)


def tool_reply(name, arguments="{}", call_id="call_1"):
    call = SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(content=None, tool_calls=[call])


@pytest.fixture
def fake_llm(monkeypatch):
    """Usage: llm = fake_llm([...replies]); the module under test gets this client."""

    def install(replies, *modules):
        llm = FakeLLM(replies)
        for module in modules:
            monkeypatch.setattr(module, "get_client", lambda: (llm, "fake-model"))
        return llm

    return install
