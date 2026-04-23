# app/orchestrator/graph.py

from langgraph.graph import StateGraph, END
from app.models.state import ResearchState
from app.agents.planner import run_planner
from app.agents.researcher import run_researcher
from app.agents.critic import run_critic
from app.agents.writer import run_writer
from app.guardrails.input_guard import validate_input
from app.guardrails.policy import should_retry


# ── Input Guard Node ──────────────────────────────────────

def input_guard_node(state: ResearchState) -> ResearchState:
    """
    Validates and sanitizes user input.
    Runs before any agent.
    """
    topic = state["topic"]
    trace = state["trace"]

    is_valid, result = validate_input(topic)

    if not is_valid:
        trace.append(f"[InputGuard] REJECTED — {result}")
        return {
            **state,
            "error": result,
            "trace": trace
        }

    trace.append(f"[InputGuard] PASSED — topic accepted")
    return {
        **state,
        "topic": result,
        "trace": trace,
        "error": None
    }


# ── Increment Retry Node ──────────────────────────────────

def increment_retry_node(state: ResearchState) -> ResearchState:
    """
    Increments retry_count before sending back to Researcher.
    This is a separate node so the count is always updated
    before the retry happens.
    """
    trace = state["trace"]
    new_count = state["retry_count"] + 1
    trace.append(
        f"[Orchestrator] Retry triggered — "
        f"attempt {new_count + 1} starting"
    )
    return {
        **state,
        "retry_count": new_count,
        "trace": trace
    }


# ── Routing Functions ─────────────────────────────────────

def route_after_input_guard(state: ResearchState) -> str:
    """
    After InputGuard — continue or stop?
    """
    if state.get("error"):
        return "end"
    return "planner"


def route_after_planner(state: ResearchState) -> str:
    """
    After Planner — continue or stop?
    """
    if state.get("error"):
        return "end"
    return "researcher"


def route_after_critic(state: ResearchState) -> str:
    """
    After Critic — retry, continue to writer, or stop?
    This is the most important routing decision.
    """
    if state.get("error"):
        return "end"

    if should_retry(state):
        return "increment_retry"

    return "writer"


def route_after_writer(state: ResearchState) -> str:
    """
    After Writer — done.
    """
    if state.get("error"):
        return "end"
    return "end"


# ── Build the Graph ───────────────────────────────────────

def build_graph():
    """
    Builds and compiles the complete LangGraph pipeline.
    Returns a compiled graph ready to run.
    """

    # Create the graph with our state type
    graph = StateGraph(ResearchState)

    # ── Add all nodes ─────────────────────────────────────
    graph.add_node("input_guard",     input_guard_node)
    graph.add_node("planner",         run_planner)
    graph.add_node("researcher",      run_researcher)
    graph.add_node("critic",          run_critic)
    graph.add_node("increment_retry", increment_retry_node)
    graph.add_node("writer",          run_writer)

    # ── Set entry point ───────────────────────────────────
    graph.set_entry_point("input_guard")

    # ── Add conditional edges ─────────────────────────────
    graph.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {
            "planner": "planner",
            "end": END
        }
    )

    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "researcher": "researcher",
            "end": END
        }
    )

    # Researcher always goes to Critic
    graph.add_edge("researcher", "critic")

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "increment_retry": "increment_retry",
            "writer": "writer",
            "end": END
        }
    )

    # increment_retry always goes back to Researcher
    graph.add_edge("increment_retry", "researcher")

    graph.add_conditional_edges(
        "writer",
        route_after_writer,
        {
            "end": END
        }
    )

    # ── Compile and return ────────────────────────────────
    return graph.compile()


# ── Main Pipeline Function ────────────────────────────────

def run_pipeline(topic: str) -> ResearchState:
    """
    Main entry point for the pipeline.
    Takes a topic string.
    Returns the final state with report.
    """

    # Build initial state
    initial_state = ResearchState(
        topic=topic,
        subquestions=[],
        findings=[],
        critic_feedback=[],
        confidence_score=0.0,
        retry_count=0,
        final_report="",
        trace=[],
        error=None
    )

    # Build and run graph
    pipeline = build_graph()
    final_state = pipeline.invoke(initial_state)

    return final_state