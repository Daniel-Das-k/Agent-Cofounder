from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict

load_dotenv()

class WebResearchAgent(BaseModel):
    """Enhanced web research agent with selective research and citation support"""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Define fields to avoid validation errors (excluded from serialization)
    client: Optional[object] = None
    grounding_tool: Optional[object] = None
    config: Optional[object] = None
    
    def model_dump(self, **kwargs):
        """Custom serialization that excludes non-serializable fields for pydantic graph compatibility"""
        # Return minimal serializable data for graph state management
        return {"agent_type": "WebResearchAgent", "status": "active", "capabilities": ["selective_research", "smart_citations"]}
    
    @classmethod
    def model_validate(cls, obj):
        """Custom validation that creates a new instance for graph-based message history compatibility"""
        if isinstance(obj, dict):
            return cls()
        return cls()
    
    def model_post_init(self, __context):
        """Initialize the research agent after model creation for graph integration"""
        super().model_post_init(__context)
        try:
            self.client = genai.Client()
            self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
            self.config = types.GenerateContentConfig(tools=[self.grounding_tool])
        except Exception as e:
            print(f"Warning: Research agent initialization failed: {e}")
            # Graceful fallback - agent will work without research capabilities
            self.client = None
            self.grounding_tool = None
            self.config = None
    
    def should_include_citations(self, query: str) -> bool:
        """Determine if citations should be included based on query type"""
        research_keywords = [
            'market size', 'data', 'statistics', 'current trends', 'recent funding',
            'competitor analysis', 'pricing data', 'industry report', 'research shows',
            'latest', 'current', 'recent', 'study', 'survey', 'report'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in research_keywords)
    
    def add_citations(self, response, include_citations: bool = True) -> str:
        """Add citations with links to the response text only when appropriate"""
        if not response or not hasattr(response, 'text'):
            return str(response) if response else "No response available"
            
        text = response.text
        
        # Don't add citations if not requested or if it's a conversational response
        if not include_citations:
            return text
        
        # Check if grounding metadata exists
        if not hasattr(response, 'candidates') or not response.candidates:
            return text
        
        candidate = response.candidates[0]
        if not hasattr(candidate, 'grounding_metadata') or not candidate.grounding_metadata:
            return text
        
        supports = candidate.grounding_metadata.grounding_supports
        chunks = candidate.grounding_metadata.grounding_chunks
        
        if not supports or not chunks:
            return text

        # Sort supports by end_index in descending order to avoid shifting issues
        sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

        for support in sorted_supports:
            end_index = support.segment.end_index
            if support.grounding_chunk_indices:
                # Create citation string like [1](link1), [2](link2)
                citation_links = []
                for i in support.grounding_chunk_indices:
                    if i < len(chunks):
                        uri = chunks[i].web.uri
                        citation_links.append(f"[{i + 1}]({uri})")

                citation_string = " " + ", ".join(citation_links)
                text = text[:end_index] + citation_string + text[end_index:]

        return text
    
    def research_query(self, query: str, add_citations: bool = None) -> str:
        """Research any query and selectively add citations based on context"""
        if not self.client or not self.config:
            return f"Research capabilities unavailable for: {query}"
            
        # Auto-determine if citations should be included
        if add_citations is None:
            add_citations = self.should_include_citations(query)
            
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=query,
                config=self.config,
            )
            
            return self.add_citations(response, add_citations)
        except Exception as e:
            return f"Research query failed: {str(e)}"
    
    # Selective research methods that are context-aware
    
    def research_market_size(self, industry: str, geography: str = "global", context: str = "") -> str:
        """Get market size and growth data with selective citations"""
        context_note = f"\n\nConversation context: {context}" if context else ""
        query = f"""
        What is the current market size of the {industry} industry in {geography}? 
        Provide concise data including:
        - Market size in USD
        - Growth rate (CAGR)
        - Key trends
        {context_note}
        """
        return self.research_query(query, add_citations=True)  # Always cite market data
    
    def research_competitors(self, business_idea: str, num_competitors: int = 5, context: str = "") -> str:
        """Find and analyze competitors with selective citations"""
        context_note = f"\n\nBased on our discussion: {context}" if context else ""
        query = f"""
        Who are the top {num_competitors} competitors for: {business_idea}?
        Provide brief overview including:
        - Company names
        - Key differentiators
        - Market position
        {context_note}
        """
        return self.research_query(query, add_citations=True)  # Always cite competitor data
    
    def research_target_customers(self, business_idea: str, target_segment: str = "", context: str = "") -> str:
        """Research target customers with conversational approach"""
        segment_context = f" targeting {target_segment}" if target_segment else ""
        conversation_context = f"\n\nContext: {context}" if context else ""
        query = f"""
        Who are the ideal customers for {business_idea}{segment_context}?
        Provide concise insights on:
        - Customer demographics
        - Key pain points
        - Current solutions
        {conversation_context}
        """
        # Only cite if asking for specific customer data
        return self.research_query(query, add_citations=False)
    
    def research_market_trends(self, industry: str, context: str = "") -> str:
        """Research current trends with selective citations"""
        context_note = f"\n\nBuilding on: {context}" if context else ""
        query = f"""
        What are the current trends in the {industry} industry?
        Focus on:
        - Key technology trends
        - Market opportunities
        - Consumer behavior changes
        {context_note}
        """
        return self.research_query(query, add_citations=True)  # Always cite trend data
    
    def research_funding_landscape(self, business_type: str, stage: str = "seed", context: str = "") -> str:
        """Research funding with selective citations"""
        context_note = f"\n\nGiven our business context: {context}" if context else ""
        query = f"""
        What is the current funding landscape for {business_type} companies at {stage} stage?
        Provide concise data on:
        - Average funding amounts
        - Active investors
        - Key criteria
        {context_note}
        """
        return self.research_query(query, add_citations=True)  # Always cite funding data
    
    def research_pricing_strategies(self, business_idea: str, business_model: str = "", context: str = "") -> str:
        """Research pricing with selective citations"""
        model_context = f" using {business_model}" if business_model else ""
        conversation_context = f"\n\nConsidering: {context}" if context else ""
        query = f"""
        What are effective pricing strategies for {business_idea}{model_context}?
        Provide brief insights on:
        - Common pricing models
        - Typical price ranges
        - Market expectations
        {conversation_context}
        """
        return self.research_query(query, add_citations=True)  # Always cite pricing data
    
    def validate_problem_solution_fit(self, problem: str, solution: str, context: str = "") -> str:
        """Validate problem-solution fit with conversational approach"""
        context_note = f"\n\nBased on our research: {context}" if context else ""
        query = f"""
        Is there market validation for the problem: "{problem}" and solution: "{solution}"?
        Provide brief analysis of:
        - Problem evidence
        - Current solutions
        - Market opportunity
        {context_note}
        """
        # Only cite if specific validation data is found
        return self.research_query(query, add_citations=False)
    
    def get_research_capabilities(self) -> List[str]:
        """Return list of available research capabilities"""
        return [
            "selective_market_research",
            "competitive_intelligence", 
            "customer_insights",
            "trend_analysis",
            "funding_data",
            "pricing_intelligence",
            "smart_citations"
        ]
    
    def health_check(self) -> Dict[str, str]:
        """Check if research agent is functioning properly"""
        if self.client and self.config:
            return {"status": "healthy", "capabilities": "full_research_enabled", "citation_mode": "selective"}
        else:
            return {"status": "degraded", "capabilities": "research_disabled", "citation_mode": "none"}

# Example usage and testing for selective research integration
if __name__ == "__main__":
    research_agent = WebResearchAgent()
    
    # Test selective functionality
    print("=== HEALTH CHECK ===")
    health = research_agent.health_check()
    print(f"Agent Status: {health}")
    
    print("\n=== RESEARCH CAPABILITIES ===")
    capabilities = research_agent.get_research_capabilities()
    print(f"Available capabilities: {capabilities}")
    
    # Test selective research and citations
    print("\n=== SELECTIVE RESEARCH TEST ===")
    
    # This should include citations (specific data request)
    print("Market size query (should have citations):")
    result1 = research_agent.research_market_size("AI chatbot", "North America")
    print(result1[:200] + "...")
    
    # This should not include citations (general question)  
    print("\nCustomer research (should not have citations):")
    result2 = research_agent.research_target_customers("AI chatbots", "small businesses")
    print(result2[:200] + "...")