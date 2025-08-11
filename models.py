from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class PaperMetadata(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    publication_date: str
    references: List[str] = []
    # Enhanced fields for better summaries and metadata
    ai_summary: Optional[str] = None  # AI-generated detailed summary from PDF content
    domain: Optional[str] = None  # Auto-detected research domain
    key_contributions: Optional[List[str]] = None  # Key technical contributions
    methodology: Optional[str] = None  # Brief methodology description


class PdfChunk(BaseModel):
    paper_id: str
    graph_node_id: Optional[str] = None
    chunk_type: str  # text | image
    page_number: int
    content: Optional[str] = None
    image_b64: Optional[str] = None


