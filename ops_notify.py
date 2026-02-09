"""Operator notification utilities (email-based)

Implements notify_ops(failure_type, run_id, timestamp) that sends an ops email when configured.
If SMTP is not configured, logs the message for local debugging.
"""

from app.config import (
    OPS_EMAIL_RECIPIENT,
    OPS_SMTP_SERVER,
    OPS_SMTP_PORT,
    OPS_SMTP_USER,
    OPS_SMTP_PASS,
)
import smtplib
import logging
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def notify_ops(
        failure_type: str,
        run_id: str,
        timestamp: str,
        details: str = "") -> bool:
    subject = "[Inventory Sentinel] Run Failed — Action Required"
    body = (
        f"The Inventory Sentinel failed during its run.\n\n"
        f"Failure type: {failure_type}\n"
        f"Run ID: {run_id}\n"
        f"Timestamp: {timestamp}\n\n"
        f"No executive alert was sent.\n\n"
        f"Recommended action:\n"
        f"• Verify required CSV files\n"
        f"• Validate schema and values\n"
        f"• Re-run after correction\n\n"
        f"Details:\n{details}\n"
    )

    if not OPS_SMTP_SERVER or not OPS_EMAIL_RECIPIENT:
        logger.warning(
            "OPS notify missing SMTP configuration; logging instead of sending email")
        logger.warning(subject + "\n" + body)
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = OPS_SMTP_USER or 'inventory-sentinel@example.com'
        msg['To'] = OPS_EMAIL_RECIPIENT
        msg.set_content(body)

        with smtplib.SMTP(OPS_SMTP_SERVER, OPS_SMTP_PORT, timeout=10) as s:
            s.starttls()
            if OPS_SMTP_USER and OPS_SMTP_PASS:
                s.login(OPS_SMTP_USER, OPS_SMTP_PASS)
            s.send_message(msg)

        logger.info("Ops notification email sent to %s", OPS_EMAIL_RECIPIENT)
        return True
    except Exception as e:
        logger.exception(f"Failed to send ops email: {e}")
        return False
