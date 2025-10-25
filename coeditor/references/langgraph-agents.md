# LangGraph Agent Patterns for Collaborative Editing

Comprehensive guide to building LangGraph agents for editor applications with shared state management.

## Core Concepts

### What is LangGraph?

LangGraph is a framework for building stateful, multi-actor applications with LLMs. It extends LangChain with:
- **State Management**: Persistent state across agent interactions
- **Graph-based Workflows**: Define complex agent workflows as graphs
- **Conditional Logic**: Route between agents based on state
- **Human-in-the-loop**: Pause for user input when needed
- **Persistence**: Save and resume workflows

### Why LangGraph for Editors?

Perfect for collaborative editing because:
- **Shared State**: Editor state accessible to all agents
- **Multi-Agent**: Multiple specialized agents (writer, reviewer, researcher)
- **Streaming**: Real-time updates to UI
- **Context Awareness**: Agents see full document context
- **Workflow Control**: Complex editing workflows (draft → review → revise)

## State Schema Design

### Base Editor State

```python
from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
import operator

class EditorState(TypedDict):
    """Shared state for editor and agents."""

    # Document content
    content: str
    content_type: str  # "text", "markdown", "code", "json"

    # Selection information
    selection: dict  # {"start": int, "end": int, "text": str}

    # Chat messages
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Agent routing
    current_agent: str
    next_agent: Optional[str]

    # Task tracking
    task: str
    task_status: str  # "pending", "in_progress", "completed", "failed"

    # Version control
    version: int
    history: list[dict]

    # Metadata
    metadata: dict
```

### Document-Specific State

For rich document editors:

```python
class DocumentState(EditorState):
    """State for structured document editors."""

    # Document structure
    sections: list[dict]  # [{"id": str, "title": str, "content": str}]
    outline: list[dict]

    # Formatting
    styles: dict
    templates: list[str]

    # Collaboration
    comments: list[dict]
    suggestions: list[dict]
```

### Code Editor State

For code editors:

```python
class CodeEditorState(EditorState):
    """State for code editors."""

    # Code-specific
    language: str
    file_path: str
    imports: list[str]

    # Analysis
    syntax_errors: list[dict]
    lint_warnings: list[dict]
    type_errors: list[dict]

    # Context
    symbols: list[dict]  # Functions, classes, variables
    dependencies: list[str]
```

### Node Editor State

For workflow/graph editors:

```python
class NodeEditorState(EditorState):
    """State for node-based editors."""

    # Graph structure
    nodes: list[dict]  # [{"id": str, "type": str, "data": dict}]
    edges: list[dict]  # [{"source": str, "target": str}]

    # Selection
    selected_nodes: list[str]
    selected_edges: list[str]

    # Layout
    layout: dict
    viewport: dict
```

## Building Agents

### Base Agent Class

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class BaseEditorAgent:
    """Base class for editor agents."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ):
        self.name = name
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.system_prompt = system_prompt

    def create_prompt(self) -> ChatPromptTemplate:
        """Create prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
        ])

    async def process(self, state: EditorState) -> EditorState:
        """Process state and return updated state."""
        raise NotImplementedError("Subclasses must implement process()")

    def get_context(self, state: EditorState) -> dict:
        """Extract relevant context from state."""
        return {
            "content": state.get("content", ""),
            "selection": state.get("selection", {}),
            "metadata": state.get("metadata", {}),
        }
```

### Writing Assistant Agent

```python
from langchain_core.messages import AIMessage, HumanMessage

