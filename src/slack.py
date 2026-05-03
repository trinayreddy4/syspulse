"""Slack integration for SysPulse.

Posts a triage summary (not the full report) to a Slack webhook.
Designed to fail gracefully — a Slack outage should never block
report generation.
"""

import json
import os
import re
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
REQUEST_TIMEOUT = 10  # seconds


# ----- Parsing helpers -----

def extract_section(markdown: str, heading: str) -> str:
    """Extract the body of a Markdown section by its heading.

    Args:
        markdown: Full report text.
        heading: Section heading to match (e.g., "Summary", "Critical Issues").

    Returns:
        Section body as a string, or empty string if not found.
    """
    # Match `## <emoji?> Heading` up to the next `## ` or end
    pattern = rf"##\s+[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    return match.group(1).strip() if match else ""


def detect_status(markdown: str) -> tuple[str, str]:
    """Parse the Status section to get a color and label.

    Returns:
        (color, label) where color is a Slack-compatible hex.
    """
    status_body = extract_section(markdown, "Status").lower()

    if "critical" in status_body or "🚨" in status_body:
        return ("#DC2626", "🚨 Critical")
    if "warning" in status_body or "⚠️" in status_body:
        return ("#F59E0B", "⚠️ Warning")
    return ("#10B981", "✅ Healthy")


# ----- Payload builder -----

def build_slack_payload(
    markdown: str,
    hostname: str,
    cost: float,
    report_path: str = "",
) -> dict:
    """Build a Slack message payload using Block Kit.

    Args:
        markdown: The full Claude-generated report.
        hostname: Server hostname for the title.
        cost: USD cost of this report run.
        report_path: Optional local path to full report.

    Returns:
        Dict ready to POST as JSON to the webhook.
    """
    color, status_label = detect_status(markdown)
    summary = extract_section(markdown, "Summary") or "_No summary available_"
    critical = extract_section(markdown, "Critical Issues") or "_None detected_"

    # Slack limits blocks to ~3000 chars per field; trim if needed
    critical_trimmed = critical[:2800] + ("..." if len(critical) > 2800 else "")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"SysPulse — {hostname}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n{status_label}"},
                {"type": "mrkdwn", "text": f"*Cost:*\n`${cost:.4f}`"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary*\n{summary}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Critical Issues*\n{critical_trimmed}",
            },
        },
    ]

    if report_path:
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"📄 Full report: `{report_path}`"}
            ],
        })

    return {
        "attachments": [
            {
                "color": color,
                "blocks": blocks,
            }
        ]
    }


# ----- Sender -----

def send_to_slack(payload: dict) -> tuple[bool, str]:
    """POST a payload to the Slack webhook.

    Args:
        payload: Dict matching Slack's webhook schema.

    Returns:
        (success, message) — True if HTTP 200, False otherwise.
    """
    if not WEBHOOK_URL:
        return (False, "SLACK_WEBHOOK_URL not configured in .env")

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            if resp.status == 200 and body == "ok":
                return (True, "Posted to Slack")
            return (False, f"Unexpected response: {resp.status} {body}")

    except urllib.error.URLError as e:
        return (False, f"Network error posting to Slack: {e}")
    except Exception as e:
        return (False, f"Unexpected error: {e}")


# ----- Public API -----

def notify(markdown: str, hostname: str, cost: float, report_path: str = "") -> None:
    """Send report summary to Slack. Errors are logged, not raised.

    This is the main entry point used by reporter.py.
    """
    payload = build_slack_payload(markdown, hostname, cost, report_path)
    success, message = send_to_slack(payload)

    if success:
        print(f"💬 {message}")
    else:
        print(f"⚠️  Slack notification failed: {message}")