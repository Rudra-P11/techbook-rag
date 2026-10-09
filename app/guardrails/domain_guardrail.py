import re
from typing import Tuple, Optional


class DomainGuardrail:
    """
    Enforces scope and safety guardrails for the TechBook RAG application.
    Intercepts medical, harmful, and completely out-of-scope non-technical queries
    before expensive retrieval or generation is executed.
    """

    MEDICAL_PATTERNS = [
        r"\b(head\s*ache|headche|migraine|fever|cough|sore throat|chest pain|stomach ache|pain)\b",
        r"\b(symptom|symptoms|medication|medicine|dosage|pill|prescription|drug)\b",
        r"\b(diagnose|diagnosis|disease|illness|infection|blood pressure|health)\b",
        r"\b(doctor|physician|hospital|clinic|treatment for|cure for|remedy)\b"
    ]

    HARMFUL_PATTERNS = [
        r"\b(how to build a bomb|make explosive|poison someone|commit suicide)\b",
        r"\b(hack into|steal credit card|ddos attack)\b"
    ]

    def check_query_safety(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluates whether a query is safe and in-scope.
        Returns:
            (is_allowed: bool, category: Optional[str], response_message: Optional[str])
        """
        q_lower = query.lower().strip()

        # Check Medical Guardrail
        for pattern in self.MEDICAL_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    False,
                    "medical_advice",
                    "I am TechBook RAG, a specialized assistant for technical books covering SQL, Python, Machine Learning, Deep Learning, and Computer Science.\n\n"
                    "I cannot provide medical advice, diagnosis, or treatment recommendations. If you are experiencing physical symptoms such as a headache, please consult a qualified healthcare professional."
                )

        # Check Harmful Content Guardrail
        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    False,
                    "safety_violation",
                    "This query violates safety guidelines and cannot be processed."
                )

        return True, None, None


domain_guardrail = DomainGuardrail()
