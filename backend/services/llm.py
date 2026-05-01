import os
from groq import Groq

_client: Groq | None = None

MODEL = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def chat(
    system: str,
    user: str,
    messages: list[dict] | None = None,
    max_tokens: int = 512,
    temperature: float = 0.5,
) -> str:
    """
    Single helper that all agents use.
    Merges system + history + user into the messages array Groq expects.
    Returns the response text string.
    """
    client = get_client()
    built: list[dict] = [{"role": "system", "content": system}]
    if messages:
        built.extend(messages)
    built.append({"role": "user", "content": user})

    completion = client.chat.completions.create(
        model=MODEL,
        messages=built,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return completion.choices[0].message.content.strip()
