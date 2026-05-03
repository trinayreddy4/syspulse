# 🖥️ SysPulse

**AI-powered Linux system health monitoring with defensive prompt engineering.**

SysPulse collects system metrics, logs, and service status from a Linux server,
then uses Claude (Anthropic's LLM) to generate a daily Markdown health report
with triaged severity, pattern analysis, and actionable recommendations.

Built with safety rails, output validation, and cost tracking — because
production AI needs more than just API calls.

---

## 🎥 Sample Report

<details>
<summary>Click to expand a real generated report</summary>

\`\`\`markdown
# 🖥️ SysPulse Daily Report — localhost.localdomain
*Generated: 2026-05-01 05:03:26*

## 🚦 Status
🚨 **Critical**

## 🔍 Summary
System is experiencing repeated critical service crashes with core dumps.
Detected 15 errors (including 7 critical-priority events) and 45 warnings.
Multiple systemd services hitting watchdog timeouts every ~5 minutes...

## ⚠️ Critical Issues
1. systemd-udevd (PID 6510) dumped core after watchdog timeout
2. systemd-logind (PID 1196) dumped core
...
\`\`\`

</details>

---

## ✨ Features

- 📊 **Metric Collection** — CPU, memory, disk, processes, uptime, services
- 📜 **Log Analysis** — Extracts errors/warnings from `journalctl` (24h window)
- 🤖 **AI Narrative** — Claude generates structured Markdown with root-cause inference
- 🛡️ **Output Validation** — Fact-checks AI claims against source data
- 💰 **Cost Tracking** — Reports USD cost per run
- ⏱️ **Rate Limiting** — Prevents accidental API budget burn
- 🔒 **Security-First** — No hardcoded secrets, input-sanitized subprocess calls

---

## 🚀 Quickstart

\`\`\`bash
# Clone
git clone https://github.com/YOUR_USERNAME/syspulse.git
cd syspulse

# Set up venv
python3 -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run
cd src
python reporter.py
\`\`\`

---

## 🏗️ Architecture

\`\`\`
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   collector  │─────▶│   reporter   │─────▶│  Claude API  │
│   (psutil,   │      │  (prompt +   │      │              │
│  subprocess) │      │  validator)  │◀─────│              │
└──────────────┘      └──────────────┘      └──────────────┘
      │                     │
      ▼                     ▼
  Raw JSON            reports/*.md
\`\`\`

**Defense-in-depth layers:**
1. **Data quality** — collector filters virtual filesystems, kernel threads, self-process
2. **Prompt engineering** — explicit field references, deterministic severity rules
3. **Output validation** — regex-checks PIDs, CPU%, service mentions against JSON
4. **Cost safety** — rate-limit file prevents runaway loops

---

## 🧪 Tech Stack

**Language:** Python 3.10+
**Libraries:** `psutil`, `anthropic`, `python-dotenv`
**Platform:** Linux with `systemd` (tested on CentOS Stream 10)
**AI Model:** Claude Sonnet 4.5

---

## 📂 Project Structure

\`\`\`
syspulse/
├── src/
│   ├── collector.py      # Gathers system metrics + logs
│   ├── reporter.py       # AI report generator
│   └── pricing.py        # API cost calculation
├── reports/              # Generated Markdown reports (gitignored)
├── requirements.txt
├── .env.example
└── README.md
\`\`\`

---

## 🗺️ Roadmap

- [x] **Day 1** — Metric collector (CPU, memory, disk, processes, services, logs)
- [x] **Day 2** — AI reporter (Claude integration, validation, cost tracking)
- [ ] **Day 3** — Slack notifications + EC2 deployment + cron schedule
- [ ] **Day 4** — Documentation + launch

---

## 💡 Engineering Notes

This project was built with a focus on **trustworthy AI output**, not just
working AI output. Key lessons learned:

- **Observer effect** — monitoring tools measure themselves; collector excludes own PID
- **Confabulation risk** — LLMs invent plausible details; validator catches numeric hallucinations
- **Debugging hierarchy** — 90% of "AI bugs" are data bugs; always verify input first
- **Defense in depth** — prompt + validator + rate limit = production-grade reliability

---

## ✨ Features

- 📊 **Metric Collection** — CPU, memory, disk, processes, uptime, services
- 📜 **Log Analysis** — Extracts errors/warnings from `journalctl` (24h window)
- 🤖 **AI Narrative** — Claude generates structured Markdown with root-cause inference
- 🛡️ **Output Validation** — Fact-checks AI claims against source data
- 💰 **Cost Tracking** — Reports USD cost per run
- ⏱️ **Rate Limiting** — Prevents accidental API budget burn
- 💬 **Slack Notifications** — Posts triage summary to a Slack channel
- ⏰ **Scheduled Runs** — Cron-based daily execution
- ☁️ **Cloud-Ready** — Deploys to AWS EC2 with hardened user model
- 🔒 **Security-First** — No hardcoded secrets, least-privilege user, input-sanitized subprocess calls


## ☁️ Production Deployment

SysPulse runs on AWS EC2 with the following production patterns:

### Infrastructure
- **Instance:** Amazon Linux 2023, t3.micro (free tier eligible)
- **User model:** Dedicated `syspulse` user with no sudo (least privilege)
- **Secrets:** `.env` file with 600 permissions (production upgrade: AWS Secrets Manager)
- **Firewall:** Security Group restricts SSH to known IP only

### Scheduling
\`\`\`cron
# Daily report at 9 AM IST
0 9 * * * cd /home/syspulse/syspulse && venv/bin/python src/reporter.py >> logs/syspulse.log 2>&1
\`\`\`

### Observability
- Slack webhook posts triage summary to `#syspulse` channel
- Full Markdown reports saved to `reports/` directory
- Cron output captured in `logs/syspulse.log`
- Cost tracked and shown in every run

### Cost Profile
- Per report: ~$0.02 (Claude Sonnet 4.5)
- Monthly (daily cadence): ~$0.60
- EC2 compute: ~$0 (free tier) or ~$7.50/mo (t3.micro on-demand)

## 💡 Engineering Notes

This project was built with a focus on **trustworthy AI output**, not just
working AI output. Key lessons learned:

- **Observer effect** — monitoring tools measure themselves; collector excludes own PID
- **Confabulation risk** — LLMs invent plausible details; validator catches numeric hallucinations
- **Debugging hierarchy** — 90% of "AI bugs" are data bugs; always verify input first
- **Defense in depth** — prompt + validator + rate limit = production-grade reliability
- **Graceful degradation** — Slack outage doesn't crash the reporter; notifications are logged, not required
- **Dev-prod parity** — venv with explicit Python version prevents "works on my machine" drift
- **Least privilege** — dedicated service user + IP-restricted SSH = attack surface minimized

## 📜 License

MIT — see [LICENSE](./LICENSE)