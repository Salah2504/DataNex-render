def detect_injection(prompt):
    patterns = [
        "ignore previous instructions",
        "bypass",
        "system prompt",
        "act as admin",
        "drop table",
    ]
    return any(x in prompt.lower() for x in patterns)