#!/usr/bin/env python3
"""
Enhanced Conversational AI Co-founder System with Context & History
Combines graph-based conversation flow with real-time web research capabilities
"""

from __future__ import annotations as _annotations

import asyncio
import sys
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any
from research_agent import WebResearchAgent

try:
    import logfire
    logfire.configure(send_to_logfire='if-token-present')
    logfire.instrument_pydantic_ai()
except ImportError:
    print("Warning: logfire not available, continuing without logging")

from pydantic import BaseModel
from pydantic_graph import (
    BaseNode,
    End,
    Graph,
    GraphRunContext,
)
from pydantic_graph.persistence.file import FileStatePersistence

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()
os.environ['GEMINI_API_KEY'] = os.getenv('GOOGLE_API_KEY')

class ConversationPhase(Enum):
    INITIAL = "initial"
    MARKET_ANALYSIS = "market"
    PRODUCT_STRATEGY = "product"
    FINANCIAL_PLANNING = "finance"
    OPEN_DISCUSSION = "open"

@dataclass
class EnhancedCofounderState:
    """
    Enhanced state tracking with research capabilities and conversation history
    """
    # Core conversation data
    startup_idea: str | None = None
    current_phase: ConversationPhase = ConversationPhase.INITIAL
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    # Research insights cache for context continuity
    research_insights: Dict[str, str] = field(default_factory=dict)
    
    # Agent message histories for context continuity  
    market_messages: List[ModelMessage] = field(default_factory=list)
    product_messages: List[ModelMessage] = field(default_factory=list)
    finance_messages: List[ModelMessage] = field(default_factory=list)
    coordinator_messages: List[ModelMessage] = field(default_factory=list)
    
    # Progress tracking
    market_phase_complete: bool = False
    product_phase_complete: bool = False
    finance_phase_complete: bool = False
    
    # Key insights extracted during conversation
    key_market_insights: List[str] = field(default_factory=list)
    key_product_insights: List[str] = field(default_factory=list) 
    key_finance_insights: List[str] = field(default_factory=list)

# ================= ENHANCED AGENT DEFINITIONS =================

# Market Analyst Agent with Research Capabilities
market_analyst = Agent(
    'google-gla:gemini-2.0-flash-001',
    deps_type=WebResearchAgent,
    system_prompt="""You are a Market Analyst AI and co-founder expert. Your role is to provide insights on market trends, competition, and user needs for business ideas.

Key responsibilities:
- Analyze market opportunities and threats
- Identify target customer segments and pain points
- Research competition and market gaps
- Provide data-driven insights and recommendations

Communication style:
- Keep responses to 2-3 sentences but pack them with insights
- Ask clarifying questions when the idea needs more detail
- Use specific examples and actionable advice
- Be direct but supportive - you're helping build something great

Research tool usage:
- Only use research tools when user asks for specific data (market size, competitors, trends)
- For general questions, rely on your knowledge and keep responses conversational
- Include citations [1](link) ONLY when providing researched data
- Don't automatically research unless explicitly asked for current data

Focus areas: market sizing, competitive landscape, customer validation, market timing, go-to-market fit."""
)

# Product Strategist Agent with Research Capabilities
product_strategist = Agent(
    'google-gla:gemini-2.0-flash-001',
    deps_type=WebResearchAgent,
    system_prompt="""You are a Product Strategist AI and co-founder expert. Your role is to suggest product features, improvements, and strategies to make products stand out.

Key responsibilities:
- Design user experience and product features
- Create differentiation strategies
- Ensure product-market fit
- Plan product roadmap and development priorities

Communication style:
- Keep responses to 2-3 sentences but make them creative and actionable
- Ask questions to understand user needs better
- Suggest specific features and improvements
- Think like a user and a builder simultaneously

Research tool usage:
- Use research tools only when asked about competitor features or market validation
- For product ideas and strategy, rely on expertise and keep responses brief
- Include citations [1](link) ONLY when referencing researched competitor data
- Focus on actionable product advice over lengthy research

Focus areas: user experience, feature prioritization, product differentiation, MVP definition, user journey optimization."""
)

# Financial Planner Agent with Research Capabilities
financial_planner = Agent(
    'google-gla:gemini-2.0-flash-001',
    deps_type=WebResearchAgent,
    system_prompt="""You are a Financial Planner AI and co-founder expert. Your role is to analyze financial viability, including costs, revenue projections, and profitability.

Key responsibilities:
- Calculate startup costs and operational expenses
- Project revenue streams and growth potential
- Analyze profitability and break-even points
- Suggest funding strategies and financial optimization

Communication style:
- Keep responses to 2-3 sentences but include specific numbers when possible
- Ask for financial details when missing key information
- Provide practical financial advice and calculations
- Balance optimism with realistic financial planning

Research tool usage:
- Use research tools only when asked about funding data, pricing benchmarks, or market revenue
- For general financial advice, rely on expertise and keep responses concise
- Include citations [1](link) ONLY when providing researched funding or pricing data
- Focus on actionable financial guidance over extensive research

Focus areas: cost structure, revenue models, funding requirements, financial projections, unit economics, cash flow management."""
)

# Agent Selection Logic for Coordinator
class AgentSelection(BaseModel):
    """Structured output for coordinator's agent selection decision"""
    selected_agent: str  # "market_analyst", "product_strategist", or "financial_planner"
    reasoning: str       # Brief explanation of why this agent was chosen

# Coordinator Agent
coordinator = Agent(
    'google-gla:gemini-2.0-flash-001',
    result_type=AgentSelection,
    system_prompt="""You are a Coordinator AI managing a conversation between a user and three expert co-founder agents: Market Analyst, Product Strategist, and Financial Planner.

Your job is to analyze the user's message and select the SINGLE most appropriate agent to respond.

Selection criteria:
- Market Analyst: questions about market size, competition, customers, market research, industry trends, target audience
- Product Strategist: questions about features, user experience, product design, MVP, differentiation, user journey
- Financial Planner: questions about costs, pricing, revenue, funding, profitability, business model, financial projections

Always select exactly one agent. Consider the specific content of the user's message, not just keywords.
Provide brief reasoning for your choice."""
)

# ================= GRAPH NODES =================

@dataclass 
class InitialInput(BaseNode[EnhancedCofounderState]):
    """
    Starting node - captures the initial startup idea and begins market analysis
    """
    async def run(self, ctx: GraphRunContext[EnhancedCofounderState]) -> MarketAnalysisPhase:
        print("🚀 Welcome to your Enhanced AI Co-founder Team!")
        print("💡 Tell me about your startup idea, and I'll connect you with our expert team.")
        print("📊 We'll start with market analysis, then move to product strategy and financial planning.")
        print("🔍 Enhanced with real-time research capabilities when you need specific data!\n")
        
        # Get startup idea from user
        idea = input("What's your startup idea? ")
        ctx.state.startup_idea = idea
        ctx.state.current_phase = ConversationPhase.MARKET_ANALYSIS
        
        # Add to conversation history
        ctx.state.conversation_history.append({
            "speaker": "user", 
            "message": idea, 
            "phase": "initial"
        })
        
        print(f"\n🎯 Great! Let me connect you with our Market Analyst to explore the market opportunity...\n")
        return MarketAnalysisPhase()

@dataclass
class MarketAnalysisPhase(BaseNode[EnhancedCofounderState]):
    """
    Enhanced market analysis conversation phase with selective research capabilities
    """
    async def run(self, ctx: GraphRunContext[EnhancedCofounderState]) -> ProductStrategyPhase | MarketAnalysisPhase | CoordinatorPhase:
        print("📊 MARKET ANALYST is now leading the conversation")
        print("💬 Type 'next' when you're ready to move to product strategy\n")
        
        research_agent = WebResearchAgent()
        
        # Get market analyst's initial response - no automatic research
        if not ctx.state.market_messages:
            initial_context = f"The user wants to start this business: {ctx.state.startup_idea}. Provide initial market insights in 2-3 sentences. Be direct and supportive."
            result = await market_analyst.run(
                initial_context,
                deps=research_agent,
                message_history=ctx.state.market_messages
            )
            ctx.state.market_messages += result.all_messages()
            ctx.state.conversation_history.append({
                "speaker": "market_analyst", 
                "message": result.output, 
                "phase": "market"
            })
            
            print(f"📊 Market Analyst: {result.output}\n")
        
        # Continue conversation loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['next', 'move on', 'continue']:
                ctx.state.market_phase_complete = True
                ctx.state.current_phase = ConversationPhase.PRODUCT_STRATEGY
                print("\n🔄 Moving to Product Strategy phase...\n")
                return ProductStrategyPhase()
            
            # Regular conversation with Market Analyst
            ctx.state.conversation_history.append({
                "speaker": "user",
                "message": user_input,
                "phase": "market"
            })
            
            # Build context for the agent - keep it conversational
            conversational_context = f"User question: {user_input}"
            
            # Add recent context if available
            if len(ctx.state.conversation_history) > 1:
                recent_context = ctx.state.conversation_history[-2:]
                context_summary = " | ".join([f"{msg['speaker']}: {msg['message']}" for msg in recent_context])
                conversational_context += f"\n\nRecent context: {context_summary}"
            
            result = await market_analyst.run(
                conversational_context,
                deps=research_agent,
                message_history=ctx.state.market_messages
            )
            ctx.state.market_messages += result.all_messages()
            ctx.state.conversation_history.append({
                "speaker": "market_analyst", 
                "message": result.output,
                "phase": "market"
            })
            
            print(f"📊 Market Analyst: {result.output}\n")

