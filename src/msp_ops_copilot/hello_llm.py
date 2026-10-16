"""Step 1: prove the key works with the smallest possible LLM call."""

from msp_ops_copilot.llm import get_client


def main() -> None:
    client, model = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with one short sentence: what is an MSP?"}],
        max_tokens=200,
    )
    print(f"model: {model}")
    print(response.choices[0].message.content)
    print(f"tokens used: {response.usage.total_tokens}")


if __name__ == "__main__":
    main()