class WritingAssistant(BaseEditorAgent):
    """Agent that helps with writing and editing."""

    def __init__(self):
        super().__init__(
            name="writing_assistant",
            system_prompt="""You are an expert writing assistant.

Your responsibilities:
- Improve clarity and readability
- Fix grammar and spelling
- Enhance style and tone
- Expand on ideas when requested
- Summarize long content

Current document context:
Content: {content}
Selection: {selection}
Word count: {word_count}

Always maintain the author's voice and intent.
Provide specific, actionable suggestions.
""",
            temperature=0.7,
        )

    async def process(self, state: EditorState) -> EditorState:
        """Process writing task."""
        context = self.get_context(state)
        messages = state["messages"]

        # Get the last user message
        last_message = messages[-1]

        # Create prompt with context
        prompt = self.create_prompt()
        chain = prompt | self.llm | StrOutputParser()

        # Generate response
        response = await chain.ainvoke({
            "input": last_message.content,
            "content": context["content"],
            "selection": context["selection"],
            "word_count": len(context["content"].split()),
        })

        # Update state
        state["messages"] = state["messages"] + [AIMessage(content=response)]
        state["task_status"] = "completed"
        state["current_agent"] = self.name

        return state

    async def improve_text(self, text: str) -> str:
        """Improve a piece of text."""
        prompt = f"""Improve this text while maintaining its meaning:

{text}

Provide only the improved version, no explanation."""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        return await chain.ainvoke({"input": prompt})

    async def expand_idea(self, idea: str, target_words: int = 200) -> str:
        """Expand a brief idea into fuller text."""
        prompt = f"""Expand this idea into approximately {target_words} words:

{idea}

Provide detailed, well-structured content."""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        return await chain.ainvoke({"input": prompt})
```

### Code Assistant Agent

```python
class CodeAssistant(BaseEditorAgent):
    """Agent that helps with coding."""

    def __init__(self):
        super().__init__(
            name="code_assistant",
            system_prompt="""You are an expert programming assistant.

Your responsibilities:
- Provide code completions
- Explain code functionality
- Find and fix bugs
- Suggest refactorings
- Write documentation
- Review code quality

Current code context:
Language: {language}
Code: {content}
Selection: {selection}
Errors: {errors}

Provide accurate, idiomatic code in the specified language.
""",
            temperature=0.3,  # Lower temperature for code
        )

    async def process(self, state: EditorState) -> EditorState:
        """Process code-related task."""
        context = self.get_context(state)
        messages = state["messages"]
        metadata = state.get("metadata", {})

        last_message = messages[-1]

        # Create specialized prompt for code
        response = await self.generate_code_response(
            last_message.content,
            context["content"],
            metadata.get("language", "python"),
            context["selection"],
        )

        state["messages"] = state["messages"] + [AIMessage(content=response)]
        state["task_status"] = "completed"

        return state

    async def generate_code_response(
        self,
        query: str,
        code: str,
        language: str,
        selection: dict,
    ) -> str:
        """Generate code-specific response."""
        prompt = self.create_prompt()
        chain = prompt | self.llm | StrOutputParser()

        return await chain.ainvoke({
            "input": query,
            "content": code,
            "language": language,
            "selection": selection,
            "errors": [],  # Could integrate linter/type checker
        })

    async def complete_code(self, code: str, cursor_position: int) -> str:
        """Generate code completion."""
        before = code[:cursor_position]
        after = code[cursor_position:]

        prompt = f"""Complete this code:

```
{before}<CURSOR>{after}
```

Provide only the completion at <CURSOR>, no explanation."""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        return await chain.ainvoke({"input": prompt})

    async def explain_code(self, code: str) -> str:
        """Explain what code does."""
        prompt = f"""Explain what this code does in simple terms:

```
{code}
```

Provide a clear, concise explanation."""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        return await chain.ainvoke({"input": prompt})

    async def find_bugs(self, code: str) -> list[dict]:
        """Find potential bugs in code."""
        prompt = f"""Analyze this code for potential bugs:

```
{code}
```

Return a JSON array of bugs found:
[{{"line": int, "severity": "error|warning", "message": str}}]"""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        result = await chain.ainvoke({"input": prompt})

        # Parse JSON response
        import json
        try:
            return json.loads(result)
        except:
            return []
```

### Research Agent

```python
class ResearchAgent(BaseEditorAgent):
    """Agent that researches topics and gathers information."""

    def __init__(self):
        super().__init__(
            name="research_agent",
            system_prompt="""You are a research assistant.

Your responsibilities:
- Research topics thoroughly
- Find relevant information
- Cite sources
- Summarize findings
- Fact-check content

Current context:
Document topic: {topic}
Content so far: {content}
Research query: {query}

Provide well-researched, accurate information with sources.
""",
        )

    async def process(self, state: EditorState) -> EditorState:
        """Process research request."""
        messages = state["messages"]
        last_message = messages[-1]

        # Extract query
        query = last_message.content

        # Perform research (integrate with search tools, web browsing, etc.)
        findings = await self.research(query)

        # Create response
        response = self.format_findings(findings)

        state["messages"] = state["messages"] + [AIMessage(content=response)]
        state["task_status"] = "completed"

        return state

    async def research(self, query: str) -> dict:
        """Perform research on a topic."""
        # This would integrate with:
        # - Web search (Tavily, Brave, etc.)
        # - Document retrieval
        # - Knowledge bases
        # For now, using LLM's knowledge

        prompt = f"""Research this topic: {query}

Provide:
1. Key information
2. Important facts
3. Relevant context
4. Credible sources (if available)

Format as structured information."""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        result = await chain.ainvoke({"input": prompt})

        return {"query": query, "findings": result}

    def format_findings(self, findings: dict) -> str:
        """Format research findings."""
        return f"""# Research Findings

Query: {findings['query']}

{findings['findings']}
"""
```

### Reviewer Agent

```python
class ReviewerAgent(BaseEditorAgent):
    """Agent that reviews content."""

    def __init__(self):
        super().__init__(
            name="reviewer",
            system_prompt="""You are an expert content reviewer.

Your responsibilities:
- Review content quality
- Check for errors and inconsistencies
- Suggest improvements
- Verify facts
- Assess readability

Content to review: {content}
Review criteria: {criteria}

Provide constructive, specific feedback.
""",
        )

    async def process(self, state: EditorState) -> EditorState:
        """Process review request."""
        content = state.get("content", "")

        # Perform review
        review = await self.review_content(content)

        # Create response
        response = self.format_review(review)

        state["messages"] = state["messages"] + [
            AIMessage(content=response)
        ]
        state["task_status"] = "completed"

        # Determine if revision needed
        if review["issues"]:
            state["next_agent"] = "writing_assistant"
        else:
            state["next_agent"] = None

        return state

    async def review_content(self, content: str) -> dict:
        """Review content and identify issues."""
        prompt = f"""Review this content:

{content}

Provide:
1. Overall assessment (1-10)
2. Strengths
3. Issues found
4. Specific suggestions
5. Decision: approve or needs revision

Format as structured review."""

        chain = self.create_prompt() | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "input": prompt,
            "content": content,
            "criteria": "clarity, accuracy, completeness",
        })

        # Parse review (simplified)
        return {
            "score": 8,
            "strengths": [],
            "issues": [],
            "suggestions": [],
            "decision": "approve",
            "details": result,
        }

    def format_review(self, review: dict) -> str:
        """Format review results."""
        return f"""# Content Review

**Score**: {review['score']}/10

{review['details']}
"""
```

## Building LangGraph Workflows

### Simple Single-Agent Graph

```python
from langgraph.graph import StateGraph, END

