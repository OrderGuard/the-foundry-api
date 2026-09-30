def mask_token(token):
    if not token:
        return "None"
    return token[:6] + "..." + token[-4:]


def sanitize_payload(payload):
    """Remove or mask sensitive fields before logging"""
    safe_payload = payload.copy()

    if "cardToken" in safe_payload:
        safe_payload["cardToken"] = "***"

    if "metadata" in safe_payload:
        safe_payload["metadata"] = "***"

    return safe_payload