@dataclass
class ProductStrategyPhase(BaseNode[EnhancedCofounderState]):
    """
    Enhanced product strategy conversation phase with selective research capabilities
    """
    async def run(self, ctx: GraphRunContext[EnhancedCofounderState]) -> FinancialPlanningPhase | ProductStrategyPhase:
        print("🛠️ PRODUCT STRATEGIST is now leading the conversation")
        print("💬 Type 'next' when you're ready to move to financial planning\n")
        
        research_agent = WebResearchAgent()
        
        # Get product strategist's initial response based on previous context
        if not ctx.state.product_messages:
            # Build context from market phase - keep it concise
            market_context = ""
            if ctx.state.conversation_history:
                market_msgs = [msg for msg in ctx.state.conversation_history if msg["phase"] == "market"][-3:]
                if market_msgs:
                    market_context = f"Market context: {market_msgs[-1]['message']}"
            
            context_summary = f"Startup idea: {ctx.state.startup_idea}. {market_context} Now let's focus on product strategy in 2-3 sentences."
            
            result = await product_strategist.run(
                context_summary,
                deps=research_agent,
                message_history=ctx.state.product_messages
            )
            ctx.state.product_messages += result.all_messages()
            ctx.state.conversation_history.append({
                "speaker": "product_strategist",
                "message": result.output,
                "phase": "product"
            })
            
            print(f"🛠️ Product Strategist: {result.output}\n")
        
        # Continue conversation loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['next', 'move on', 'continue']:
                ctx.state.product_phase_complete = True
                ctx.state.current_phase = ConversationPhase.FINANCIAL_PLANNING
                print("\n🔄 Moving to Financial Planning phase...\n")
                return FinancialPlanningPhase()
            
            ctx.state.conversation_history.append({
                "speaker": "user",
                "message": user_input,
                "phase": "product"
            })
            
            # Build conversational context
            conversational_context = f"User question: {user_input}"
            
            # Add recent context
            if len(ctx.state.conversation_history) > 1:
                recent_context = ctx.state.conversation_history[-2:]
                context_summary = " | ".join([f"{msg['speaker']}: {msg['message']}" for msg in recent_context])
                conversational_context += f"\n\nRecent context: {context_summary}"
            
            result = await product_strategist.run(
                conversational_context,
                deps=research_agent,
                message_history=ctx.state.product_messages
            )
            ctx.state.product_messages += result.all_messages()
            ctx.state.conversation_history.append({
                "speaker": "product_strategist",
                "message": result.output,
                "phase": "product"
            })
            
            print(f"🛠️ Product Strategist: {result.output}\n")