def create_simple_graph():
    """Create a simple single-agent graph."""

    # Initialize agent
    writing_agent = WritingAssistant()

    # Create graph
    workflow = StateGraph(EditorState)

    # Add node
    workflow.add_node("writing_assistant", writing_agent.process)

    # Set entry point
    workflow.set_entry_point("writing_assistant")

    # Add edge to end
    workflow.add_edge("writing_assistant", END)

    # Compile
    return workflow.compile()
```

### Multi-Agent Sequential Graph

```python
def create_sequential_graph():
    """Create graph with sequential agent execution."""

    # Initialize agents
    research_agent = ResearchAgent()
    writing_agent = WritingAssistant()
    reviewer_agent = ReviewerAgent()

    # Create graph
    workflow = StateGraph(EditorState)

    # Add nodes
    workflow.add_node("research", research_agent.process)
    workflow.add_node("write", writing_agent.process)
    workflow.add_node("review", reviewer_agent.process)

    # Create linear workflow: research → write → review
    workflow.set_entry_point("research")
    workflow.add_edge("research", "write")
    workflow.add_edge("write", "review")
    workflow.add_edge("review", END)

    return workflow.compile()
```

### Conditional Routing Graph

```python
def create_conditional_graph():
    """Create graph with conditional routing."""

    # Initialize agents
    writing_agent = WritingAssistant()
    code_agent = CodeAssistant()
    reviewer_agent = ReviewerAgent()

    # Create graph
    workflow = StateGraph(EditorState)

    # Add nodes
    workflow.add_node("writing_assistant", writing_agent.process)
    workflow.add_node("code_assistant", code_agent.process)
    workflow.add_node("reviewer", reviewer_agent.process)

    # Conditional entry point based on content type
    def route_initial(state: EditorState) -> str:
        """Route to appropriate agent based on task."""
        content_type = state.get("content_type", "text")

        if content_type == "code":
            return "code_assistant"
        else:
            return "writing_assistant"

    workflow.set_conditional_entry_point(
        route_initial,
        {
            "writing_assistant": "writing_assistant",
            "code_assistant": "code_assistant",
        }
    )

    # Both agents go to reviewer
    workflow.add_edge("writing_assistant", "reviewer")
    workflow.add_edge("code_assistant", "reviewer")

    # Conditional exit from reviewer
    def route_review(state: EditorState) -> str:
        """Route based on review result."""
        next_agent = state.get("next_agent")

        if next_agent:
            return next_agent
        else:
            return "end"

    workflow.add_conditional_edges(
        "reviewer",
        route_review,
        {
            "writing_assistant": "writing_assistant",
            "code_assistant": "code_assistant",
            "end": END,
        }
    )

    return workflow.compile()
```

### Human-in-the-Loop Graph

```python
from langgraph.checkpoint import MemorySaver

