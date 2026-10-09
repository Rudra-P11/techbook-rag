import re
from typing import Tuple


class PromptInjectionGuardrail:
    """
    Detects and neutralizes prompt-injection attempts in user queries.
    """

    SUSPICIOUS_PATTERNS = [
        r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
        r"(reveal|print|show|output)\s+(your|the)?\s*(system\s+prompt|api\s*key|credentials|secret)",
        r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unfiltered|jailbroken)",
        r"repeat\s+the\s+(entire\s+)?(text\s+above|system\s+instructions)"
    ]

    def sanitize_query(self, query: str) -> Tuple[str, bool]:
        """
        Returns (sanitized_query, was_flagged).
        """
        flagged = False
        cleaned = query.strip()

        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                flagged = True
                # Neutralize by replacing the adversarial command
                cleaned = re.sub(pattern, "[FILTERED_INSTRUCTION]", cleaned, flags=re.IGNORECASE)

        return cleaned, flagged


injection_guardrail = PromptInjectionGuardrail()
