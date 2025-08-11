from __future__ import annotations

from typing import List
from neo4j import GraphDatabase
from loguru import logger
from models import PaperMetadata


class Neo4jManager:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def add_paper(self, paper_meta: PaperMetadata) -> None:
        with self.driver.session() as session:
            session.execute_write(self._create_paper_node, paper_meta)

    @staticmethod
    def _create_paper_node(tx, paper_meta: PaperMetadata):
        query = (
            "MERGE (p:Paper {arxiv_id: $arxiv_id}) "
            "ON CREATE SET p.title=$title, p.authors=$authors, p.abstract=$abstract, "
            "p.pdf_url=$pdf_url, p.publication_date=$publication_date, "
            "p.ai_summary=$ai_summary, p.domain=$domain, p.key_contributions=$key_contributions, "
            "p.methodology=$methodology "
            "ON MATCH SET p.title=$title, p.authors=$authors, p.abstract=$abstract, "
            "p.pdf_url=$pdf_url, p.publication_date=$publication_date, "
            "p.ai_summary=$ai_summary, p.domain=$domain, p.key_contributions=$key_contributions, "
            "p.methodology=$methodology"
        )
        tx.run(query, **paper_meta.model_dump())

    def add_citations(self, paper_id: str, cited_ids: List[str]) -> None:
        if not cited_ids:
            return
        with self.driver.session() as session:
            session.execute_write(self._create_citation_rels, paper_id, cited_ids)

    @staticmethod
    def _create_citation_rels(tx, paper_id: str, cited_ids: List[str]):
        query = (
            "MATCH (source:Paper {arxiv_id: $paper_id}) "
            "FOREACH (cid IN $cited_ids | "
            "  MERGE (cited:Paper {arxiv_id: cid}) "
            "  MERGE (source)-[:CITES]->(cited)"
            ")"
        )
        tx.run(query, paper_id=paper_id, cited_ids=cited_ids)

    def get_paper_metadata(self, arxiv_id: str) -> PaperMetadata:
        """获取单篇论文的完整元数据"""
        with self.driver.session() as session:
            result = session.execute_read(self._get_paper_metadata, arxiv_id)
            if not result:
                raise ValueError(f"Paper {arxiv_id} not found in graph database")
            return result

    @staticmethod
    def _get_paper_metadata(tx, arxiv_id: str):
        query = (
            "MATCH (p:Paper {arxiv_id: $arxiv_id}) "
            "RETURN p.arxiv_id as arxiv_id, p.title as title, p.authors as authors, "
            "p.abstract as abstract, p.pdf_url as pdf_url, p.publication_date as publication_date, "
            "p.ai_summary as ai_summary, p.domain as domain, p.key_contributions as key_contributions, "
            "p.methodology as methodology"
        )
        result = tx.run(query, arxiv_id=arxiv_id)
        record = result.single()
        if record:
            return PaperMetadata(
                arxiv_id=record["arxiv_id"],
                title=record["title"] or "",
                authors=record["authors"] or [],
                abstract=record["abstract"] or "",
                pdf_url=record["pdf_url"] or "",
                publication_date=record["publication_date"] or "",
                ai_summary=record["ai_summary"],
                domain=record["domain"],
                key_contributions=record["key_contributions"],
                methodology=record["methodology"]
            )
        return None

    def get_cited_papers_metadata(self, arxiv_id: str, limit: int = 5) -> List[PaperMetadata]:
        """获取指定论文引用的其他论文的元数据"""
        with self.driver.session() as session:
            return session.execute_read(self._get_cited_papers_metadata, arxiv_id, limit)

    @staticmethod
    def _get_cited_papers_metadata(tx, arxiv_id: str, limit: int):
        query = (
            "MATCH (source:Paper {arxiv_id: $arxiv_id})-[:CITES]->(cited:Paper) "
            "WHERE cited.title IS NOT NULL AND cited.abstract IS NOT NULL "
            "RETURN cited.arxiv_id as arxiv_id, cited.title as title, cited.authors as authors, "
            "cited.abstract as abstract, cited.pdf_url as pdf_url, cited.publication_date as publication_date, "
            "cited.ai_summary as ai_summary, cited.domain as domain, cited.key_contributions as key_contributions, "
            "cited.methodology as methodology "
            "LIMIT $limit"
        )
        result = tx.run(query, arxiv_id=arxiv_id, limit=limit)
        papers = []
        for record in result:
            papers.append(PaperMetadata(
                arxiv_id=record["arxiv_id"],
                title=record["title"] or "",
                authors=record["authors"] or [],
                abstract=record["abstract"] or "",
                pdf_url=record["pdf_url"] or "",
                publication_date=record["publication_date"] or "",
                ai_summary=record["ai_summary"],
                domain=record["domain"],
                key_contributions=record["key_contributions"],
                methodology=record["methodology"]
            ))
        return papers

    def get_incomplete_cited_papers(self, limit: int = 100) -> List[str]:
        """获取图中缺少元数据的被引论文ID列表"""
        with self.driver.session() as session:
            return session.execute_read(self._get_incomplete_cited_papers, limit)

    @staticmethod
    def _get_incomplete_cited_papers(tx, limit: int):
        query = (
            "MATCH (p:Paper) "
            "WHERE p.title IS NULL OR p.abstract IS NULL "
            "RETURN p.arxiv_id as arxiv_id "
            "LIMIT $limit"
        )
        result = tx.run(query, limit=limit)
        return [record["arxiv_id"] for record in result]

    def backfill_papers_metadata(self, papers_list: List[PaperMetadata]) -> None:
        """批量补全论文元数据"""
        with self.driver.session() as session:
            for paper in papers_list:
                session.execute_write(self._update_paper_metadata, paper)

    @staticmethod
    def _update_paper_metadata(tx, paper_meta: PaperMetadata):
        query = (
            "MATCH (p:Paper {arxiv_id: $arxiv_id}) "
            "SET p.title = $title, p.authors = $authors, p.abstract = $abstract, "
            "p.pdf_url = $pdf_url, p.publication_date = $publication_date, "
            "p.ai_summary = $ai_summary, p.domain = $domain, p.key_contributions = $key_contributions, "
            "p.methodology = $methodology"
        )
        tx.run(query, **paper_meta.model_dump())


