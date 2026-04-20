"""Home Assistant integration for CORA."""

from __future__ import annotations

import requests
import config

HEADERS = {
    "Authorization": f"Bearer {config.HOME_ASSISTANT_TOKEN}",
    "Content-Type": "application/json",
}


def _parse_action(user_input: str) -> tuple[str, str, dict] | None:
    """Parse ACTION: service | entity | value format."""
    if not user_input.startswith("ACTION:"):
        return None
    parts = user_input.replace("ACTION:", "").strip().split("|")
    if len(parts) < 2:
        return None
    service = parts[0].strip()
    entity = parts[1].strip()
    value = parts[2].strip() if len(parts) > 2 else ""
    data: dict = {"entity_id": entity}
    if "=" in value:
        key, val = value.split("=", 1)
        try:
            data[key.strip()] = int(val.strip())
        except ValueError:
            data[key.strip()] = val.strip()
    return service, entity, data


def execute(user_input: str) -> str:
    """Execute a home assistant action from ACTION format."""
    parsed = _parse_action(user_input)
    if not parsed:
        return "I couldn't understand that command."
    service, entity, data = parsed
    domain = service.split(".")[0]
    service_name = service.split(".")[1] if "." in service else service
    url = f"{config.HOME_ASSISTANT_URL}/api/services/{domain}/{service_name}"
    try:
        response = requests.post(url, headers=HEADERS, json=data, timeout=5)
        if response.status_code == 200:
            return "Done."
        return f"Home Assistant returned error {response.status_code}."
    except requests.exceptions.ConnectionError:
        return "I can't reach Home Assistant right now."
    except requests.exceptions.Timeout:
        return "Home Assistant timed out."


def get_states() -> list[dict]:
    """Return all current device states from Home Assistant."""
    url = f"{config.HOME_ASSISTANT_URL}/api/states"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []