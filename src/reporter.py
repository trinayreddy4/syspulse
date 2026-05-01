"""SysPulse Reporter — Generate AI-powered health reports.

Reads system data from the collector, sends it to Claude,
and produces a Markdown report saved to reports/.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from anthropic import (
    Anthropic,
    APIError,           # generic API error
    APIConnectionError, # network issues
    RateLimitError,     # too many requests
    APITimeoutError,    # API took too long
    AuthenticationError # bad key
)

from collector import collect_all


# ----- Configuration -----

load_dotenv()
client = Anthropic()

MODEL = "claude-sonnet-4-5"
MAX_OUTPUT_TOKENS = 2000
REPORTS_DIR = Path(__file__).parent.parent / "reports"


# ----- System Prompt -----

SYSTEM_PROMPT = """You are SysPulse, a senior DevOps engineer who writes daily
system health reports for engineering teams. Your reports are scannable,
honest, and action-oriented.

## CRITICAL: Always Check These Fields First

Before writing the report, inspect:
- `logs.total_errors` — if > 0, this is AT LEAST a Warning status
- `logs.total_warnings` — note the count in your summary
- `logs.recent_errors` — these are specific critical events. ALWAYS list the top 3.
- `logs.failed_ssh_attempts` — if > 0, flag as security concern
- `services` — any status != "active" is a problem
- `disk` percent_used — anything > 85% is a warning, > 95% is critical
- `memory.percent_used` — > 90% is critical
- `cpu.usage_percent` — > 85% sustained is concerning

If `logs.total_errors > 0`, you MUST:
1. Mark status as at least ⚠️ Warning (🚨 Critical if errors include "crit" priority)
2. List specific errors in "Critical Issues" section with timestamps
3. Reference them in the Summary

## Your Rules

1. **Never invent data.** Only analyze what's in the provided JSON.
   If a field is missing or shows an error, say so.

2. **Never claim "0 errors" unless `logs.total_errors == 0`.**
   Always cite the number from the JSON directly.

3. **Lead with severity.** Critical issues at the top, healthy status at the bottom.

4. **Be concise.** Short sentences. Use tables.
   No filler like "It's worth noting that..."

5. **Infer causes when possible.** Connect CPU spikes to top processes,
   service failures to log entries, etc.

6. **Use this exact report structure:**

# 🖥️ SysPulse Daily Report — {hostname}
*Generated: {timestamp}*

## 🚦 Status
One line: ✅ Healthy | ⚠️ Warning | 🚨 Critical

## 🔍 Summary
2-3 sentences. MUST mention exact error/warning counts from logs.

## ⚠️ Critical Issues
If logs.total_errors > 0: list top 3 errors with timestamps.
If all quiet: write "None detected."

## 📊 System Metrics
Markdown table: CPU, memory, disk, uptime.

## 🔧 Services
Markdown table. Flag anything not "active".

## 📜 Log Highlights
- Error count: [from logs.total_errors]
- Warning count: [from logs.total_warnings]
- Failed SSH: [from logs.failed_ssh_attempts]
- Top 3 recent_errors with timestamps (if any)

## 💡 Recommendations
Bulleted, actionable. Max 5 items.

