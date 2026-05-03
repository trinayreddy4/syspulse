# 🖥️ SysPulse

**AI-powered Linux system health monitoring with defensive prompt engineering.**

SysPulse collects system metrics, logs, and service health from a Linux server, then uses Claude (Anthropic LLM) to generate a daily Markdown report with severity triage, pattern detection, and actionable insights.

Built with **validation layers, safety rails, and cost awareness** — because production AI needs more than API calls.

---

## 🎥 Sample Report

<details>
<summary><strong>Click to expand a real generated report</strong></summary>

```markdown
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
```

</details>

---

## ✨ Features

* 📊 **Metric Collection** — CPU, memory, disk, processes, uptime, services
* 📜 **Log Analysis** — Parses `journalctl` (last 24h) for warnings/errors
* 🤖 **AI Narrative** — Claude generates structured Markdown reports
* 🛡️ **Output Validation** — Cross-checks AI claims against raw data
* 💰 **Cost Tracking** — Per-run USD visibility
* ⏱️ **Rate Limiting** — Prevents runaway API usage
* 💬 **Slack Notifications** — Sends triage summaries
* ⏰ **Scheduled Runs** — Cron-based automation
* ☁️ **Cloud-Ready** — AWS EC2 deployment ready
* 🔒 **Security-First** — No hardcoded secrets, sanitized inputs

---

## 🚀 Quickstart

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/syspulse.git
cd syspulse

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add ANTHROPIC_API_KEY

# Run
cd src
python reporter.py
```

---

## 🏗️ Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  collector   │─────▶│   reporter   │─────▶│  Claude API  │
│ (psutil +    │      │ (prompt +    │      │              │
│ subprocess)  │      │ validator)   │◀─────│              │
└──────────────┘      └──────────────┘      └──────────────┘
      │                     │
      ▼                     ▼
  Raw JSON            reports/*.md
```

### 🛡️ Defense-in-Depth

1. **Data Quality** — filters kernel threads, virtual FS, self-process
2. **Prompt Design** — explicit fields + deterministic severity rules
3. **Validation Layer** — regex + numeric checks against source data
4. **Cost Safety** — rate limiting prevents runaway loops

---

## 🧪 Tech Stack

* **Language:** Python 3.10+
* **Libraries:** `psutil`, `anthropic`, `python-dotenv`
* **Platform:** Linux (`systemd`) — tested on CentOS Stream 10
* **Model:** Claude Sonnet 4.5

---

## 📂 Project Structure

```
syspulse/
├── src/
│   ├── collector.py
│   ├── reporter.py
│   └── pricing.py
├── reports/              # Generated (gitignored)
├── logs/                 # Runtime logs
├── requirements.txt
├── .env.example
└── README.md
```

---

## ☁️ Production Deployment

### Infrastructure

* **EC2:** Amazon Linux 2023 (t3.micro)
* **User:** Dedicated `syspulse` (no sudo)
* **Secrets:** `.env` (600 permissions)
* **Security:** IP-restricted SSH

### Scheduling

```cron
# Daily at 9 AM IST
0 9 * * * cd /home/syspulse/syspulse && venv/bin/python src/reporter.py >> logs/syspulse.log 2>&1
```

### Observability

* Slack → triage summaries
* Markdown reports → `reports/`
* Logs → `logs/syspulse.log`
* Cost tracking per run

### Cost Profile

* Per run: ~$0.02
* Monthly: ~$0.60
* EC2: Free tier or ~$7.50/month

---

## 🧠 Engineering Insights

This project focuses on **trustworthy AI**, not just working AI:

* **Observer effect** → monitoring tools measure themselves
* **Confabulation risk** → LLMs invent plausible details
* **Debugging rule** → most “AI bugs” are data bugs
* **Defense in depth** → prompt + validation + rate limits
* **Graceful degradation** → failures don’t break pipeline
* **Dev–prod parity** → controlled environments prevent drift
* **Least privilege** → minimized attack surface

---

## 🗺️ Roadmap

* [x] Metric collector
* [x] AI report generation
* [x] Validation + cost tracking
* [x] Slack + EC2 deployment
* [ ] Web dashboard (future)
* [ ] Multi-node monitoring

---

## 📜 License

MIT — see [LICENSE](./LICENSE)
