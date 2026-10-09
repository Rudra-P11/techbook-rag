import re
from typing import Tuple


class TextCleaner:
    """
    Cleans and normalizes extracted PDF text without destroying
    technical meaning, code syntax, or indentation.
    """

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Join line-break hyphenations (e.g., 'trans- \nformer' -> 'transformer')
        # Only when hyphen is preceded and followed by lower/upper alphabetic letters
        text = re.sub(r'([a-zA-Z]{2,})-\n\s*([a-zA-Z]{2,})', r'\1\2', text)

        # Replace excessive blank lines (more than 2 consecutive newlines)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove null bytes and non-printable control characters, but keep tabs and newlines
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        return text.strip()

    @staticmethod
    def is_likely_scanned(text: str, min_chars: int = 50) -> bool:
        """
        Heuristic to detect if a page has insufficient native text and might be scanned.
        """
        cleaned = text.strip() if text else ""
        return len(cleaned) < min_chars


text_cleaner = TextCleaner()
