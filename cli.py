import os
import typer
from typing import Optional
from pipelines.process_pdf import process_pdf_command
from pipelines.process_paper import process_and_ingest_paper, backfill_cited_papers_metadata
from sources.arxiv_fetcher import fetch_papers_by_ids
from graph.neo4j_manager import Neo4jManager
from qdrant_client import QdrantClient
from rag.insights import create_insight_generator
from dotenv import load_dotenv


load_dotenv()  # Load env vars from .env if present
app = typer.Typer(help="Agent crawler CLI")


@app.command("process-pdf")
def cmd_process_pdf(
    url_arg: Optional[str] = typer.Argument(None, help="PDF URL as positional argument"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="PDF URL (alternative to positional)"),
    paper_id: Optional[str] = typer.Option(None, "--paper-id", "-p", help="Override paper id"),
):
    effective_url = url or url_arg
    if not effective_url:
        raise typer.BadParameter("Please provide a PDF URL as positional argument or via --url/-u")
    process_pdf_command(url=effective_url, paper_id=paper_id)


@app.command("ingest-arxiv")
def ingest_arxiv(
    arxiv_id: str = typer.Argument(..., help="arXiv ID to ingest, e.g., 1706.03762"),
    neo4j_uri: str = typer.Option("bolt://localhost:7687", help="Neo4j bolt URI"),
    neo4j_user: str = typer.Option("neo4j", help="Neo4j user"),
    neo4j_password: str = typer.Option("neo4j_password", help="Neo4j password"),
):
    papers = fetch_papers_by_ids([arxiv_id])
    if not papers:
        raise typer.BadParameter(f"arXiv id not found: {arxiv_id}")
    paper = papers[0]
    qdrant = QdrantClient(url="http://localhost:6333")
    graph = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
    try:
        process_and_ingest_paper(paper, qdrant, graph)
    finally:
        graph.close()


@app.command("get-insight")
def get_insight(
    arxiv_id: str = typer.Argument(..., help="arXiv ID to generate insight for, e.g., 1706.03762"),
    neo4j_uri: str = typer.Option("bolt://localhost:7687", envvar="NEO4J_URI", help="Neo4j bolt URI"),
    neo4j_user: str = typer.Option("neo4j", envvar="NEO4J_USER", help="Neo4j user"),
    neo4j_password: str = typer.Option("neo4j_password", envvar="NEO4J_PASSWORD", help="Neo4j password"),
    qdrant_url: str = typer.Option("http://localhost:6333", envvar="QDRANT_URL", help="Qdrant URL"),
    openai_api_key: Optional[str] = typer.Option(None, envvar="OPENAI_API_KEY", help="OpenAI API key (or provider key)"),
    openai_base_url: Optional[str] = typer.Option(None, envvar="OPENAI_BASE_URL", help="OpenAI-compatible base URL (e.g., vLLM/OpenRouter/Groq if compatible)"),
    model_name: str = typer.Option(os.getenv("MODEL_NAME", "openai/gpt-oss-20b"), help="LLM model name (env: MODEL_NAME)"),
):
    """生成指定arXiv论文的深度洞察分析"""
    try:
        # 创建insight生成器
        generator = create_insight_generator(
            qdrant_url=qdrant_url,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            model_name=model_name,
        )
        
        # 生成洞察
        insight = generator.generate_insight(arxiv_id)
        
        # 输出结果
        print(f"\n{'='*60}")
        print(f"论文洞察分析: {arxiv_id}")
        print(f"{'='*60}")
        print(insight)
        print(f"{'='*60}\n")
        
    except Exception as e:
        typer.echo(f"错误：{e}", err=True)
        raise typer.Exit(1)
    finally:
        # 清理资源
        try:
            generator.graph_manager.close()
        except:
            pass


@app.command("backfill-metadata")
def backfill_metadata_cmd(
    neo4j_uri: str = typer.Option("bolt://localhost:7687", envvar="NEO4J_URI", help="Neo4j bolt URI"),
    neo4j_user: str = typer.Option("neo4j", envvar="NEO4J_USER", help="Neo4j user"),
    neo4j_password: str = typer.Option("neo4j_password", envvar="NEO4J_PASSWORD", help="Neo4j password"),
):
    """批量补全图中缺少元数据的被引论文"""
    graph = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
    try:
        backfill_cited_papers_metadata(graph)
        print("✅ 被引论文元数据补全完成")
    finally:
        graph.close()


if __name__ == "__main__":
    app()



