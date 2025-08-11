from __future__ import annotations

import io
import base64
import re
from typing import List, Dict, Any, Optional
import uuid

import httpx
from loguru import logger
from tenacity import retry, wait_exponential, stop_after_attempt
from pydantic import BaseModel
import numpy as np
from PIL import Image

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

try:
    import open_clip
    import torch
except Exception:  # pragma: no cover
    open_clip = None  # type: ignore
    torch = None  # type: ignore

try:
    # prefer pymupdf for fast text/image extraction as hi-res OCR alternative
    import fitz  # pymupdf
except Exception:  # pragma: no cover
    fitz = None  # type: ignore


class PdfChunk(BaseModel):
    paper_id: str
    chunk_type: str  # text | image
    page_number: int
    content: Optional[str] = None
    image_b64: Optional[str] = None


@retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(5))
async def download_pdf(url: str) -> bytes:
    headers = {"User-Agent": "digitalPaperAgent/0.1 (+https://example.local)"}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        if not (r.headers.get("content-type", "").lower().startswith("application/pdf") or url.endswith(".pdf")):
            logger.warning("URL does not look like a PDF, content-type={} url={}", r.headers.get("content-type"), url)
        return r.content


def extract_with_pymupdf(pdf_bytes: bytes, paper_id: str) -> List[PdfChunk]:
    if fitz is None:
        raise RuntimeError("pymupdf not installed")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunks: List[PdfChunk] = []
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        text = page.get_text("text")
        if text and text.strip():
            # naive split into paragraphs
            for para in re.split(r"\n\s*\n+", text):
                para = para.strip()
                if not para:
                    continue
                chunks.append(PdfChunk(paper_id=paper_id, chunk_type="text", page_number=page_index + 1, content=para))
        # images
        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n >= 5:  # convert CMYK etc.
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_bytes = pix.tobytes("png")
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            chunks.append(PdfChunk(paper_id=paper_id, chunk_type="image", page_number=page_index + 1, image_b64=b64))
    return chunks


def build_text_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed")
    return SentenceTransformer(model_name)


def build_image_embedder(model_name: str = "ViT-B-32", pretrained: str = "openai"):
    if open_clip is None or torch is None:
        raise RuntimeError("open-clip-torch not installed")
    model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
    model.eval()
    return model, preprocess


def ensure_qdrant_collection(client: QdrantClient, collection: str, vector_size_text: int, vector_size_image: int):
    exists = False
    try:
        info = client.get_collection(collection)
        exists = info is not None
    except Exception:
        exists = False
    if not exists:
        client.recreate_collection(
            collection_name=collection,
            vectors_config={
                "text": VectorParams(size=vector_size_text, distance=Distance.COSINE),
                "image": VectorParams(size=vector_size_image, distance=Distance.COSINE),
            },
        )


def upsert_chunks(
    client: QdrantClient,
    collection: str,
    paper_id: str,
    text_vectors: List[np.ndarray],
    text_chunks: List[PdfChunk],
    image_vectors: List[np.ndarray],
    image_chunks: List[PdfChunk],
):
    points: List[PointStruct] = []
    pid_prefix = paper_id.replace("/", "_")
    # text
    for i, (vec, ch) in enumerate(zip(text_vectors, text_chunks)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={"text": vec.astype(np.float32).tolist()},
                payload={
                    "paper_id": paper_id,
                    "chunk_type": ch.chunk_type,
                    "page_number": ch.page_number,
                    "content": ch.content,
                    "ord": i,
                },
            )
        )
    # images
    for i, (vec, ch) in enumerate(zip(image_vectors, image_chunks)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={"image": vec.astype(np.float32).tolist()},
                payload={
                    "paper_id": paper_id,
                    "chunk_type": ch.chunk_type,
                    "page_number": ch.page_number,
                    "image_b64": ch.image_b64,
                    "ord": i,
                },
            )
        )
    if points:
        client.upsert(collection_name=collection, points=points)


def process_pdf_command(url: str, paper_id: Optional[str] = None) -> None:
    import asyncio

    async def _run():
        logger.info("Downloading PDF: {}", url)
        pdf = await download_pdf(url)
        _paper_id = paper_id or re.sub(r"[^0-9A-Za-z_-]", "_", url.split("/")[-1].replace(".pdf", ""))

        logger.info("Extracting with PyMuPDF ...")
        chunks = extract_with_pymupdf(pdf, paper_id=_paper_id)
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        image_chunks = [c for c in chunks if c.chunk_type == "image"]
        logger.info("Got {} text chunks, {} image chunks", len(text_chunks), len(image_chunks))

        # Embed
        logger.info("Loading text embedder ...")
        text_model = build_text_embedder()
        text_vectors = text_model.encode([c.content or "" for c in text_chunks], batch_size=32, show_progress_bar=False, normalize_embeddings=True)

        logger.info("Loading image embedder ...")
        image_vectors: List[np.ndarray] = []
        try:
            if image_chunks and open_clip is not None and torch is not None:
                model, preprocess = build_image_embedder()
                ims: List[np.ndarray] = []
                for ch in image_chunks:
                    img = Image.open(io.BytesIO(base64.b64decode(ch.image_b64 or ""))).convert("RGB")
                    ims.append(np.array(preprocess(img)).astype(np.float32))
                import torch as _torch

                with _torch.no_grad():
                    batch = _torch.stack([_torch.from_numpy(im) for im in ims])
                    features = model.encode_image(batch)
                    image_vectors = features.cpu().numpy()
        except Exception as e:
            logger.warning("Image embedding skipped: {}", e)

        # Qdrant
        client = QdrantClient(url="http://localhost:6333")
        text_dim = int(text_vectors.shape[1]) if hasattr(text_vectors, 'shape') else (len(text_vectors[0]) if text_chunks else 384)
        ensure_qdrant_collection(client, collection="papers", vector_size_text=text_dim, vector_size_image=512)
        upsert_chunks(client, collection="papers", paper_id=_paper_id, text_vectors=text_vectors, text_chunks=text_chunks, image_vectors=image_vectors, image_chunks=image_chunks)
        logger.info("Done upsert to Qdrant for paper {}", _paper_id)

    asyncio.run(_run())


