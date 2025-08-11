"""AI-powered paper summarization module"""

from __future__ import annotations

import os
import re
from typing import List, Tuple, Optional
from loguru import logger

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


class PaperSummarizer:
    """AI-powered paper summarizer that generates detailed summaries from PDF content"""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        model_name: str = "openai/gpt-oss-20b",
    ):
        self.model_name = model_name
        
        # Initialize LLM client based on available environment variables
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            if groq is None:
                raise RuntimeError("GROQ_API_KEY is set, but groq package not installed. Install with: pip install groq")
            logger.info("Using Groq client for AI summarization")
            self.llm_client = groq.Groq(api_key=groq_api_key)
        else:
            if openai is None:
                raise RuntimeError("openai package not installed. Install with: pip install openai")
            logger.info("Using OpenAI-compatible client for AI summarization")
            self.llm_client = openai.OpenAI(
                api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
                base_url=openai_base_url or os.getenv("OPENAI_BASE_URL"),
            )

    def extract_key_sections(self, full_text: str) -> dict:
        """Extract key sections from paper text"""
        sections = {
            "abstract": "",
            "introduction": "",
            "methodology": "",
            "results": "",
            "conclusion": "",
            "main_content": ""
        }
        
        # Simple section extraction based on common patterns
        text_lower = full_text.lower()
        
        # Try to find abstract
        abstract_match = re.search(r'abstract\s*\n(.*?)(?:\n\s*(?:introduction|1\.?\s*introduction))', text_lower, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            sections["abstract"] = abstract_match.group(1).strip()
        
        # Try to find introduction
        intro_match = re.search(r'(?:introduction|1\.?\s*introduction)\s*\n(.*?)(?:\n\s*(?:2\.|method|approach|related work))', text_lower, re.DOTALL | re.IGNORECASE)
        if intro_match:
            sections["introduction"] = intro_match.group(1).strip()[:1000]  # Limit length
        
        # Try to find methodology/method section
        method_match = re.search(r'(?:method|approach|methodology|2\.)\s*\n(.*?)(?:\n\s*(?:3\.|result|experiment|evaluation))', text_lower, re.DOTALL | re.IGNORECASE)
        if method_match:
            sections["methodology"] = method_match.group(1).strip()[:1000]
        
        # Try to find conclusion
        conclusion_match = re.search(r'(?:conclusion|discussion|summary)\s*\n(.*?)(?:\n\s*(?:reference|acknowledgment|appendix))', text_lower, re.DOTALL | re.IGNORECASE)
        if conclusion_match:
            sections["conclusion"] = conclusion_match.group(1).strip()[:800]
        
        # Get main content (first 2000 chars as fallback)
        sections["main_content"] = full_text[:2000]
        
        return sections

    def detect_domain(self, title: str, abstract: str) -> str:
        """Detect research domain based on title and abstract"""
        text = f"{title} {abstract}".lower()
        
        # Domain keywords mapping
        domain_keywords = {
            "Computer Vision": ["computer vision", "image", "visual", "object detection", "segmentation", "cnn", "convolution"],
            "Natural Language Processing": ["nlp", "language", "text", "linguistic", "bert", "transformer", "chatbot", "dialogue"],
            "Machine Learning": ["machine learning", "neural network", "deep learning", "training", "optimization", "gradient"],
            "Reinforcement Learning": ["reinforcement", "reward", "policy", "agent", "environment", "q-learning"],
            "Robotics": ["robot", "robotic", "manipulation", "navigation", "autonomous", "control"],
            "Speech Processing": ["speech", "audio", "voice", "acoustic", "phoneme", "asr"],
            "Information Retrieval": ["retrieval", "search", "ranking", "recommendation", "information"],
            "Artificial Intelligence": ["artificial intelligence", "ai", "intelligent", "reasoning", "knowledge"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text for keyword in keywords):
                return domain
        
        return "Computer Science"  # Default domain

    def generate_comprehensive_summary(
        self, 
        paper_meta: PaperMetadata, 
        full_text: str, 
        max_length: int = 400
    ) -> Tuple[str, str, List[str], str]:
        """
        Generate comprehensive AI summary from paper content
        
        Returns:
            Tuple of (ai_summary, domain, key_contributions, methodology)
        """
        logger.info("Generating AI summary for paper: {}", paper_meta.title)
        
        # Extract key sections
        sections = self.extract_key_sections(full_text)
        
        # Detect domain
        domain = self.detect_domain(paper_meta.title, paper_meta.abstract)
        
        # Build prompt for AI summarization
        prompt = self._build_summarization_prompt(paper_meta, sections, max_length)
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3,  # Lower temperature for more consistent summaries
            )
            
            result = response.choices[0].message.content
            logger.debug("Raw AI response: {}", result[:200] + "..." if len(result) > 200 else result)
            
            # Parse the structured response
            ai_summary, key_contributions, methodology = self._parse_ai_response(result)
            
            # If parsing failed, use the entire response as summary
            if not ai_summary and result:
                ai_summary = result[:max_length]
                logger.warning("Structured parsing failed, using raw response as summary")
            
            logger.info("Successfully generated AI summary for: {} (summary_len={})", paper_meta.title, len(ai_summary))
            return ai_summary, domain, key_contributions, methodology
            
        except Exception as e:
            logger.warning("Failed to generate AI summary for {}: {}", paper_meta.title, e)
            # Fallback to original abstract with domain
            fallback_summary = f"[{domain}] {paper_meta.abstract}"
            if len(fallback_summary) > max_length:
                fallback_summary = fallback_summary[:max_length-3] + "..."
            return fallback_summary, domain, [], ""

    def _build_summarization_prompt(self, paper_meta: PaperMetadata, sections: dict, max_length: int) -> str:
        """Build prompt for AI summarization"""
        
        content_sections = []
        if sections["abstract"]:
            content_sections.append(f"Abstract: {sections['abstract'][:300]}")
        if sections["introduction"]:
            content_sections.append(f"Introduction: {sections['introduction'][:500]}")
        if sections["methodology"]:
            content_sections.append(f"Methodology: {sections['methodology'][:500]}")
        if sections["conclusion"]:
            content_sections.append(f"Conclusion: {sections['conclusion'][:300]}")
        
        # Fallback to main content if no sections found
        if not content_sections:
            content_sections.append(f"Main Content: {sections['main_content']}")
        
        prompt = f"""Please analyze this research paper and provide a structured summary:

Title: {paper_meta.title}
Authors: {', '.join(paper_meta.authors[:3])}{'...' if len(paper_meta.authors) > 3 else ''}

Content Sections:
{chr(10).join(content_sections)}

Please provide a response in exactly this format:

SUMMARY: [Write a comprehensive {max_length}-character summary that captures the main contribution, approach, and significance. Make it informative and engaging.]

CONTRIBUTIONS: [List 2-3 key technical contributions, separated by " | "]

METHODOLOGY: [Brief description of the main technical approach or method used]

Requirements:
- Summary should be exactly around {max_length} characters
- Focus on technical contributions and innovations
- Use clear, professional language
- Highlight what makes this work unique or important"""

        return prompt

    def _parse_ai_response(self, response: str) -> Tuple[str, List[str], str]:
        """Parse structured AI response - improved with flexible parsing"""
        summary = ""
        contributions = []
        methodology = ""
        
        if not response:
            return summary, contributions, methodology
        
        try:
            # Try structured parsing first
            summary_match = re.search(r'SUMMARY:\s*(.*?)(?=\n\s*CONTRIBUTIONS:|$)', response, re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()
            
            contrib_match = re.search(r'CONTRIBUTIONS:\s*(.*?)(?=\n\s*METHODOLOGY:|$)', response, re.DOTALL)
            if contrib_match:
                contrib_text = contrib_match.group(1).strip()
                contributions = [c.strip() for c in contrib_text.split("|") if c.strip()]
            
            method_match = re.search(r'METHODOLOGY:\s*(.*?)$', response, re.DOTALL)
            if method_match:
                methodology = method_match.group(1).strip()
            
            # If structured parsing didn't work, try alternative patterns
            if not summary:
                # Look for other summary indicators
                alt_patterns = [
                    r'(?:摘要|Summary|总结)[:：]\s*(.*?)(?=\n|$)',
                    r'(?:核心内容|Core Content)[:：]\s*(.*?)(?=\n|$)',
                    r'^(.*?)(?=\n\n|\n[A-Z]|\n\d+\.)',  # First paragraph
                ]
                for pattern in alt_patterns:
                    match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                    if match and len(match.group(1).strip()) > 50:  # Minimum meaningful length
                        summary = match.group(1).strip()
                        break
                
        except Exception as e:
            logger.warning("Failed to parse AI response structure: {}", e)
        
        # Final fallback: if no structured content found, use response as summary
        if not summary and response:
            # Clean up the response and use as summary
            cleaned = re.sub(r'\n+', ' ', response).strip()
            summary = cleaned[:400] if len(cleaned) > 400 else cleaned
            
        return summary, contributions, methodology


def create_paper_summarizer(
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    model_name: str = "openai/gpt-oss-20b",
) -> PaperSummarizer:
    """Create PaperSummarizer instance"""
    return PaperSummarizer(
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        model_name=model_name,
    )
