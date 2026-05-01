"""Anthropic API pricing (update as official prices change).

All prices are in USD per million tokens.
"""

PRICING = {
    "claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
    },
    "claude-haiku-4-5": {
        "input": 1.00,   # cheaper, for non-critical tasks
        "output": 5.00,
    },
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the USD cost of a single API call.

    Args:
        model: Model identifier (e.g., "claude-sonnet-4-5").
        input_tokens: Number of input tokens consumed.
        output_tokens: Number of output tokens generated.

    Returns:
        Cost in USD as a float. Returns 0.0 if model unknown.
    """
    if model not in PRICING:
        return 0.0

    rates = PRICING[model]
    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    return input_cost + output_cost