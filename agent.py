#!/usr/bin/env python3
"""
INVENTORY SENTINEL AGENT
========================
Autonomous agent for continuous inventory monitoring
"""

import time
import json
import logging
from datetime import datetime, timezone
from optimized_sentinel import OptimizedInventorySentinel


class InventoryAgent:
    def __init__(self, check_interval=300):  # 5 minutes default
        self.sentinel = OptimizedInventorySentinel()
        self.check_interval = check_interval
        self.running = False
        self.last_alert = None

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start the agent"""
        self.running = True
        self.logger.info("🤖 Inventory Agent started")

        # Initialize AI client if configured
        try:
            from app.config import (
                AI_PROVIDER, AI_API_KEY, AI_MODEL,
                AI_ENDPOINT, AI_AUTOMATE)
            if AI_PROVIDER:
                from agent_ai import AgentAI
                self.ai = AgentAI(
                    provider=AI_PROVIDER,
                    api_key=AI_API_KEY,
                    model=AI_MODEL,
                    endpoint=AI_ENDPOINT,
                    automate=AI_AUTOMATE)
                self.logger.info(
                    f"🔗 AI enabled (provider={AI_PROVIDER}, "
                    f"automate={AI_AUTOMATE})")
        except Exception:
            # If AI client is not configured or import fails, continue without
            # AI
            self.ai = None

        while self.running:
            try:
                self.run_check()
                # Wait for next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                self.logger.error(f"❌ Agent error: {e}")
                time.sleep(60)  # Wait 1 minute on error

    def run_check(self):
        """Run check (deterministic flow with AI language-only & ops)."""
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        try:
            # Use deterministic engine to compute at-risk SKUs
            risks = self.sentinel.analyze_inventory()
        except FileNotFoundError as e:
            # CSV missing
            from ops_notify import notify_ops
            notify_ops(
                "CSV_MISSING",
                run_id,
                datetime.now(timezone.utc).isoformat(),
                details=str(e))
            return {"status": "failure", "failure_type": "CSV_MISSING"}
        except Exception as e:
            from ops_notify import notify_ops
            notify_ops(
                "MATH_ERROR",
                run_id,
                datetime.now(timezone.utc).isoformat(),
                details=str(e))
            return {"status": "failure", "failure_type": "MATH_ERROR"}

        if not risks:
            self.logger.info("silent: no at-risk SKUs detected")
            # Write audit entry to alerts.json as silent
            with open('alerts.json', 'a') as f:
                rec = {"run_id": run_id, "status": "silent",
                       "timestamp": datetime.now(timezone.utc).isoformat()}
                f.write(json.dumps(rec) + "\n")
            return {"status": "silent"}

        # Build payload to send to AI (only at-risk SKUs)
        payload = {
            "total_cash_at_risk": sum(r.cash_at_risk for r in risks),
            "earliest_expiry": min(r.days_left for r in risks),
            "confidence_score": 80,  # deterministic heuristic for now
            "skus": [
                {
                    "sku": r.sku,
                    "cash_at_risk": r.cash_at_risk,
                    "days_to_expiry": r.days_left,
                    "breakeven_probability": round(r.breakeven_prob, 2)
                }
                for r in risks[:3]
            ]
        }

        # Deduplication check (fast path using alerts.latest.json cache)
        try:
            from app.config import DEDUPE_WINDOW_DAYS
            duplicate = False
            try:
                # Try fast cache first
                with open('alerts.latest.json', 'r') as lf:
                    latest = json.load(lf)
                    if latest.get('status') == 'alert' and latest.get('skus'):
                        past_skus = {s['sku'] for s in latest.get('skus', [])}
                        current_skus = {s['sku'] for s in payload['skus']}
                        if past_skus & current_skus:
                            try:
                                ts = latest.get('timestamp')
                                past_time = datetime.fromisoformat(ts)
                            except Exception:
                                past_time = None
                            if past_time:
                                now = datetime.now(timezone.utc)
                                days_ago = (now - past_time).days
                                if days_ago <= DEDUPE_WINDOW_DAYS:
                                    duplicate = True
            except FileNotFoundError:
                # fallback to full scan only if cache missing
                try:
                    with open('alerts.json', 'r') as f:
                        now = datetime.now(timezone.utc)
                        for line in f:
                            try:
                                obj = json.loads(line)
                                if (obj.get('status') == 'alert' and obj.get('skus')):
                                    past_skus = {s['sku'] for s in obj.get('skus', [])}
                                    current_skus = {s['sku'] for s in payload['skus']}
                                    if past_skus & current_skus:
                                        try:
                                            ts = obj.get('timestamp')
                                            past_time = datetime.fromisoformat(ts)
                                        except Exception:
                                            continue
                                        days_ago = (now - past_time).days
                                        if days_ago <= DEDUPE_WINDOW_DAYS:
                                            duplicate = True
                                            break
                            except Exception:
                                continue
                except FileNotFoundError:
                    duplicate = False

            if duplicate:
                self.logger.info("silent: duplicate alert within dedupe window")
                with open('alerts.json', 'a') as f:
                    f.write(json.dumps({
                        "run_id": run_id,
                        "status": "silent",
                        "reason": "duplicate",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }) + "\n")
                return {"status": "silent", "reason": "duplicate"}
        except Exception as e:
            self.logger.warning(f"Dedup check failed: {e}")

        # Generate executive message via AI (language-only)
        if getattr(self, 'ai', None):
            try:
                msg_obj = self.ai.generate_message(payload)
                message_text = msg_obj.get('message', '')
                confidence = msg_obj.get('confidence', 0)
            except Exception as e:
                from ops_notify import notify_ops
                notify_ops(
                    "LLM_ERROR",
                    run_id,
                    datetime.now(timezone.utc).isoformat(),
                    details=str(e))
                return {"status": "failure", "failure_type": "LLM_ERROR"}
        else:
            # No AI configured -> use deterministic fallback language
            msg_lines = [
                f"- {r.sku}: ${r.cash_at_risk} at risk, "
                f"expires {r.days_left} days"
                for r in risks[:3]
            ]
            message_text = "\n".join(msg_lines)
            confidence = 75

        if not message_text.strip():
            # LLM returned nothing -> treat as silence
            self.logger.info("silent: LLM returned no message")
            with open('alerts.json', 'a') as f:
                rec = {"run_id": run_id, "status": "silent",
                       "timestamp": datetime.now(timezone.utc).isoformat()}
                f.write(json.dumps(rec) + "\n")
            return {"status": "silent"}

        # Deliver executive alert (one channel)
        try:
            from app.config import EXECUTIVE_CHANNEL
            if EXECUTIVE_CHANNEL == 'email':
                from app.config import EXECUTIVE_EMAIL
                # Send via ops_notify SMTP helper (reuse for simplicity)
                from ops_notify import notify_ops  # noqa: F401
                subject = f"[Inventory Sentinel] Alert — {run_id}"
                import smtplib
                from email.message import EmailMessage
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = 'inventory-sentinel@example.com'
                msg['To'] = EXECUTIVE_EMAIL
                msg.set_content(message_text)

                # Try send, but do not retry on failure
                try:
                    if OPS_SMTP_SERVER := globals().get(
                            'OPS_SMTP_SERVER', None):
                        # use ops config if available
                        from app.config import (
                            OPS_SMTP_SERVER, OPS_SMTP_PORT,
                            OPS_SMTP_USER, OPS_SMTP_PASS)
                        smtp_addr = (OPS_SMTP_SERVER, OPS_SMTP_PORT)
                        with smtplib.SMTP(*smtp_addr, timeout=10) as s:
                            s.starttls()
                            if OPS_SMTP_USER and OPS_SMTP_PASS:
                                s.login(OPS_SMTP_USER, OPS_SMTP_PASS)
                            s.send_message(msg)
                    else:
                        # no SMTP: log & treat as delivered for testing
                        self.logger.warning(
                            'SMTP not configured; logging message')
                        self.logger.info(
                            'EXECUTIVE MESSAGE:\n%s', message_text)

                except Exception as e:
                    # Notify ops; mark failure
                    from ops_notify import notify_ops
                    notify_ops(
                        'ALERT_DELIVERY_ERROR', run_id,
                        datetime.now(timezone.utc).isoformat(),
                        details=str(e))
                    return {
                        "status": "failure",
                        "failure_type": "ALERT_DELIVERY_ERROR"}

            # Save audit record for the alert and update latest cache for fast dedupe
            rec = {"run_id": run_id, "status": "alert",
                   "skus": payload['skus'],
                   "total_cash_at_risk": payload['total_cash_at_risk'],
                   "message": message_text,
                   "timestamp": datetime.now(timezone.utc).isoformat(),
                   "confidence": confidence}
            with open('alerts.json', 'a') as f:
                f.write(json.dumps(rec) + "\n")
            try:
                with open('alerts.latest.json', 'w') as lf:
                    json.dump({
                        "run_id": run_id,
                        "status": "alert",
                        "skus": payload['skus'],
                        "timestamp": rec['timestamp']
                    }, lf)
            except Exception:
                # non-fatal: continue
                pass

            self.logger.info("✅ Executive alert delivered")
            return {
                "status": "alert",
                "message": message_text,
                "confidence": confidence}

        except Exception as e:
            from ops_notify import notify_ops
            notify_ops(
                'ALERT_DELIVERY_ERROR',
                run_id,
                datetime.now(timezone.utc).isoformat(),
                details=str(e))
            return {
                "status": "failure",
                "failure_type": "ALERT_DELIVERY_ERROR"}

    def attempt_mitigation(self, result, decision):
        """Perform (or sandbox) mitigation suggested by AI.

        Safety rules:
        - If AI_SANDBOX: dry-run only, no external actions.
        - If not AI_ALLOW_AUTOMATED_MITIGATION: block execution.
        - POC logs intended actions only.
        """
        try:
            from app.config import AI_SANDBOX, AI_ALLOW_AUTOMATED_MITIGATION
        except Exception:
            AI_SANDBOX = True
            AI_ALLOW_AUTOMATED_MITIGATION = False

        if AI_SANDBOX:
            self.logger.info(
                f"🧪 Mitigation (sandbox): {
                    decision.get('message')}")
            return False

        if not AI_ALLOW_AUTOMATED_MITIGATION:
            self.logger.warning(
                "🛑 Mitigation blocked by safety settings. "
                "Enable AI_ALLOW_AUTOMATED_MITIGATION to allow.")
            return False

        # If we reach here, mitigation is allowed — still do not perform real
        # external effects in this POC
        self.logger.info(
            f"🛠️ Executing mitigation (SIMULATED): "
            f"{decision.get('message')}")
        # TODO: implement real mitigation (API calls, inventory adjustments,
        # notifications)
        return False

    def stop(self):
        """Stop the agent"""
        self.running = False
        self.logger.info("🛑 Inventory Agent stopped")

    def handle_alert(self, result):
        """Handle alert notifications"""
        alert = result['alert_message']

        # Avoid duplicate alerts
        if alert == self.last_alert:
            return

        self.last_alert = alert

        # Log alert
        self.logger.warning(f"🚨 ALERT: {alert}")

        # Save alert to file
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "message": alert,
            "risks": result['top_risks'],
            "total_cash_at_risk": result['total_cash_at_risk']
        }

        with open("alerts.json", "a") as f:
            f.write(json.dumps(alert_data) + "\n")

    def get_status(self):
        """Get current agent status"""
        try:
            result = self.sentinel.run_analysis()
            return {
                "status": "running" if self.running else "stopped",
                "last_check": datetime.now().isoformat(),
                "risks": result['total_risks'],
                "cash_at_risk": result['total_cash_at_risk'],
                "has_alert": bool(result.get('alert_message'))
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


def main():
    """Run agent"""
    print("🤖 INVENTORY SENTINEL AGENT")
    print("=" * 40)

    agent = InventoryAgent(check_interval=60)  # Check every minute

    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()


if __name__ == "__main__":
    main()
