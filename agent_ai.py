"""AI integration for Inventory Agent (POC)

Provides:
- AgentAI: wrapper around OpenAI/Azure OpenAI for summary and decision-making
- Safe fallbacks when API is not configured or unavailable
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import openai (optional dependency)
try:
    import openai
except Exception:
    openai = None


class AgentAI:
    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        model: str = "gpt-3.5-turbo",
        endpoint: str = "",
        automate: bool = False,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.automate = automate

        # Configure OpenAI client if available
        if provider in ("openai", "azure") and openai:
            try:
                if provider == "azure":
                    # Configure Azure OpenAI compatibility if endpoint provided
                    openai.api_type = "azure"
                    openai.api_base = endpoint or openai.api_base
                    openai.api_key = api_key
                    # model name should match deployed model
                else:
                    openai.api_key = api_key
            except Exception as e:
                logger.warning(f"Failed to configure OpenAI client: {e}")

    def _call_model(
            self,
            messages,
            max_tokens=256,
            temperature=0.0,
            timeout=10):
        """Helper that calls the OpenAI API if available, otherwise raises."""
        if not openai:
            raise RuntimeError("OpenAI SDK not installed")

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            request_timeout=timeout
        )
        return response

    def summarize(self, result: Dict[str, Any]) -> Optional[str]:
        """Return a short summary for a given analysis result."""
        try:
            # Build a compact prompt
            top = result.get('top_risks', [])
            text = f"Found {
                result.get(
                    'total_risks',
                    0)} risks, total cash at risk ${
                result.get(
                    'total_cash_at_risk',
                    0):,.2f}.\n"
            text += "Top risks:\n"
            for r in top:
                text += (
                    f"- {r.get('sku')}: ${r.get('cash_at_risk')}, "
                    f"{r.get('days_left')} days left "
                    f"(urgency {r.get('urgency_score')})\n"
                )

            messages = [
                {"role": "system", "content": "You are a concise inventory risk summarizer."},
                {"role": "user", "content": "Summarize the following analysis in one or two sentences:\n" + text}
            ]

            if openai:
                resp = self._call_model(
                    messages, max_tokens=128, temperature=0.1, timeout=10)
                summary = resp.choices[0].message.content.strip()
                return summary
            else:
                # Fallback: simple deterministic summary
                if result.get('total_risks', 0) == 0:
                    return "No significant inventory risks detected."
                top_skus = ', '.join([r.get('sku') for r in top[:3]])
                return f"{
                    result.get('total_risks')} SKUs at risk. Top SKUs: {top_skus}."

        except Exception as e:
            logger.warning(f"AI summarize failed: {e}")
            return None

    def generate_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an executive-grade message from the payload using the final system prompt.

        Returns a dict: {"message": str, "confidence": int}
        Raises an exception on LLM error so caller can notify ops and abort.
        """
        system_prompt = (
            "You are an inventory risk sentinel reporting to executive leadership.\n\n"
            "Rules:\n"
            "- Maximum 120 words\n"
            "- Bullet points only\n"
            "- No tables\n"
            "- No explanations\n"
            "- No emojis\n"
            "- CFO / finance-operations tone\n"
            "- At most ONE recommendation sentence\n"
            "- If data does not indicate material risk, output NOTHING\n")

        user_content = json.dumps(payload)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        # If openai is available, call it; on failure, raise to let agent
        # notify ops
        if openai:
            try:
                resp = self._call_model(
                    messages, max_tokens=256, temperature=0.0, timeout=10)
                text = resp.choices[0].message.content.strip()

                # If model returns nothing or blank, treat as no alert
                if not text:
                    return {"message": "", "confidence": 0}

                # Confidence not easily available; attempt to find a number
                # heuristic or set 80
                confidence = 80
                return {"message": text, "confidence": confidence}
            except Exception as e:
                logger.exception(f"LLM generate_message failed: {e}")
                raise

        # Fallback deterministic message generator (language-only,
        # conservative)
        total_cash = payload.get('total_cash_at_risk', 0)
        skus = payload.get('skus', [])
        if total_cash <= 0 or not skus:
            return {"message": "", "confidence": 0}

        lines = []
        lines.append(
            f"{len(skus)} SKUs at risk; total cash at risk: ${total_cash:,.0f}.")
        lines.append(
            f"Earliest expiry: {
                payload.get('earliest_expiry')}; Confidence: {
                payload.get(
                    'confidence_score',
                    75)}%")
        # One recommendation sentence maximum
        lines.append(
            "Recommend review of pricing and redistribution for top SKUs.")

        message = "\n".join(f"- {line}" for line in lines)[:1200]
        return {
            "message": message,
            "confidence": payload.get('confidence_score', 75),
        }