## Your Tone
Technical but clear. Specific numbers, not vague ("disk at 90%" not "getting full").
"""

# ----- Core Functions -----

def build_user_prompt(system_data: dict) -> str:
    """Build the user message containing the JSON payload for Claude.

    Args:
        system_data: Dict from collector.collect_all()

    Returns:
        A formatted string ready to send as the user message.
    """
    return (
        "Generate today's health report based on this system snapshot:\n\n"
        "```json\n"
        f"{json.dumps(system_data, indent=2)}\n"
        "```"
    )

LAST_RUN_FILE = Path(__file__).parent.parent / ".last_run"
MIN_INTERVAL_SECONDS = 60   # prevent runs within 60s of each other


def check_rate_limit():
    """Prevent accidental rapid re-runs that could burn through API budget.

    Raises:
        RuntimeError: if the script was run less than MIN_INTERVAL_SECONDS ago.
    """
    if not LAST_RUN_FILE.exists():
        return

    last_run = float(LAST_RUN_FILE.read_text().strip() or 0)
    elapsed = time.time() - last_run

    if elapsed < MIN_INTERVAL_SECONDS:
        wait = int(MIN_INTERVAL_SECONDS - elapsed)
        raise RuntimeError(
            f"⏱️  Last run was {int(elapsed)}s ago. "
            f"Wait {wait}s before running again (safety rail)."
        )


def record_run():
    """Record the current time as the last successful run."""
    LAST_RUN_FILE.write_text(str(time.time()))

def generate_report(system_data: dict) -> tuple[str, object]:
    """Send system data to Claude and return the generated Markdown report.

    Args:
        system_data: Output from collect_all().

    Returns:
        Tuple of (markdown_text, usage_object).

    Raises:
        RuntimeError: if the API call fails after handling.
    """
    user_prompt = build_user_prompt(system_data)

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=60.0,   # ← NEW: 60s SDK-level timeout
        )
        return message.content[0].text, message.usage

    except AuthenticationError:
        raise RuntimeError(
            "❌ Invalid API key. Check ANTHROPIC_API_KEY in your .env file."
        )
    except RateLimitError:
        raise RuntimeError(
            "⏳ Rate limit hit. Wait a minute and try again, "
            "or upgrade your API tier."
        )
    except APITimeoutError:
        raise RuntimeError(
            "⌛ Anthropic API timed out after 60s. Check network or try again."
        )
    except APIConnectionError as e:
        raise RuntimeError(
            f"🌐 Network error reaching Anthropic: {e}. Check internet."
        )
    except APIError as e:
        raise RuntimeError(
            f"❌ Anthropic API error: {e}"
        )


def save_report(markdown: str, hostname: str) -> Path:
    """Save the report to reports/ with a timestamped filename.

    Args:
        markdown: The report content.
        hostname: Used in the filename for multi-server scenarios.

    Returns:
        The Path object of the saved file.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_{hostname}_syspulse.md"
    filepath = REPORTS_DIR / filename
    filepath.write_text(markdown, encoding="utf-8")
    return filepath


def validate_report(markdown: str, system_data: dict) -> list[str]:
    """Sanity-check the LLM output against the actual system data.

    Catches common hallucinations by comparing key facts in the report
    against ground truth from the collector JSON.

    Args:
        markdown: The report text Claude generated.
        system_data: The raw dict from collect_all().

    Returns:
        List of warning strings. Empty list = report looks faithful.
    """
    warnings = []
    lower_md = markdown.lower()

    logs = system_data.get("logs", {})
    errors = logs.get("total_errors", 0)

    # Check 1: Error count lies
    if errors > 0 and ("0 errors" in lower_md or "no errors detected" in lower_md):
        warnings.append(
            f"Report claims no errors, but logs.total_errors = {errors}"
        )

    # Check 2: Failed SSH attempts lies
    ssh_failures = logs.get("failed_ssh_attempts", 0)
    if ssh_failures > 0 and "no unauthorized access" in lower_md:
        warnings.append(
            f"Report claims no SSH issues, but failed_ssh_attempts = {ssh_failures}"
        )

    # Check 3: Non-active services should be mentioned
    services = system_data.get("services", {})
    for name, info in services.items():
        status = info.get("status")
        if status and status != "active" and name.lower() not in lower_md:
            warnings.append(
                f"Service '{name}' is '{status}' but not mentioned in report"
            )

    # Check 4: High disk usage should be mentioned
    for disk in system_data.get("disk", []):
        pct = disk.get("percent_used", 0)
        mount = disk.get("mount", "")
        if pct > 85 and mount not in markdown:
            warnings.append(
                f"Disk {mount} at {pct}% usage not mentioned in report"
            )

    return warnings

# ----- Main Entry Point -----

from pricing import calculate_cost

def main():
    # Safety rail
    try:
        check_rate_limit()
    except RuntimeError as e:
        print(e)
        return

    print("🔍 Collecting system data...")
    system_data = collect_all()

    print("🤖 Sending to Claude...")
    try:
        report_md, usage = generate_report(system_data)
    except RuntimeError as e:
        print(f"\n{e}")
        return

    # Validation
    validation_warnings = validate_report(report_md, system_data)

    hostname = system_data.get("metadata", {}).get("hostname", "unknown")
    filepath = save_report(report_md, hostname)

    # Record successful run for rate limiting
    record_run()

    # Cost tracking
    cost = calculate_cost(MODEL, usage.input_tokens, usage.output_tokens)

    # Output summary
    if validation_warnings:
        print("\n⚠️  VALIDATION WARNINGS:")
        for w in validation_warnings:
            print(f"   • {w}")
    else:
        print("\n✅ Report passed validation checks")

    print(f"\n📄 Report saved: {filepath}")
    print(f"📊 Tokens: input={usage.input_tokens}, output={usage.output_tokens}")
    print(f"💰 Cost: ${cost:.4f}")
    print("\n" + "=" * 60)
    print(report_md)
    print("=" * 60)


if __name__ == "__main__":
    main()