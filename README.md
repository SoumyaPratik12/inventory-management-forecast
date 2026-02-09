# 🚀 Inventory Sentinel Agent

A deterministic, AI-augmented inventory risk detection system with carbon footprint tracking and supplier compliance flagging.

## ✨ Features

- **Deterministic Risk Engine**: Breaks even probability, cash remaining, and days-to-expiry thresholds
- **Carbon Footprint Tracking**: Calculates CO2 impact of potential product wastage by category
- **Supplier Compliance**: Flags non-compliant suppliers (missing certifications, violations)
- **AI Language-Only**: LLM generates executive messages only; deterministic math decides risk
- **Opt-in Automation**: AI automation disabled by default; manual enable required
- **Ops Notifications**: Failure alerts sent to operations email; executives see only decisions
- **Audit Trail**: All alerts logged to `alerts.json`
- **Fast Dedupe**: Latest-alert cache for efficient duplicate detection
- **Optimized DB**: SQLite pragmas + batch queries for sub-5ms execution

## 🚀 Quick Start

### Installation
```bash
# Create virtualenv
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r dev-requirements.txt
```

### Run a Single Check
```bash
# Run one-off agent check (respects dedupe window)
python cli_agent.py once

# Force non-duplicate (ignore dedupe window)
python cli_agent.py once --no-dedupe
```

### Run Continuously (5 minute intervals)
```bash
python cli_agent.py run --interval 300
```

### Run Tests
```bash
python -m pytest -v
```

## 📁 Project Structure

```
inventory_sentinel/
├── agent.py                      # Main agent orchestrator
├── optimized_sentinel.py         # Deterministic risk engine
├── agent_ai.py                   # AI language-only wrapper
├── ops_notify.py                 # Ops failure notification
├── carbon_footprint.py           # CO2 impact calculator
├── supplier_compliance.py        # Supplier compliance checker
├── cli_agent.py                  # CLI interface
├── app/
│   ├── config.py                 # Configuration (env-based)
│   ├── main.py                   # FastAPI app (optional web)
│   └── models.py                 # Data models
├── tests/                        # Pytest test suite
├── data/
│   ├── inventory.csv             # Sample inventory
│   └── sales.csv                 # Sample sales
├── scripts/
│   └── install_windows_service.ps1  # Windows service install
├── dev-requirements.txt          # Dev dependencies
├── .env.example                  # Environment template
├── README.md                      # This file
└── .gitignore
```

## ⚙️ Configuration

Copy `.env.example` to `.env` and set:

```bash
# AI Configuration (optional)
AI_PROVIDER=                     # empty, "openai", or "azure"
AI_API_KEY=                      # your API key
AI_MODEL=gpt-3.5-turbo          # model name
AI_AUTOMATE=false               # KEEP FALSE until audited
AI_SANDBOX=true                 # Mitigation dry-run only

# Risk Thresholds
BREAKEVEN_PROB_THRESHOLD=0.30   # Breakeven probability < 30%
REMAINING_CASH_THRESHOLD=300.0  # Cash at risk > $300
DAYS_LEFT_THRESHOLD=30          # Days to expiry < 30

# Alert Deduplication
DEDUPE_WINDOW_DAYS=7            # Ignore duplicate alerts within 7 days

# Email
EXECUTIVE_EMAIL=cfo@example.com
OPS_EMAIL_RECIPIENT=ops@example.com
OPS_SMTP_SERVER=                # Leave empty to log instead of email
OPS_SMTP_PORT=587
OPS_SMTP_USER=
OPS_SMTP_PASS=
```

## 🔍 How It Works

### Deterministic Risk Calculation

For each SKU:
1. **Remaining units** = units_on_hand - total_sold
2. **Required velocity** = remaining_units / days_left
3. **Actual velocity** = units_sold_in_last_30_days / 30
4. **Breakeven probability** = actual_velocity / required_velocity
5. **Risk** if ALL conditions true:
   - Breakeven probability < `BREAKEVEN_PROB_THRESHOLD` (e.g., 30%)
   - Remaining cash at risk > `REMAINING_CASH_THRESHOLD` (e.g., $300)
   - Days to expiry < `DAYS_LEFT_THRESHOLD` (e.g., 30 days)

### Carbon Footprint

When a SKU is at-risk:
- **Category-based emissions**: Food (2.5 kg CO2/unit), Electronics (15 kg), Textiles (5 kg), etc.
- **Total production impact** = units_at_risk × co2_per_unit
- **Disposal impact** = production_impact × disposal_multiplier (varies by category)
- **Sustainability score** = 100 - (total_impact / max_impact × 100)

### Supplier Compliance

Checks supplier certifications:
- **Required**: ISO_9001, ISO_14001, SA_8000
- **Violations**: Child labor, unsafe conditions, environmental incidents, missing audits
- **Risk level**: "low" (compliant), "medium", "high", "critical"

### AI Message Generation