def create_human_in_loop_graph():
    """Create graph that pauses for human input."""

    writing_agent = WritingAssistant()
    reviewer_agent = ReviewerAgent()

    workflow = StateGraph(EditorState)

    workflow.add_node("write", writing_agent.process)
    workflow.add_node("review", reviewer_agent.process)
    workflow.add_node("human_review", lambda x: x)  # Pause point

    workflow.set_entry_point("write")
    workflow.add_edge("write", "review")
    workflow.add_edge("review", "human_review")

    # After human review, conditionally continue
    def after_human_review(state: EditorState) -> str:
        user_decision = state.get("metadata", {}).get("decision")

        if user_decision == "revise":
            return "write"
        else:
            return "end"

    workflow.add_conditional_edges(
        "human_review",
        after_human_review,
        {
            "write": "write",
            "end": END,
        }
    )

    # Compile with checkpointer for persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Usage
graph = create_human_in_loop_graph()

# Start workflow
state = {
    "content": "Draft content",
    "messages": [],
    "task": "write_article",
}

# Run until human review
config = {"configurable": {"thread_id": "1"}}
result = await graph.ainvoke(state, config)

# Human provides feedback
result["metadata"]["decision"] = "revise"
result["messages"].append(HumanMessage(content="Please expand section 2"))

# Continue from checkpoint
final = await graph.ainvoke(result, config)
```

## Advanced Patterns

### Parallel Agent Execution

```python
def create_parallel_graph():
    """Multiple agents work in parallel."""

    workflow = StateGraph(EditorState)

    # Add parallel agents
    workflow.add_node("fact_checker", fact_checker_agent.process)
    workflow.add_node("style_checker", style_checker_agent.process)
    workflow.add_node("grammar_checker", grammar_checker_agent.process)

    # Aggregator combines results
    async def aggregate_results(state: EditorState) -> EditorState:
        """Combine results from parallel agents."""
        # Merge findings from all agents
        return state

    workflow.add_node("aggregate", aggregate_results)

    # Start all in parallel
    workflow.set_entry_point("fact_checker")
    workflow.set_entry_point("style_checker")
    workflow.set_entry_point("grammar_checker")

    # All flow to aggregator
    workflow.add_edge("fact_checker", "aggregate")
    workflow.add_edge("style_checker", "aggregate")
    workflow.add_edge("grammar_checker", "aggregate")
    workflow.add_edge("aggregate", END)

    return workflow.compile()
```

### Streaming Updates

```python
async def stream_agent_updates(graph, state):
    """Stream agent updates to frontend."""

    async for event in graph.astream(state):
        # Each event contains state update
        node_name = list(event.keys())[0]
        node_output = event[node_name]

        # Send to frontend via WebSocket
        yield {
            "agent": node_name,
            "state": node_output,
            "status": "in_progress",
        }

    yield {
        "status": "completed",
        "final_state": node_output,
    }
```

### Agent Memory

```python
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import get_buffer_string

class AgentWithMemory(BaseEditorAgent):
    """Agent with conversation memory."""

    def __init__(self, name: str, system_prompt: str):
        super().__init__(name, system_prompt)
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
        )

    async def process(self, state: EditorState) -> EditorState:
        """Process with memory."""

        # Get conversation history
        history = self.memory.load_memory_variables({})
        chat_history = history.get("chat_history", [])

        # Create prompt with history
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            *chat_history,
            ("human", "{input}"),
        ])

        chain = prompt | self.llm | StrOutputParser()

        # Generate response
        last_message = state["messages"][-1]
        response = await chain.ainvoke({"input": last_message.content})

        # Save to memory
        self.memory.save_context(
            {"input": last_message.content},
            {"output": response},
        )

        # Update state
        state["messages"] = state["messages"] + [AIMessage(content=response)]

        return state
```

## Testing Agents

```python
import pytest
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_writing_assistant():
    """Test writing assistant agent."""

    agent = WritingAssistant()

    state = {
        "content": "This is test content.",
        "selection": {"start": 0, "end": 0, "text": ""},
        "messages": [HumanMessage(content="Improve this text")],
        "task": "improve",
        "task_status": "pending",
        "metadata": {},
    }

    result = await agent.process(state)

    assert result["task_status"] == "completed"
    assert len(result["messages"]) > 1
    assert result["current_agent"] == "writing_assistant"

@pytest.mark.asyncio
async def test_graph_execution():
    """Test full graph execution."""

    graph = create_simple_graph()

    state = {
        "content": "Test content",
        "messages": [HumanMessage(content="Help me write")],
        "task": "write",
        "task_status": "pending",
    }

    result = await graph.ainvoke(state)

    assert result["task_status"] == "completed"
```

## Best Practices

1. **Clear State Schema**: Define comprehensive, typed state
2. **Modular Agents**: Each agent has single responsibility
3. **Error Handling**: Gracefully handle LLM failures
4. **Streaming**: Use streaming for better UX
5. **Observability**: Log agent decisions and state changes
6. **Testing**: Test agents and workflows independently
7. **Versioning**: Track state versions for undo/redo
8. **Performance**: Cache agent responses when appropriate
9. **Security**: Validate all state updates
10. **Documentation**: Document agent capabilities and workflows
