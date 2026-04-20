import config
import local_ai
import ha_client


def route(user_input: str, usage_count: int) -> str:
    # Normalize text once so keyword checks are case-insensitive.
    normalized_input = user_input.lower()

    # 1) First priority: detect home assistant intent.
    # If the input looks like a smart-home command, route to home assistant.
    home_assistant_keywords = [
        "turn on",
        "turn off",
        "lock",
        "unlock",
        "set temperature",
    ]
    if any(keyword in normalized_input for keyword in home_assistant_keywords):
        action = local_ai.respond(user_input)
        if action.startswith("ACTION:"):
            return ha_client.execute(action)
    return action

    # 2) Second priority: free tier always uses local AI.
    if config.USER_TIER == "free":
        return local_ai.respond(user_input)

    # 3) Third priority: plus tier over monthly cloud limit uses local AI.
    if (
        config.USER_TIER == "plus"
        and usage_count > config.PLUS_TIER_MONTHLY_CLOUD_AI_REQUEST_LIMIT
    ):
        return local_ai.respond(user_input)

    # 4) Otherwise, default to cloud AI.
    return "Route: Cloud AI layer"
