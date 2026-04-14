import re
import uuid

from app.schemas.query import Citation
from app.services.retrieval.dense_retriever import RetrievedChunk


def build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    """Build citation objects from the reranked chunks."""
    citations = []
    for i, chunk in enumerate(chunks, 1):
        doc_id = chunk.document_id
        try:
            doc_uuid = uuid.UUID(doc_id)
        except (ValueError, AttributeError):
            doc_uuid = uuid.uuid4()

        # Truncate chunk text for preview
        preview = chunk.text[:300] + "..." if len(chunk.text) > 300 else chunk.text

        citations.append(
            Citation(
                source_number=i,
                document_name=chunk.document_name,
                document_id=doc_uuid,
                page_number=chunk.page_number,
                section_heading=chunk.section_heading,
                chunk_text=preview,
                relevance_score=round(chunk.score, 4),
            )
        )
    return citations


def extract_cited_sources(answer: str) -> list[int]:
    """Extract [Source N] references from the answer text."""
    pattern = r"\[Source\s+(\d+)\]"
    matches = re.findall(pattern, answer)
    return sorted(set(int(m) for m in matches))


def filter_cited_citations(
    citations: list[Citation], answer: str
) -> list[Citation]:
    """Return only citations that are actually referenced in the answer."""
    cited_numbers = extract_cited_sources(answer)
    if not cited_numbers:
        return citations  # Return all if no explicit citations found
    return [c for c in citations if c.source_number in cited_numbers]