If AI enabled and `AI_PROVIDER` set:
- Agent calls `AgentAI.generate_message(payload)` with at-risk SKUs
- LLM generates **one executive message** (≤120 words, bullets only)
- System prompt enforces CFO-friendly tone, no explanations, no emoji
- On LLM error: notify ops, do **not** send executive alert

### Execution Flow

```
run_check()
  ├─ analyze_inventory() → [at-risk SKUs]
  ├─ calculate_carbon_footprint() → kg CO2 per SKU
  ├─ check_supplier_compliance() → risk level per SKU
  ├─ check_dedupe() → skip if duplicate
  ├─ generate_ai_message() or use fallback
  ├─ deliver_executive_alert() → email or log
  ├─ write_audit_record() → alerts.json
  └─ return { status: "alert" | "silent", message, confidence }
```

## 🔐 Safety & Operations

### Core Principles (DO NOT OVERRIDE)
- **Deterministic math** always decides if risk exists
- **AI only writes language**; it cannot decide to trigger alerts
- **Automation is opt-in** (`AI_AUTOMATE=false` by default)
- **Sandbox mode** prevents real external actions (`AI_SANDBOX=true` by default)

### Failure Handling
The agent will **stop immediately** on:
- **CSV_MISSING**: Required data file not found
- **CSV_INVALID**: Corrupted or unparseable data
- **MATH_ERROR**: Calculation failure (notify ops)
- **LLM_ERROR**: AI API unreachable or error
- **ALERT_DELIVERY_ERROR**: Email send failure

Operators receive an email with subject: **[Inventory Sentinel] Run Failed — Action Required**  
Executives **never** see failure details.

### Deduplication
- Latest alert cached in `alerts.latest.json` for fast lookup
- Fallback to `alerts.json` if cache missing
- Dedupe window: 7 days (configurable)

### Testing & Deployment
```bash
# Local testing (dedupe enabled)
python cli_agent.py once

# Force test run (ignore dedupe)
python cli_agent.py once --no-dedupe

# Run test suite
python -m pytest -v

# CI recommendation: keep AI_AUTOMATE=false in CI secrets
```

## 📊 Immutable LLM System Prompt

```
You are an inventory risk sentinel reporting to executive leadership.

Rules:
- Maximum 120 words
- Bullet points only
- No tables
- No explanations
- No emojis
- CFO / finance-operations tone
- At most ONE recommendation sentence
- If data does not indicate material risk, output NOTHING
```

**Behavioral note**: The model receives ONLY at-risk SKUs, total cash at risk, earliest expiry, confidence score, and at most the top 3 SKUs. On any LLM error the agent will notify ops with `LLM_ERROR` and will **not** send an executive alert.

## 🪟 Windows Service Installation

To run the agent as a Windows service (optional):

```powershell
# Requires NSSM: https://nssm.cc/download
# Download nssm.exe and add to PATH

.\scripts\install_windows_service.ps1 -ServiceName InventorySentinel

# Then:
Start-Service -Name InventorySentinel
Stop-Service -Name InventorySentinel
```

Or use Scheduled Task for periodic execution:
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00am
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "cli_agent.py once"
Register-ScheduledTask -TaskName "InventorySentinel" -Trigger $trigger -Action $action
```

## ✅ Example Output

```json
{
  "status": "alert",
  "message": "- PROD-012: $4850.8 at risk, expires 8 days\n- PROD-013: $3835.0 at risk, expires 15 days",
  "confidence": 75
}
```

## 📝 Audit & Logging

All checks logged to `alerts.json`:
- **Silent runs**: No risk detected
- **Alert runs**: At-risk SKUs flagged; message sent
- **Failure runs**: Error details recorded; ops notified

View audit log:
```bash
tail -f alerts.json
```

## 🛠️ Development

### Add Tests
```bash
# Add test to tests/test_*.py
python -m pytest tests/test_*.py -v
```

### Update Risk Thresholds
Edit `app/config.py`:
```python
BREAKEVEN_PROB_THRESHOLD = 0.30  # Adjust as needed
REMAINING_CASH_THRESHOLD = 300.0
DAYS_LEFT_THRESHOLD = 30
```

### Add New Waste Categories
Edit `carbon_footprint.py`:
```python
CATEGORY_EMISSIONS = {
    "food": 2.5,
    "my_category": 10.0,  # Add here
    ...
}
```

### Add Supplier Data
Edit `supplier_compliance.py`:
```python
SUPPLIERS_DB = {
    "NEW-SUPP-001": {
        "name": "New Supplier",
        "certifications": ["ISO_9001"],
        "last_audit": "2026-01-01",
        "violations": []
    },
    ...
}
```

## 📞 Support

For issues or questions:
1. Check `.env.example` for required configuration
2. Run tests: `python -m pytest -v`
3. Review `alerts.json` for audit trail
4. Check logs: `tail logs/*.log`

---

**Last Updated**: February 9, 2026  
**Status**: ✅ Production Ready

For questions or to enable automation, contact ops and perform a formal audit before enabling `AI_AUTOMATE=true` and `AI_ALLOW_AUTOMATED_MITIGATION=true`.