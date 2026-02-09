# 🚀 Optimized Inventory Sentinel

## 📊 High-Quality Data & Performance

### ✅ Data Quality Improvements:
- **15 realistic products** with varied costs ($8-$90)
- **31 sales transactions** with realistic patterns
- **Near-expiry scenarios** to trigger risk detection
- **Clean data structure** with no duplicates

### ⚡ Performance Results:
```
✅ Analysis completed in 4.10ms
📊 Found 11 at-risk SKUs
💰 Total cash at risk: $51,727.75
🎯 Priority SKUs: PROD-010, PROD-002, PROD-005
```

## 🚀 Quick Start

### Run Analysis:
```bash
python optimized_sentinel.py
```

### Start API Server:
```bash
python optimized_api.py
# Access: http://localhost:5003
```

### Run Tests:
```bash
python test_optimized.py
```

## 📁 Clean File Structure:
```
inventory_sentinel/
├── data/
│   ├── inventory.csv     # 15 quality products
│   └── sales.csv         # 31 realistic transactions
├── optimized_sentinel.py # Core system (single file)
├── optimized_api.py      # FastAPI server
├── test_optimized.py     # Comprehensive tests
└── requirements_optimized.txt # Minimal deps
```

## 🎯 Key Features:
- **Sub-5ms execution** time
- **Real risk detection** with 11 at-risk SKUs
- **Quality alerts** with urgency scoring
- **Production ready** with robust error handling

## 📈 Sample Risk Detection:
- PROD-010: $4,038 at risk, expires in 1 day
- PROD-002: $3,930 at risk, expires in 1 day  
- PROD-005: $4,374 at risk, expires in 2 days

**System Status: ✅ OPTIMIZED & PRODUCTION READY**

---

## 🔐 Operational notes & safety (MUST READ)
- **Core principles** (do not override):
  - Deterministic math decides risk (no AI forecasting).
  - **AI only writes language** (one executive message or nothing).
  - Executives see only decisions (no failure details). Operators get **failure** notifications.
  - Silence is expected and a sign the system worked.
- **Configuration**:
  - Use `.env` or a secrets manager. See `./.env.example` for keys: `AI_PROVIDER`, `AI_AUTOMATE`, `AI_SANDBOX`, `AI_ALLOW_AUTOMATED_MITIGATION`, `BREAKEVEN_PROB_THRESHOLD`, `REMAINING_CASH_THRESHOLD`, `DAYS_LEFT_THRESHOLD`, `DEDUPE_WINDOW_DAYS`, `EXECUTIVE_EMAIL`, `OPS_EMAIL_RECIPIENT`.
  - Start with `AI_AUTOMATE=false` and `AI_SANDBOX=true` for safe testing; enable automation only after audit.
- **Failure handling**:
  - The agent will stop immediately on CSV issues or math errors and call `notify_ops()` with one of: `CSV_MISSING`, `CSV_INVALID`, `MATH_ERROR`, `LLM_ERROR`, `ALERT_DELIVERY_ERROR`.
  - Operators receive an email with the subject **[Inventory Sentinel] Run Failed — Action Required**; executives never receive failure details.
- **Testing & deployment**:
  - Run `python -m pytest` locally. For CI, add a scheduled dry-run and keep `AI_AUTOMATE=false` in CI secrets.
  - For manual runs or web prototype use the FastAPI endpoint to upload CSVs and trigger the run; UI shows only `Last Run`, `Status`, `Confidence`, and the single `Message` when sent.

---

## 🧾 Immutable LLM System Prompt (DO NOT CHANGE)
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

- **Behavioral note:** the model receives ONLY at-risk SKUs, total cash at risk, earliest expiry, confidence score, and at most the top 3 SKUs. The payload format is a strict JSON object (see `agent.run_check()` implementation). On any LLM error the agent will notify ops with `LLM_ERROR` and **will not** send an executive alert.

---

For questions or to enable automation, contact ops and perform a formal audit before enabling `AI_AUTOMATE=true` and `AI_ALLOW_AUTOMATED_MITIGATION=true`.