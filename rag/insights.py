from __future__ import annotations

import os
from typing import List, Optional
from loguru import logger

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from graph.neo4j_manager import Neo4jManager
from models import PaperMetadata
from pipelines.process_pdf import build_text_embedder

try:
    import openai
except ImportError:
    openai = None
try:
    import groq
except ImportError:
    groq = None


class InsightGenerator:
    """论文洞察生成器，结合Qdrant向量检索和Neo4j图检索"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        graph_manager: Neo4jManager,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
    ):
        self.qdrant_client = qdrant_client
        self.graph_manager = graph_manager
        self.model_name = model_name
        
        # 初始化文本嵌入器
        self.text_embedder = build_text_embedder()
        
        # Initialize LLM client based on available environment variables
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            if groq is None:
                raise RuntimeError("GROQ_API_KEY is set, but groq package not installed. Install with: pip install groq")
            logger.info("Using Groq client as GROQ_API_KEY is set.")
            self.llm_client = groq.Groq(api_key=groq_api_key)
        else:
            if openai is None:
                raise RuntimeError("openai package not installed. Install with: pip install openai")
            logger.info("Using OpenAI-compatible client.")
            self.llm_client = openai.OpenAI(
                api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
                base_url=openai_base_url or os.getenv("OPENAI_BASE_URL"),
            )

    def generate_insight(self, arxiv_id: str, max_cited_papers: int = 5, max_content_chunks: int = 5) -> str:
        """
        为指定arXiv论文生成深度洞察
        
        Args:
            arxiv_id: arXiv论文ID
            max_cited_papers: 最多获取的被引论文数量
            max_content_chunks: 最多获取的内容块数量
        
        Returns:
            生成的论文洞察文本
        """
        logger.info("Generating insight for paper: {}", arxiv_id)
        
        # 1. 从图数据库获取论文基本信息
        try:
            paper_meta = self.graph_manager.get_paper_metadata(arxiv_id)
        except ValueError as e:
            return f"错误：无法找到论文 {arxiv_id}。请先运行 'ingest-arxiv {arxiv_id}' 来获取该论文的数据。"
        
        # 2. Qdrant内部检索：获取该论文的核心内容块
        core_chunks = self._retrieve_paper_content(paper_meta, max_content_chunks)
        
        # 3. Neo4j引用链检索：获取被引论文的元数据
        cited_papers = self.graph_manager.get_cited_papers_metadata(arxiv_id, max_cited_papers)
        
        # 4. 构建超级prompt
        prompt = self._build_insight_prompt(paper_meta, core_chunks, cited_papers)
        
        # 5. 调用LLM生成洞察
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7,
            )
            insight = response.choices[0].message.content
            logger.info("Successfully generated insight for paper: {}", arxiv_id)
            return insight
        except Exception as e:
            logger.error("Failed to generate insight: {}", e)
            return f"生成洞察时出错：{e}"

    def _retrieve_paper_content(self, paper_meta: PaperMetadata, limit: int) -> List[str]:
        """从Qdrant检索论文的核心内容块"""
        try:
            # 使用论文标题和摘要作为查询向量
            query_text = f"{paper_meta.title}\n{paper_meta.abstract}"
            query_vector = self.text_embedder.encode(query_text, normalize_embeddings=True)

            from qdrant_client.models import NamedVector

            def _search_with_id(pid: str):
                return self.qdrant_client.search(
                    collection_name="papers",
                    query_vector=NamedVector(name="text", vector=query_vector.tolist()),
                    query_filter=Filter(
                        must=[
                            FieldCondition(key="paper_id", match=MatchValue(value=pid)),
                            FieldCondition(key="chunk_type", match=MatchValue(value="text")),
                        ]
                    ),
                    limit=limit,
                    with_payload=True,
                )

            ids_to_try = [paper_meta.arxiv_id]
            base_id = paper_meta.arxiv_id.split("v")[0]
            if base_id != paper_meta.arxiv_id:
                ids_to_try.append(base_id)

            for pid in ids_to_try:
                try:
                    results = _search_with_id(pid)
                    content_chunks: List[str] = []
                    for hit in results:
                        if hit.payload and hit.payload.get("content"):
                            content_chunks.append(hit.payload["content"])
                    if content_chunks:
                        logger.info("Retrieved {} content chunks for paper {} (filter pid={})", len(content_chunks), paper_meta.arxiv_id, pid)
                        return content_chunks
                except Exception as e:  # continue to next id
                    logger.debug("Qdrant search failed for pid {}: {}", pid, e)

            logger.info("Retrieved 0 content chunks for paper {} after trying IDs {}", paper_meta.arxiv_id, ids_to_try)
            return []

        except Exception as e:
            logger.warning("Failed to retrieve paper content from Qdrant: {}", e)
            return []

    def _build_insight_prompt(
        self, 
        paper_meta: PaperMetadata, 
        core_chunks: List[str], 
        cited_papers: List[PaperMetadata]
    ) -> str:
        """构建用于生成洞察的超级prompt"""
        
        # 核心内容部分
        core_content_section = ""
        if core_chunks:
            core_content_section = f"""
## 论文核心内容
基于最相关的文本片段：
{chr(10).join([f"- {chunk[:200]}..." if len(chunk) > 200 else f"- {chunk}" for chunk in core_chunks[:3]])}
"""
        else:
            core_content_section = f"""
## 论文基本信息
标题：{paper_meta.title}
摘要：{paper_meta.abstract[:500]}...
"""

        # 被引论文部分
        cited_section = ""
        if cited_papers:
            cited_info = []
            for paper in cited_papers:
                cited_info.append(f"• '{paper.title}' ({paper.publication_date}): {paper.abstract[:150]}...")
            cited_section = f"""
## 基础研究（被引论文）
该论文建立在以下先前研究基础上：
{chr(10).join(cited_info)}
"""
        else:
            cited_section = """
## 基础研究（被引论文）
未能检索到该论文引用的相关论文的详细信息。
"""

        # 构建完整prompt
        prompt = f"""你是一位AI研究专家，请为论文 "{paper_meta.title}" 提供深度洞察分析。

{core_content_section}

{cited_section}

## 分析任务
请基于以上信息，提供一个结构化的深度分析，包括：

1. **核心贡献**：总结该论文的主要技术创新和学术贡献
2. **方法特色**：分析论文采用的关键方法或技术路线
3. **历史脉络**：说明该工作如何建立在已有研究基础上，解决了什么问题
4. **技术影响**：评估该研究对相关领域可能产生的影响

请用中文回答，语言专业且易理解。如果信息不足，请明确指出并基于现有信息给出合理的分析。"""

        return prompt


def create_insight_generator(
    qdrant_url: str = "http://localhost:6333",
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "neo4j_password",
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    model_name: str = "gpt-3.5-turbo",
) -> InsightGenerator:
    """创建InsightGenerator实例的便捷函数"""
    qdrant_client = QdrantClient(url=qdrant_url)
    graph_manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
    
    return InsightGenerator(
        qdrant_client=qdrant_client,
        graph_manager=graph_manager,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        model_name=model_name,
    )
