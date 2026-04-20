from __future__ import annotations

import json
import os
from typing import Any, Dict

from openai import OpenAI

from app.models import RequestType


SYSTEM_PROMPT = """
You are an enterprise workflow enrichment assistant.

Analyze the workflow request and return valid JSON only.
Classify the request, infer missing fields if possible, write a short summary,
and return a confidence score between 0 and 1.
""".strip()


class AIEnrichmentService:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "fallback").lower()
        self.client: OpenAI | None = None
        self.model: str | None = None

        if self.provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

            print("Provider:", self.provider)
            print("Groq key present:", bool(api_key))
            print("Model:", self.model)

            if api_key:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1",
                )

        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

            print("Provider:", self.provider)
            print("OpenAI key present:", bool(api_key))
            print("Model:", self.model)

            if api_key:
                self.client = OpenAI(api_key=api_key)

    def enrich_request(self, title: str, description: str) -> Dict[str, Any]:
        if not self.client or not self.model:
            print("Using fallback enrichment because client/model is missing")
            return self._fallback_enrichment(title, description)

        user_prompt = f"""
Title: {title}
Description: {description}

Return JSON in exactly this format:
{{
  "request_type": "PROCUREMENT",
  "amount": null,
  "leave_days": null,
  "severity": 3,
  "summary": "short approver-friendly summary",
  "confidence": 0.85
}}

Allowed request_type values:
PROCUREMENT, LEAVE, SUPPORT, FINANCE, HR,UNKNOWN

IMPORTANT:
- severity must be an INTEGER from 1 to 5
- DO NOT use words like low, medium, or high
- amount must be a number or null
- leave_days must be an integer or null
- confidence must be a number between 0 and 1
- Asking for leave and days off will be a LEAVE request but anything related to wellbeing and HR is HR
- return valid JSON only
""".strip()

        try:
            print("Calling real LLM...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            print("LLM raw output:", content)

            parsed = json.loads(content)

            # Normalize request_type
            request_type = str(parsed.get("request_type", "UNKNOWN")).upper()
            if request_type not in {"PROCUREMENT", "LEAVE", "SUPPORT", "FINANCE", "HR", "UNKNOWN"}:
                request_type = "UNKNOWN"

            # Normalize amount
            amount = parsed.get("amount")
            try:
                amount = float(amount) if amount is not None else None
            except (TypeError, ValueError):
                amount = None

            # Normalize leave_days
            leave_days = parsed.get("leave_days")
            try:
                if leave_days is not None:
                    leave_days = int(leave_days)
            except (TypeError, ValueError):
                leave_days = None

            # Normalize severity
            severity = parsed.get("severity")
            severity_map = {
                "low": 1,
                "medium": 3,
                "high": 5,
                "critical": 5,
            }

            if isinstance(severity, str):
                sev_clean = severity.strip().lower()
                if sev_clean.isdigit():
                    severity = int(sev_clean)
                else:
                    severity = severity_map.get(sev_clean)

            elif isinstance(severity, float):
                severity = int(severity)

            elif not isinstance(severity, int):
                severity = None

            if severity is not None and (severity < 1 or severity > 5):
                severity = None

            # Normalize summary
            summary = parsed.get("summary")
            if not isinstance(summary, str) or not summary.strip():
                summary = f"Request received: {title}. Review details and route for approval."

            # Normalize confidence
            confidence = parsed.get("confidence", 0.7)
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 0.7

            if confidence < 0:
                confidence = 0.0
            elif confidence > 1:
                confidence = 1.0

            cleaned = {
                "request_type": request_type,
                "amount": amount,
                "leave_days": leave_days,
                "severity": severity,
                "summary": summary,
                "confidence": confidence,
            }

            print("Normalized LLM output:", cleaned)
            return cleaned

        except Exception as e:
            print("LLM call failed:", repr(e))
            return self._fallback_enrichment(title, description)

    def _fallback_enrichment(self, title: str, description: str) -> Dict[str, Any]:
        text = f"{title} {description}".lower()

        request_type = RequestType.UNKNOWN.value
        amount = None
        leave_days = None
        severity = None

        if any(word in text for word in ["buy", "purchase", "vendor", "laptop", "software", "license", "equipment"]):
            request_type = RequestType.PROCUREMENT.value
        elif any(word in text for word in ["leave", "vacation", "sick", "days off", "time off", "unavailable", "travel"]):
            request_type = RequestType.LEAVE.value
        elif any(word in text for word in ["incident", "issue", "bug", "support", "outage", "access", "deployment", "dashboard"]):
            request_type = RequestType.SUPPORT.value
        elif any(word in text for word in ["finance", "budget", "invoice", "payment", "expense", "accounts", "salary"]):
            request_type = RequestType.FINANCE.value
        elif any(word in text for word in ["hr", "human resources", "payroll", "benefits", "wellbeing", "harassment", "safety", "onboarding", "policy"]):
            request_type = RequestType.HR.value

        return {
            "request_type": request_type,
            "amount": amount,
            "leave_days": leave_days,
            "severity": severity,
            "summary": f"Request received: {title}. Review details and route for approval.",
            "confidence": 0.45,
        }


ai_service = AIEnrichmentService()
