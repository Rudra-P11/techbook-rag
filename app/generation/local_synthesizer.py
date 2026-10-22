import re
import time
from typing import List, Dict, Any, Tuple


class LocalExtractiveSynthesizer:
    """
    Deterministic local extractor that synthesizes structured answers directly
    from retrieved evidence passages without requiring external LLM API calls.
    Ensures that live demos never fail due to API key expiry or rate limits.
    """

    def synthesize(self, query: str, evidence_list: List[Dict[str, Any]]) -> Tuple[str, int]:
        start = time.perf_counter()
        if not evidence_list:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return "The provided technical books do not contain sufficient evidence to answer this question.", max(1, latency_ms)

        q_lower = query.lower()
        q_tokens = set(re.findall(r'\w+', q_lower))

        # Top source summary
        primary_chunk = evidence_list[0]
        primary_title = primary_chunk.get("title", "Technical Reference")
        primary_pages = primary_chunk.get("pages", [])
        page_str = f"pp. {', '.join(map(str, primary_pages))}" if primary_pages else "N/A"

        # Extract code blocks if any exist in the retrieved evidence
        extracted_code = []
        for ev in evidence_list:
            text = ev.get("text", "")
            code_matches = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
            if code_matches:
                extracted_code.extend(code_matches)
            else:
                # Look for indented Python / SQL snippets
                indented_lines = [line for line in text.splitlines() if line.startswith("    ") or line.startswith("\t")]
                if len(indented_lines) >= 3:
                    extracted_code.append("\n".join(indented_lines[:8]))

        # Score sentences from retrieved chunks based on query token relevance
        extracted_points = []
        for idx, ev in enumerate(evidence_list, 1):
            text = ev.get("text", "")
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) < 35 or len(s_clean) > 280:
                    continue
                s_tokens = set(re.findall(r'\w+', s_clean.lower()))
                overlap = len(q_tokens & s_tokens)
                if overlap > 0:
                    extracted_points.append({
                        "sentence": s_clean,
                        "overlap": overlap,
                        "ev_id": f"[E{idx}]",
                        "title": ev.get("title", "Textbook")
                    })

        # Sort extracted points by relevance
        extracted_points.sort(key=lambda x: x["overlap"], reverse=True)

        # Deduplicate sentences
        seen_stems = set()
        chosen_points = []
        for pt in extracted_points:
            stem = " ".join(pt["sentence"].lower().split()[:6])
            if stem not in seen_stems:
                seen_stems.add(stem)
                chosen_points.append(pt)
            if len(chosen_points) >= 4:
                break

        # Build synthesized answer
        answer_parts = []
        answer_parts.append(f"> ⚡ **Local Neural Extractor Mode (Deterministic Local Synthesis — Zero API Cost)**")
        answer_parts.append("")
        answer_parts.append(f"Based on **{primary_title}** ({page_str}) and relevant textbook evidence:")
        answer_parts.append("")

        if chosen_points:
            for pt in chosen_points:
                answer_parts.append(f"- {pt['sentence']} {pt['ev_id']}")
        else:
            # Fallback to direct excerpts from top 2 chunks
            top_snippet = primary_chunk.get("text", "")[:350].strip()
            answer_parts.append(f"{top_snippet}... [E1]")

        if extracted_code:
            answer_parts.append("")
            answer_parts.append("```python")
            answer_parts.append(extracted_code[0].strip())
            answer_parts.append("```")

        answer_parts.append("")
        answer_parts.append(f"*(Synthesized deterministically from {len(evidence_list)} retrieved textbook chunks)*")

        final_text = "\n".join(answer_parts)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return final_text, max(2, latency_ms)


local_synthesizer = LocalExtractiveSynthesizer()
