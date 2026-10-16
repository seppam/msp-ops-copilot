"""Step 2: the tool-calling loop, written by hand with no framework.

Loop: ask the model -> if it requests tools, run them and append results ->
ask again -> stop when it answers in plain text. Every agent framework is a
variation of this loop.
"""

import json
import sys

from msp_ops_copilot.llm import get_client
from msp_ops_copilot.tools import REGISTRY, SCHEMAS

MAX_STEPS = 6  # safety stop so a confused model cannot loop forever


def run(question: str) -> str:
    client, model = get_client()
    messages = [
        {"role": "system", "content": "You are an IT service desk assistant. Use tools to look up tickets; never invent ticket data."},
        {"role": "user", "content": question},
    ]
    for step in range(1, MAX_STEPS + 1):
        reply = client.chat.completions.create(
            model=model, messages=messages, tools=SCHEMAS, max_tokens=800
        ).choices[0].message
        messages.append(reply)
        if not reply.tool_calls:
            return reply.content
        for call in reply.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
                print(f"[step {step}] model asked for {name}({args})")
                if name not in REGISTRY:
                    result = {"error": f"unknown tool '{name}'", "available": list(REGISTRY)}
                else:
                    result = REGISTRY[name](**args)
            except Exception as exc:  # bad JSON, wrong arguments, tool crash
                # Report the problem back to the model instead of crashing,
                # so it can correct itself on the next step.
                result = {"error": f"{type(exc).__name__}: {exc}"}
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )
    return "Stopped: too many tool steps."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which open tickets look urgent, and why?"
    print(run(q))
