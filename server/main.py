from __future__ import annotations

import os
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from graph.neo4j_manager import Neo4jManager
from rag.insights import create_insight_generator


load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

app = FastAPI(title="DigitalPaperAgent API")


class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]


class PaperDetail(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    publication_date: str
    domain: str


def get_graph() -> Neo4jManager:
    return Neo4jManager(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


def extract_domain(title: str, abstract: str) -> str:
    """Extract domain/field from title and abstract"""
    text = (title + " " + abstract).lower()
    
    # Define domain keywords
    domains = {
        "Computer Vision": ["vision", "image", "visual", "cnn", "convolution", "detection", "segmentation", "object"],
        "Natural Language Processing": ["language", "nlp", "text", "transformer", "attention", "bert", "gpt", "linguistic"],
        "Machine Learning": ["learning", "neural", "network", "deep", "training", "optimization", "model"],
        "Reinforcement Learning": ["reinforcement", "rl", "agent", "policy", "reward", "environment", "action"],
        "Robotics": ["robot", "robotics", "manipulation", "control", "autonomous", "motion"],
        "Speech & Audio": ["speech", "audio", "acoustic", "voice", "recognition", "sound"],
        "Graph Neural Networks": ["graph", "node", "edge", "network", "topology", "gnn"],
        "Generative AI": ["generative", "generation", "diffusion", "gan", "vae", "autoencoder", "generate"],
        "Multimodal": ["multimodal", "multi-modal", "vision-language", "cross-modal"],
    }
    
    for domain, keywords in domains.items():
        if any(keyword in text for keyword in keywords):
            return domain
    
    return "AI/ML"  # Default domain


def enrich_node(paper_data: Dict, node_type: str = "regular") -> Dict[str, Any]:
    """Enrich node with metadata for frontend display"""
    node = {"id": paper_data["id"]}
    
    if paper_data.get("title"):
        node["title"] = paper_data["title"]
        
        # Use AI summary if available, otherwise fallback to abstract
        ai_summary = paper_data.get("ai_summary", "")
        abstract = paper_data.get("abstract", "")
        
        if ai_summary:
            # Use AI-generated comprehensive summary (longer and more detailed)
            summary = ai_summary[:300] + "..." if len(ai_summary) > 300 else ai_summary
            node["summary"] = summary
        elif abstract:
            # Fallback to truncated abstract
            summary = abstract[:120] + "..." if len(abstract) > 120 else abstract
            node["summary"] = summary
        
        # Use AI-detected domain if available, otherwise extract from keywords
        domain = paper_data.get("domain") or extract_domain(paper_data.get("title", ""), abstract)
        node["domain"] = domain
        
        # Add AI-generated fields if available
        if paper_data.get("key_contributions"):
            node["key_contributions"] = paper_data["key_contributions"]
        if paper_data.get("methodology"):
            node["methodology"] = paper_data["methodology"]
        
        # First author
        authors = paper_data.get("authors", [])
        if authors:
            if isinstance(authors, list):
                node["first_author"] = authors[0]
                node["author_count"] = len(authors)
            else:
                author_list = str(authors).split(",")
                node["first_author"] = author_list[0].strip()
                node["author_count"] = len(author_list)
        
        # Publication year
        pub_date = paper_data.get("publication_date", "")
        node["year"] = pub_date[:4] if pub_date else ""
    
    node["type"] = node_type  # today, cited, expanded
    return node


@app.get("/api/papers/{arxiv_id}/insight")
def get_paper_insight(arxiv_id: str):
    generator = create_insight_generator(
        qdrant_url=QDRANT_URL,
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
    )
    try:
        insight = generator.generate_insight(arxiv_id)
        return {"arxiv_id": arxiv_id, "insight": insight}
    finally:
        generator.graph_manager.close()


@app.get("/api/papers/{arxiv_id}/detail", response_model=PaperDetail)
def get_paper_detail(arxiv_id: str):
    """Get detailed information about a specific paper"""
    graph = get_graph()
    try:
        q = (
            "MATCH (p:Paper {arxiv_id: $id}) "
            "RETURN p.arxiv_id as arxiv_id, p.title as title, p.authors as authors, "
            "p.abstract as abstract, p.pdf_url as pdf_url, p.publication_date as publication_date, "
            "p.ai_summary as ai_summary, p.domain as domain, p.key_contributions as key_contributions, "
            "p.methodology as methodology"
        )
        with graph.driver.session() as session:
            result = session.run(q, id=arxiv_id)
            record = result.single()
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Paper {arxiv_id} not found")
        
        data = record.data()
        return PaperDetail(
            arxiv_id=data["arxiv_id"],
            title=data["title"] or "Untitled",
            authors=data["authors"] or [],
            abstract=data["abstract"] or "",
            pdf_url=data["pdf_url"] or f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            publication_date=data["publication_date"] or "",
            domain=extract_domain(data.get("title", ""), data.get("abstract", ""))
        )
    finally:
        graph.close()


@app.get("/api/graph/daily", response_model=GraphResponse)
def get_graph_daily():
    from datetime import date
    graph = get_graph()
    try:
        # 1) today's papers with rich metadata
        q_today = (
            "MATCH (p:Paper) WHERE p.publication_date = $today AND p.title IS NOT NULL "
            "RETURN p.arxiv_id as id, p.title as title, p.authors as authors, "
            "p.abstract as abstract, p.publication_date as publication_date, "
            "p.ai_summary as ai_summary, p.domain as domain, p.key_contributions as key_contributions, "
            "p.methodology as methodology"
        )
        with graph.driver.session() as session:
            today = str(date.today())
            result = session.run(q_today, today=today)
            todays = [r.data() for r in result]

        # fallback: if no papers today, return latest N papers
        if not todays:
            q_latest = (
                "MATCH (p:Paper) WHERE p.publication_date IS NOT NULL AND p.title IS NOT NULL "
                "RETURN p.arxiv_id as id, p.title as title, p.authors as authors, "
                "p.abstract as abstract, p.publication_date as publication_date, "
                "p.ai_summary as ai_summary, p.domain as domain, p.key_contributions as key_contributions, "
                "p.methodology as methodology "
                "ORDER BY p.publication_date DESC LIMIT 10"
            )
            with graph.driver.session() as session:
                result = session.run(q_latest)
                todays = [r.data() for r in result]

        if not todays:
            return GraphResponse(nodes=[], links=[])

        ids = [r["id"] for r in todays]
        
        # 2) get cited papers metadata
        q_cited = (
            "MATCH (p:Paper)-[r:CITES]->(c:Paper) WHERE p.arxiv_id IN $ids "
            "RETURN DISTINCT c.arxiv_id as id, c.title as title, c.authors as authors, "
            "c.abstract as abstract, c.publication_date as publication_date"
        )
        with graph.driver.session() as session:
            result = session.run(q_cited, ids=ids)
            cited_papers = [r.data() for r in result]

        # 3) get citation relationships
        q_edges = (
            "MATCH (p:Paper)-[r:CITES]->(c:Paper) WHERE p.arxiv_id IN $ids "
            "RETURN p.arxiv_id as src, c.arxiv_id as dst"
        )
        with graph.driver.session() as session:
            result = session.run(q_edges, ids=ids)
            edges = [r.data() for r in result]

        # 4) build enriched nodes
        nodes = []
        
        # Add today's papers (featured)
        for paper in todays:
            node = enrich_node(paper, "today")
            nodes.append(node)
        
        # Add cited papers
        for paper in cited_papers:
            node = enrich_node(paper, "cited")
            nodes.append(node)

        links = [{"source": e["src"], "target": e["dst"], "type": "CITES"} for e in edges]
        return GraphResponse(nodes=nodes, links=links)
    finally:
        graph.close()


@app.get("/api/graph/expand/{arxiv_id}", response_model=GraphResponse)
def expand_node(arxiv_id: str):
    graph = get_graph()
    try:
        q = (
            "MATCH (p:Paper {arxiv_id: $id})-[r]-(n:Paper) "
            "RETURN p.arxiv_id as src, type(r) as rel, n.arxiv_id as dst, "
            "n.title as title, n.authors as authors, n.abstract as abstract, "
            "n.publication_date as publication_date"
        )
        with graph.driver.session() as session:
            result = session.run(q, id=arxiv_id)
            rows = [r.data() for r in result]
        
        if not rows:
            return GraphResponse(nodes=[{"id": arxiv_id}], links=[])
        
        # Build node map
        nodes_map = {arxiv_id: {"id": arxiv_id, "type": "center"}}
        links = []
        
        for r in rows:
            dst = r["dst"]
            rel_type = r["rel"]
            
            # Create enriched node for neighbor
            neighbor_data = {
                "id": dst,
                "title": r.get("title"),
                "authors": r.get("authors"),
                "abstract": r.get("abstract"),
                "publication_date": r.get("publication_date")
            }
            
            if dst not in nodes_map:
                nodes_map[dst] = enrich_node(neighbor_data, "expanded")
            
            # Add link with proper direction
            if rel_type == "CITES":
                links.append({"source": r["src"], "target": dst, "type": "CITES"})
            else:  # reverse citation
                links.append({"source": dst, "target": r["src"], "type": "CITES"})
        
        return GraphResponse(nodes=list(nodes_map.values()), links=links)
    finally:
        graph.close()


@app.get("/")
def root():
    return {"message": "DigitalPaperAgent API", "docs": "/docs"}