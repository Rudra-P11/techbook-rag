import re
from typing import List, Dict, Any, Tuple
from app.api.schemas.chat import Citation


class CitationValidator:
    """
    Validates that model citations reference actual retrieved evidence passages,
    replaces raw evidence IDs with formatted citations, and rejects fabricated IDs.
    """

    @staticmethod
    def format_citation_string(title: str, pages: List[int]) -> str:
        if not pages:
            return f"[{title}]"
        if len(pages) == 1:
            return f"[{title}, p. {pages[0]}]"
        # Spanning multiple pages
        if pages[-1] - pages[0] == len(pages) - 1:
            return f"[{title}, pp. {pages[0]}–{pages[-1]}]"
        return f"[{title}, pp. {', '.join(map(str, pages))}]"

    def process_and_validate(
        self,
        raw_answer: str,
        evidence_list: List[Dict[str, Any]],
        format_inline: bool = True
    ) -> Tuple[str, List[Citation]]:
        """
        Extracts [E#] identifiers from raw_answer, verifies them against evidence_list,
        and produces the clean answer and verified citations list.
        """
        evidence_map = {ev["evidence_id"]: ev for ev in evidence_list}
        cited_ids = set(re.findall(r'\[(E\d+)\]', raw_answer))

        verified_citations: List[Citation] = []
        valid_cited_ids = set()

        for eid in cited_ids:
            if eid in evidence_map:
                ev = evidence_map[eid]
                valid_cited_ids.add(eid)
                verified_citations.append(Citation(
                    evidence_id=eid,
                    document_id=ev["document_id"],
                    filename=ev["filename"],
                    title=ev["title"],
                    pages=ev.get("pages", [1]),
                    subject=ev.get("subject")
                ))

        processed_answer = raw_answer

        # Strip any fabricated evidence IDs (e.g. [E99])
        for match in re.finditer(r'\[(E\d+)\]', raw_answer):
            full_tag = match.group(0)
            eid = match.group(1)
            if eid not in evidence_map:
                processed_answer = processed_answer.replace(full_tag, "")

        # Optionally format inline tags: [E1] -> [Python in Finance, p. 45]
        if format_inline:
            for eid in valid_cited_ids:
                ev = evidence_map[eid]
                formatted_tag = self.format_citation_string(ev["title"], ev.get("pages", []))
                processed_answer = processed_answer.replace(f"[{eid}]", f" {formatted_tag}")

        # Clean any double spaces caused by replacement
        processed_answer = re.sub(r' {2,}', ' ', processed_answer)

        # Sort verified citations by evidence ID
        verified_citations.sort(key=lambda c: int(c.evidence_id.replace("E", "")))

        return processed_answer.strip(), verified_citations


citation_validator = CitationValidator()
