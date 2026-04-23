# app/orchestrator/graph.py

import hashlib
from langgraph.graph import StateGraph, END
from app.models.state import ResearchState
from app.agents.planner import run_planner
from app.agents.researcher import run_researcher
from app.agents.critic import run_critic
from app.agents.writer import run_writer
from app.guardrails.input_guard import validate_input
from app.guardrails.policy import should_retry

# ── Simple in-memory cache ────────────────────────────────
# Stores successful pipeline results by topic hash
# Prevents duplicate API calls for same topic
# Resets when app restarts

_cache = {}


# ── Input Guard Node ──────────────────────────────────────

def input_guard_node(state: ResearchState) -> ResearchState:
    topic = state["topic"]
    trace = state["trace"]

    is_valid, result = validate_input(topic)

    if not is_valid:
        trace.append(f"[InputGuard] REJECTED — {result}")
        return {**state, "error": result, "trace": trace}

    trace.append("[InputGuard] PASSED — topic accepted")
    return {**state, "topic": result, "trace": trace, "error": None}


# ── Increment Retry Node ──────────────────────────────────

def increment_retry_node(state: ResearchState) -> ResearchState:
    trace = state["trace"]
    new_count = state["retry_count"] + 1
    trace.append(
        f"[Orchestrator] Retry triggered — attempt {new_count + 1} starting"
    )
    return {**state, "retry_count": new_count, "trace": trace}


# ── Routing Functions ─────────────────────────────────────

def route_after_input_guard(state: ResearchState) -> str:
    if state.get("error"):
        return "end"
    return "planner"


def route_after_planner(state: ResearchState) -> str:
    if state.get("error"):
        return "end"
    return "researcher"


def route_after_critic(state: ResearchState) -> str:
    if state.get("error"):
        return "end"
    if should_retry(state):
        return "increment_retry"
    return "writer"


def route_after_writer(state: ResearchState) -> str:
    return "end"


# ── Build Graph ───────────────────────────────────────────

def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("input_guard",     input_guard_node)
    graph.add_node("planner",         run_planner)
    graph.add_node("researcher",      run_researcher)
    graph.add_node("critic",          run_critic)
    graph.add_node("increment_retry", increment_retry_node)
    graph.add_node("writer",          run_writer)

    graph.set_entry_point("input_guard")

    graph.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {"planner": "planner", "end": END}
    )
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"researcher": "researcher", "end": END}
    )
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
    graph.add_edge("increment_retry", "researcher")
    graph.add_conditional_edges(
        "writer",
        route_after_writer,
        {"end": END}
    )

    return graph.compile()


# ── Main Pipeline Function ────────────────────────────────

def run_pipeline(topic: str) -> ResearchState:
    """
    Main entry point.
    Checks cache first — if same topic was researched before,
    returns cached result with zero API calls.
    Otherwise runs full pipeline and caches the result.
    """

    # Generate cache key from topic
    cache_key = hashlib.md5(
        topic.lower().strip().encode()
    ).hexdigest()

    # Return cached result if available
    if cache_key in _cache:
        cached = dict(_cache[cache_key])
        cached["trace"] = (
            ["[CACHE HIT] Returning cached result — 0 API calls made"] +
            cached["trace"]
        )
        return cached

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

    # Run pipeline
    pipeline = build_graph()
    final_state = pipeline.invoke(initial_state)

    # Cache only successful results
    if not final_state.get("error"):
        _cache[cache_key] = dict(final_state)

    return final_state