@dataclass
class FinancialPlanningPhase(BaseNode[EnhancedCofounderState]):
    """
    Enhanced financial planning conversation phase with selective research capabilities
    """
    async def run(self, ctx: GraphRunContext[EnhancedCofounderState]) -> CoordinatorPhase:
        print("💰 FINANCIAL PLANNER is now leading the conversation")
        print("💬 Type 'next' when you're ready to open discussion to all experts\n")
        
        research_agent = WebResearchAgent()
        
        # Get financial planner's initial response based on previous context
        if not ctx.state.finance_messages:
            # Build comprehensive context from all previous phases - keep it concise
            recent_context = ""
            if ctx.state.conversation_history:
                recent_msgs = ctx.state.conversation_history[-5:]
                recent_context = f"Previous discussion: {recent_msgs[-1]['message']}"
            
            context_summary = f"Startup idea: {ctx.state.startup_idea}. {recent_context} Now let's analyze the financial aspects in 2-3 sentences."
            
            result = await financial_planner.run(
                context_summary,
                deps=research_agent,
                message_history=ctx.state.finance_messages
            )
            ctx.state.finance_messages += result.all_messages()
            ctx.state.conversation_history.append({
                "speaker": "financial_planner",
                "message": result.output,
                "phase": "finance"
            })
            
            print(f"💰 Financial Planner: {result.output}\n")
        
        # Continue conversation loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['next', 'move on', 'continue']:
                ctx.state.finance_phase_complete = True
                ctx.state.current_phase = ConversationPhase.OPEN_DISCUSSION
                print("\n🔄 Opening discussion to all experts! The coordinator will now select the best expert for each question...\n")
                return CoordinatorPhase()
            
            ctx.state.conversation_history.append({
                "speaker": "user",
                "message": user_input,
                "phase": "finance"
            })
            
            # Build conversational context
            conversational_context = f"User question: {user_input}"
            
            # Add recent context
            if len(ctx.state.conversation_history) > 1:
                recent_context = ctx.state.conversation_history[-2:]
                context_summary = " | ".join([f"{msg['speaker']}: {msg['message']}" for msg in recent_context])
                conversational_context += f"\n\nRecent context: {context_summary}"
            
            result = await financial_planner.run(
                conversational_context,
                deps=research_agent,
                message_history=ctx.state.finance_messages
            )
            ctx.state.finance_messages += result.all_messages()
            ctx.state.conversation_history.append({
                "speaker": "financial_planner",
                "message": result.output,
                "phase": "finance"
            })
            
            print(f"💰 Financial Planner: {result.output}\n")

@dataclass 
class CoordinatorPhase(BaseNode[EnhancedCofounderState, None, str]):
    """
    Enhanced open discussion phase with coordinator and selective research capabilities
    """
    async def run(self, ctx: GraphRunContext[EnhancedCofounderState]) -> End[str] | CoordinatorPhase:
        print("🤝 COORDINATOR is now managing the conversation")
        print("💬 All experts are available! Ask anything and I'll connect you with the right specialist.")
        print("💬 Type 'exit' to end the session\n")
        
        research_agent = WebResearchAgent()
        
        # Main conversation loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'end', 'done']:
                summary = self._generate_session_summary(ctx.state)
                return End(summary)
            
            # Coordinator selects appropriate agent
            recent_context = ""
            if ctx.state.conversation_history:
                recent_msgs = ctx.state.conversation_history[-3:]
                recent_context = " ".join([f"{msg['speaker']}: {msg['message']}" for msg in recent_msgs])
            
            coordinator_context = f"Recent conversation: {recent_context}. User's new message: {user_input}"
            
            selection_result = await coordinator.run(
                coordinator_context,
                message_history=ctx.state.coordinator_messages
            )
            ctx.state.coordinator_messages += selection_result.all_messages()
            
            # Route to selected agent
            selected_agent = selection_result.data.selected_agent
            print(f"🎯 Coordinator: Connecting you with {selected_agent.replace('_', ' ').title()} - {selection_result.data.reasoning}\n")
            
            ctx.state.conversation_history.append({
                "speaker": "user",
                "message": user_input,
                "phase": "open"
            })
            
            # Build conversational context for selected agent
            conversational_context = f"User question: {user_input}"
            if recent_context:
                conversational_context += f"\n\nRecent context: {recent_context}"
            
            # Execute selected agent's response with research capabilities but conversational style
            if selected_agent == "market_analyst":
                result = await market_analyst.run(conversational_context, deps=research_agent, message_history=ctx.state.market_messages)
                ctx.state.market_messages += result.all_messages()
                print(f"📊 Market Analyst: {result.output}\n")
                speaker = "market_analyst"
                
            elif selected_agent == "product_strategist":
                result = await product_strategist.run(conversational_context, deps=research_agent, message_history=ctx.state.product_messages)
                ctx.state.product_messages += result.all_messages()
                print(f"🛠️ Product Strategist: {result.output}\n")
                speaker = "product_strategist"
                
            elif selected_agent == "financial_planner":
                result = await financial_planner.run(conversational_context, deps=research_agent, message_history=ctx.state.finance_messages)
                ctx.state.finance_messages += result.all_messages()
                print(f"💰 Financial Planner: {result.output}\n")
                speaker = "financial_planner"
                
            else:
                print("❌ Error: Unknown agent selected")
                continue
            
            ctx.state.conversation_history.append({
                "speaker": speaker,
                "message": result.output,
                "phase": "open"
            })

    def _generate_session_summary(self, state: EnhancedCofounderState) -> str:
        """Generate a summary of the entire co-founder session"""
        summary = f"""
🎉 Enhanced Co-founder Session Complete!

💡 Startup Idea: {state.startup_idea}

📊 Phases Completed:
- Market Analysis: {'✅' if state.market_phase_complete else '⏳'}
- Product Strategy: {'✅' if state.product_phase_complete else '⏳'}  
- Financial Planning: {'✅' if state.finance_phase_complete else '⏳'}

💬 Total Conversation Messages: {len(state.conversation_history)}

🔍 Your AI co-founder team provided research-backed insights with real-time data when needed!
        """
        return summary.strip()

