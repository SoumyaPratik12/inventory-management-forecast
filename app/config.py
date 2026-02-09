import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# AI configuration (opt-in)
# 'openai' or 'azure' or empty for disabled
AI_PROVIDER = os.getenv("AI_PROVIDER", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")
# used for Azure or custom endpoints
AI_ENDPOINT = os.getenv("AI_ENDPOINT", "")
AI_AUTOMATE = os.getenv("AI_AUTOMATE", "false").lower() in ("1", "true", "yes")
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "10"))  # seconds timeout for AI calls

# Safety and mitigation controls
# When AI_SANDBOX is true, mitigation actions are always dry-run (no
# external effects)
AI_SANDBOX = os.getenv("AI_SANDBOX", "true").lower() in ("1", "true", "yes")
# Allow actual automated mitigation only if explicitly enabled
AI_ALLOW_AUTOMATED_MITIGATION = os.getenv(
    "AI_ALLOW_AUTOMATED_MITIGATION", "false").lower() in (
        "1", "true", "yes")

# Deterministic risk thresholds
BREAKEVEN_PROB_THRESHOLD = float(os.getenv("BREAKEVEN_PROB_THRESHOLD", "0.30"))
REMAINING_CASH_THRESHOLD = float(
    os.getenv("REMAINING_CASH_THRESHOLD", "300.0"))
DAYS_LEFT_THRESHOLD = int(os.getenv("DAYS_LEFT_THRESHOLD", "30"))

# Alert deduplication and delivery
DEDUPE_WINDOW_DAYS = int(os.getenv("DEDUPE_WINDOW_DAYS", "7"))
EXECUTIVE_CHANNEL = os.getenv(
    "EXECUTIVE_CHANNEL",
    "email")  # only 'email' currently supported
EXECUTIVE_EMAIL = os.getenv("EXECUTIVE_EMAIL", "cfo@example.com")

# Ops notification settings (for failures)
OPS_EMAIL_RECIPIENT = os.getenv("OPS_EMAIL_RECIPIENT", "ops@example.com")
OPS_SMTP_SERVER = os.getenv("OPS_SMTP_SERVER", "")
OPS_SMTP_PORT = int(os.getenv("OPS_SMTP_PORT", "587"))
OPS_SMTP_USER = os.getenv("OPS_SMTP_USER", "")
OPS_SMTP_PASS = os.getenv("OPS_SMTP_PASS", "")
