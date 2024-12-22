

@cache.memoize(typed=True)
def query_to_claude_internal(
    prompt: str, stop_sequences: frozenset = None, extraData=None, prefill: str = None, system_message: str = None
):
    api_key = sellerinfo.CLAUDE_API_KEY
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "anthropic-version": "2023-06-01",
    }

    messages = [{"role": "user", "content": prompt}]

    if prefill:
        messages.append({"role": "assistant", "content": prefill})

    data = {
        "messages": messages,
        "max_tokens": 2024,
        "model": "claude-3-5-sonnet-20241022",
    }

    if system_message:
        data["system"] = system_message

    if not extraData:
        extraData = {}
    extraData = dict(extraData)
    if extraData.get("timeout"):
        timeout = extraData["timeout"]
    else:
        timeout = 30

    response = requests.post(url, headers=headers, json=data, timeout=timeout)
    response.raise_for_status()

    generated_text = response.json()["content"][0]["text"]

    if stop_sequences:
        for stop_seq in stop_sequences:
            if stop_seq in generated_text:
                generated_text = generated_text[: generated_text.index(stop_seq)]

    return generated_text
        return None