# ================= GRAPH DEFINITION =================

enhanced_cofounder_graph = Graph(
    nodes=(
        InitialInput,
        MarketAnalysisPhase, 
        ProductStrategyPhase,
        FinancialPlanningPhase,
        CoordinatorPhase
    ),
    state_type=EnhancedCofounderState
)

# ================= EXECUTION MODES =================

async def run_continuous():
    """
    Run the complete co-founder conversation from start to finish
    """
    print("🚀 Starting Enhanced AI Co-founder Continuous Session...\n")
    
    state = EnhancedCofounderState()
    node = InitialInput()
    end = await enhanced_cofounder_graph.run(node, state=state)
    print('\n' + '='*50)
    print('SESSION SUMMARY:')
    print(end.output)

async def run_cli(startup_idea: str | None):
    """
    Run with persistence - can resume sessions and handle specific inputs
    """
    persistence = FileStatePersistence(Path('enhanced_cofounder_session.json'))
    persistence.set_graph_types(enhanced_cofounder_graph)
    
    # Check for existing session
    if snapshot := await persistence.load_next():
        state = snapshot.state
        print(f"📁 Resuming session for: {state.startup_idea}")
        
        # Determine current phase and create appropriate node
        if state.current_phase == ConversationPhase.MARKET_ANALYSIS:
            node = MarketAnalysisPhase()
        elif state.current_phase == ConversationPhase.PRODUCT_STRATEGY:
            node = ProductStrategyPhase()
        elif state.current_phase == ConversationPhase.FINANCIAL_PLANNING:
            node = FinancialPlanningPhase()
        elif state.current_phase == ConversationPhase.OPEN_DISCUSSION:
            node = CoordinatorPhase()
        else:
            node = InitialInput()
    else:
        # New session
        state = EnhancedCofounderState()
        if startup_idea:
            state.startup_idea = startup_idea
            state.current_phase = ConversationPhase.MARKET_ANALYSIS
            node = MarketAnalysisPhase()
        else:
            node = InitialInput()
    
    # Run the graph with persistence
    async with enhanced_cofounder_graph.iter(node, state=state, persistence=persistence) as run:
        while True:
            node = await run.next()
            if isinstance(node, End):
                print('\n' + '='*50)
                print('SESSION SUMMARY:')
                print(node.data)
                
                # Show session history
                history = await persistence.load_all()
                print(f'\n📊 Session History: {len(history)} steps completed')
                print('✅ Enhanced co-founder session finished!')
                break

# Legacy support for simple session
async def main():
    if len(sys.argv) < 2:
        print("Usage: python app.py 'your startup idea'")
        print("Example: python app.py 'smart glasses for blind people'")
        sys.exit(1)
    
    startup_idea = sys.argv[1]
    await run_cli(startup_idea)

# ================= MAIN EXECUTION =================

if __name__ == '__main__':
    try:
        sub_command = sys.argv[1]
        assert sub_command in ('continuous', 'cli', 'mermaid')
    except (IndexError, AssertionError):
        print(
            'Usage:\n'
            '  python app.py mermaid                           # Show graph structure\n'
            '  python app.py continuous                        # Run full session\n'
            '  python app.py cli ["startup idea"]              # Run with persistence\n',
            file=sys.stderr,
        )
        sys.exit(1)
    
    if sub_command == 'mermaid':
        print("🔄 Enhanced AI Co-founder Workflow Graph:")
        print(enhanced_cofounder_graph.mermaid_code(start_node=InitialInput))
    elif sub_command == 'continuous':
        asyncio.run(run_continuous())
    else:  # cli
        startup_idea = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(run_cli(startup_idea))