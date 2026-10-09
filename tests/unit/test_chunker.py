import pytest
from app.ingestion.chunker import chunker


def test_chunker_basic():
    pages = [
        {"page_number": 1, "text": "Paragraph 1 on page one explaining SQL.\n\nParagraph 2 on page one."},
        {"page_number": 2, "text": "Paragraph 3 on page two explaining joins."}
    ]
    chunks = chunker.chunk_document(
        document_id="doc_test",
        filename="test.pdf",
        title="Test Book",
        subject="SQL",
        file_hash="dummyhash",
        pages_data=pages
    )
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk["document_id"] == "doc_test"
    assert chunk["subject"] == "SQL"
    assert "start_page" in chunk
    assert "end_page" in chunk
    assert "chunk_id" in chunk
