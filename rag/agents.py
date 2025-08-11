"""AI Agents using LangGraph for paper analysis tasks"""

from __future__ import annotations

import os
from typing import List, Dict, Any, TypedDict, Annotated
from loguru import logger

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate

from models import PaperMetadata


class PaperAnalysisState(TypedDict):
    """State for paper analysis agent workflow"""
    paper_metadata: PaperMetadata
    full_text: str
    extracted_sections: Dict[str, str]
    ai_summary: str
    domain: str
    key_contributions: List[str]
    methodology: str
    confidence_scores: Dict[str, float]
    messages: Annotated[list, add_messages]


class PaperAnalysisAgents:
    """LangGraph-based agents for comprehensive paper analysis"""
    
    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        self.model_name = model_name
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.llm = ChatGroq(
            model=model_name,
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Build the agent workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for paper analysis"""
        workflow = StateGraph(PaperAnalysisState)
        
        # Add nodes for different analysis tasks
        workflow.add_node("extract_sections", self._extract_sections_agent)
        workflow.add_node("analyze_domain", self._domain_analysis_agent)  
        workflow.add_node("extract_methodology", self._methodology_extraction_agent)
        workflow.add_node("identify_contributions", self._contributions_identification_agent)
        workflow.add_node("generate_summary", self._summary_generation_agent)
        workflow.add_node("quality_assessment", self._quality_assessment_agent)
        
        # Define the workflow edges
        workflow.add_edge(START, "extract_sections")
        workflow.add_edge("extract_sections", "analyze_domain")
        workflow.add_edge("analyze_domain", "extract_methodology")
        workflow.add_edge("extract_methodology", "identify_contributions")
        workflow.add_edge("identify_contributions", "generate_summary")
        workflow.add_edge("generate_summary", "quality_assessment")
        workflow.add_edge("quality_assessment", END)
        
        return workflow.compile()
    
    def analyze_paper(self, paper_metadata: PaperMetadata, full_text: str) -> Dict[str, Any]:
        """Run the complete paper analysis workflow"""
        logger.info("Starting LangGraph paper analysis for: {}", paper_metadata.title)
        
        initial_state = PaperAnalysisState(
            paper_metadata=paper_metadata,
            full_text=full_text,
            extracted_sections={},
            ai_summary="",
            domain="",
            key_contributions=[],
            methodology="",
            confidence_scores={},
            messages=[]
        )
        
        # Execute the workflow
        final_state = self.workflow.invoke(initial_state)
        
        logger.info("Completed LangGraph paper analysis for: {}", paper_metadata.title)
        
        return {
            "ai_summary": final_state["ai_summary"],
            "domain": final_state["domain"],
            "key_contributions": final_state["key_contributions"],
            "methodology": final_state["methodology"],
            "confidence_scores": final_state["confidence_scores"]
        }
    
    def _extract_sections_agent(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """Agent to extract key sections from paper text"""
        logger.debug("Running section extraction agent")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing academic papers. Extract the key sections from the following paper text.
            
Your task:
1. Identify and extract the ABSTRACT section
2. Identify and extract the INTRODUCTION section  
3. Identify and extract the METHODOLOGY/METHOD section
4. Identify and extract the RESULTS/EXPERIMENTS section
5. Identify and extract the CONCLUSION section

Return your response in this exact format:
ABSTRACT: [extracted abstract text]
INTRODUCTION: [extracted introduction text]
METHODOLOGY: [extracted methodology text]
RESULTS: [extracted results text]
CONCLUSION: [extracted conclusion text]

If a section is not found, write "NOT_FOUND" for that section."""),
            ("human", "Paper Title: {title}\n\nPaper Text:\n{full_text}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            title=state["paper_metadata"].title,
            full_text=state["full_text"][:8000]  # Limit text length
        ))
        
        # Parse the response to extract sections
        sections = self._parse_sections_response(response.content)
        state["extracted_sections"] = sections
        state["messages"].append(HumanMessage(content=f"Extracted {len(sections)} sections"))
        
        return state
    
    def _domain_analysis_agent(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """Agent to analyze and classify the research domain"""
        logger.debug("Running domain analysis agent")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at classifying academic papers by research domain.

Based on the paper title, abstract, and methodology, classify this paper into ONE of these domains:
- Natural Language Processing
- Computer Vision  
- Machine Learning
- Deep Learning
- Reinforcement Learning
- Robotics
- Speech Processing
- Information Retrieval
- Artificial Intelligence
- Data Mining
- Human-Computer Interaction
- Computer Graphics
- Cybersecurity
- Computer Systems
- Computational Biology

Return ONLY the domain name, nothing else."""),
            ("human", """Title: {title}
Abstract: {abstract}
Methodology: {methodology}""")
        ])
        
        methodology_text = state["extracted_sections"].get("METHODOLOGY", "")
        
        response = self.llm.invoke(prompt.format_messages(
            title=state["paper_metadata"].title,
            abstract=state["paper_metadata"].abstract,
            methodology=methodology_text[:500]
        ))
        
        domain = response.content.strip()
        state["domain"] = domain
        state["messages"].append(HumanMessage(content=f"Classified domain as: {domain}"))
        
        return state
    
    def _methodology_extraction_agent(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """Specialized agent for extracting methodology information"""
        logger.debug("Running methodology extraction agent")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting methodology information from academic papers.

Your task is to provide a concise 2-3 sentence summary of the main technical approach or method used in this paper.

Focus on:
- The core algorithm, technique, or approach
- Key architectural components or design choices
- Main experimental setup or evaluation method

Keep it technical but accessible. Return ONLY the methodology summary, no additional text."""),
            ("human", """Paper Title: {title}

Abstract: {abstract}

Methodology Section: {methodology_section}

Introduction: {introduction}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            title=state["paper_metadata"].title,
            abstract=state["paper_metadata"].abstract,
            methodology_section=state["extracted_sections"].get("METHODOLOGY", "")[:1000],
            introduction=state["extracted_sections"].get("INTRODUCTION", "")[:500]
        ))
        
        methodology = response.content.strip()
        state["methodology"] = methodology
        state["messages"].append(HumanMessage(content=f"Extracted methodology: {methodology[:100]}..."))
        
        return state
    
    def _contributions_identification_agent(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """Agent to identify key contributions of the paper"""
        logger.debug("Running contributions identification agent")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at identifying key contributions in academic papers.

Extract the 2-4 main technical contributions of this paper. Each contribution should be:
- Specific and concrete
- Technically meaningful
- Novel or innovative

Return your response as a numbered list:
1. [First contribution]
2. [Second contribution]
3. [Third contribution]
etc.

Focus on technical innovations, new methods, or significant improvements over existing work."""),
            ("human", """Title: {title}

Abstract: {abstract}

Introduction: {introduction}

Conclusion: {conclusion}""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            title=state["paper_metadata"].title,
            abstract=state["paper_metadata"].abstract,
            introduction=state["extracted_sections"].get("INTRODUCTION", "")[:800],
            conclusion=state["extracted_sections"].get("CONCLUSION", "")[:800]
        ))
        
        # Parse numbered list into contributions
        contributions = self._parse_contributions_response(response.content)
        state["key_contributions"] = contributions
        state["messages"].append(HumanMessage(content=f"Identified {len(contributions)} contributions"))
        
        return state
    
    def _summary_generation_agent(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """Agent to generate comprehensive summary"""
        logger.debug("Running summary generation agent")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical writer specializing in academic paper summaries.

Create a comprehensive 300-character summary that captures:
- The main problem being addressed
- The key technical approach/solution
- The significance of the results

Make it informative yet accessible. Focus on what makes this work important and unique."""),
            ("human", """Title: {title}
Domain: {domain}
Abstract: {abstract}
Methodology: {methodology}
Key Contributions: {contributions}""")
        ])
        
        contributions_text = " | ".join(state["key_contributions"])
        
        response = self.llm.invoke(prompt.format_messages(
            title=state["paper_metadata"].title,
            domain=state["domain"],
            abstract=state["paper_metadata"].abstract[:400],
            methodology=state["methodology"],
            contributions=contributions_text
        ))
        
        summary = response.content.strip()
        state["ai_summary"] = summary
        state["messages"].append(HumanMessage(content=f"Generated summary: {len(summary)} chars"))
        
        return state
    
    def _quality_assessment_agent(self, state: PaperAnalysisState) -> PaperAnalysisState:
        """Agent to assess the quality of extracted information"""
        logger.debug("Running quality assessment agent")
        
        # Simple heuristic-based quality assessment
        confidence_scores = {
            "domain": 0.9 if state["domain"] and state["domain"] != "NOT_FOUND" else 0.3,
            "methodology": 0.8 if len(state["methodology"]) > 50 else 0.4,
            "contributions": 0.9 if len(state["key_contributions"]) >= 2 else 0.5,
            "summary": 0.8 if 200 <= len(state["ai_summary"]) <= 400 else 0.6
        }
        
        state["confidence_scores"] = confidence_scores
        state["messages"].append(HumanMessage(content=f"Quality assessment completed: avg={sum(confidence_scores.values())/len(confidence_scores):.2f}"))
        
        return state
    
    def _parse_sections_response(self, response: str) -> Dict[str, str]:
        """Parse the sections extraction response"""
        sections = {}
        current_section = None
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and line.split(':')[0].strip().upper() in ['ABSTRACT', 'INTRODUCTION', 'METHODOLOGY', 'RESULTS', 'CONCLUSION']:
                parts = line.split(':', 1)
                current_section = parts[0].strip().upper()
                if len(parts) > 1 and parts[1].strip() != "NOT_FOUND":
                    sections[current_section] = parts[1].strip()
            elif current_section and line and not line.startswith(tuple(['ABSTRACT:', 'INTRODUCTION:', 'METHODOLOGY:', 'RESULTS:', 'CONCLUSION:'])):
                if current_section in sections:
                    sections[current_section] += " " + line
                else:
                    sections[current_section] = line
        
        return sections
    
    def _parse_contributions_response(self, response: str) -> List[str]:
        """Parse the contributions response into a list"""
        contributions = []
        for line in response.split('\n'):
            line = line.strip()
            # Look for numbered items
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering/bullets and clean up
                cleaned = line.lstrip('0123456789.-• ').strip()
                if cleaned and len(cleaned) > 10:  # Minimum meaningful length
                    contributions.append(cleaned)
        
        return contributions[:4]  # Limit to 4 contributions


def create_paper_analysis_agents(model_name: str = "openai/gpt-oss-20b") -> PaperAnalysisAgents:
    """Create PaperAnalysisAgents instance"""
    return PaperAnalysisAgents(model_name=model_name)
