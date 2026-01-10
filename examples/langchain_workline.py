"""
LangChain + Workline SDK example.

Prereqs:
  - Start Workline API: wl serve --addr 127.0.0.1:8080 --base-path /v0
  - Install deps: pip install langchain langchain-openai
  - Set OpenAI key: export OPENAI_API_KEY=...

Optional env vars:
  - WORKLINE_BASE_URL (default: http://127.0.0.1:8080)
  - WORKLINE_PROJECT_ID (default: myproj)
  - WORKLINE_API_KEY (API key for automation)
  - WORKLINE_ACCESS_TOKEN (JWT bearer token)
  - WORKLINE_HUMAN_REVIEW_MODE (interactive only)

This script:
  1) Runs discovery with a product planner that can ask humans questions.
  2) Ensures a "problem refinement" task exists and stores discovery output in it.
  3) Produces an agile iteration plan (sprint goal, backlog, dependencies).
  4) Runs a human-in-the-loop review step (interactive).
  5) Creates a Workline iteration, then tasks per sprint backlog item.
  6) Runs demo/review gates, closes the iteration, then fetches events.
  7) Logs all agent actions into a Workline "agent log" task.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

try:
    from langchain.agents import create_agent as lc_create_agent

    _LC_AGENT_MODE = "graph"
except ImportError:
    lc_create_agent = None
    _LC_AGENT_MODE = "executor"

if _LC_AGENT_MODE == "executor":
    try:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
    except ImportError:
        from langchain.agents import create_tool_calling_agent
        from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

_ROOT = Path(__file__).resolve().parents[1]
_SDK_PATH = _ROOT / "sdk" / "python"
if str(_SDK_PATH) not in sys.path:
    sys.path.insert(0, str(_SDK_PATH))

from workline import APIError, WorklineClient

BASE_URL = os.getenv("WORKLINE_BASE_URL", "http://127.0.0.1:8080")
PROJECT_ID = os.getenv("WORKLINE_PROJECT_ID", "example")
API_KEY = os.getenv("WORKLINE_API_KEY")
ACCESS_TOKEN = os.getenv("WORKLINE_ACCESS_TOKEN")
HUMAN_REVIEW_MODE = os.getenv("WORKLINE_HUMAN_REVIEW_MODE", "interactive")

client = WorklineClient(BASE_URL, PROJECT_ID, api_key=API_KEY, access_token=ACCESS_TOKEN)


@tool
def add_workline_attestation(entity_kind: str, entity_id: str, kind: str) -> Dict[str, str]:
    """Add an attestation to a Workline entity (task, iteration, etc)."""
    attestation = client.add_attestation(entity_kind, entity_id, kind)
    return {
        "id": attestation.id,
        "entity_kind": attestation.entity_kind,
        "entity_id": attestation.entity_id,
        "kind": attestation.kind,
        "actor_id": attestation.actor_id,
    }


@tool
def create_workline_task_full(
    title: str,
    task_type: str = "feature",
    iteration_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    depends_on: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """Create a Workline task with iteration, dependencies, and owner."""
    body: Dict[str, object] = {"title": title, "type": task_type}
    if iteration_id:
        body["iteration_id"] = iteration_id
    if assignee_id:
        body["assignee_id"] = assignee_id
    if depends_on:
        body["depends_on"] = depends_on
    if description:
        body["description"] = description
    data = client._request("POST", client._project_path("tasks"), body)
    return {
        "id": data["id"],
        "title": data["title"],
        "type": data["type"],
        "status": data["status"],
        "iteration_id": data.get("iteration_id"),
        "assignee_id": data.get("assignee_id"),
    }


@tool
def create_workline_iteration(iteration_id: str, goal: str) -> Dict[str, str]:
    """Create a Workline iteration."""
    body = {"id": iteration_id, "goal": goal}
    data = client._request("POST", client._project_path("iterations"), body)
    return {"id": data["id"], "goal": data["goal"], "status": data["status"]}


@tool
def set_workline_iteration_status(iteration_id: str, status: str, force: bool = False) -> Dict[str, str]:
    """Update Workline iteration status (pending -> running -> delivered -> validated)."""
    body = {"status": status}
    url = client._project_path(f"iterations/{iteration_id}/status")
    if force:
        url = f"{url}?force=true"
    data = client._request("PATCH", url, body)
    return {"id": data["id"], "status": data["status"]}


@tool
def latest_workline_events(limit: int = 5) -> List[Dict[str, str]]:
    """Fetch the latest Workline events for audit/debugging."""
    events = client.events(limit)
    return [
        {
            "id": str(event.id),
            "type": event.type,
            "entity_kind": event.entity_kind,
            "entity_id": event.entity_id,
            "actor_id": event.actor_id,
        }
        for event in events
    ]


@tool
def list_workline_iterations(limit: int = 50) -> List[Dict[str, str]]:
    """List recent iterations."""
    data = client._request("GET", client._project_path(f"iterations?limit={limit}"))
    items = data.get("items", data)
    return [
        {"id": item["id"], "goal": item["goal"], "status": item["status"]}
        for item in items
    ]


@tool
def list_workline_tasks(iteration_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, str]]:
    """List tasks, optionally filtered by iteration or status."""
    params = []
    if iteration_id:
        params.append(f"iteration_id={iteration_id}")
    if status:
        params.append(f"status={status}")
    params.append(f"limit={limit}")
    query = "&".join(params)
    data = client._request("GET", client._project_path(f"tasks?{query}"))
    items = data.get("items", data)
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "status": item["status"],
            "iteration_id": item.get("iteration_id"),
        }
        for item in items
    ]


def _get_task(task_id: str) -> Optional[Dict[str, object]]:
    try:
        return client._request("GET", client._project_path(f"tasks/{task_id}"))
    except APIError as err:
        if err.status_code == 404:
            return None
        raise


def _create_problem_refinement_task(task_id: str) -> Dict[str, object]:
    body = {
        "id": task_id,
        "title": "Problem refinement",
        "type": "workshop",
        "description": "Capture the refined problem statement and assumptions.",
        "policy": {"preset": "workshop.discovery"},
    }
    return client._request("POST", client._project_path("tasks"), body)


def _update_task_work_outcomes(task_id: str, work_outcomes: Dict[str, object]) -> Dict[str, object]:
    body = {"work_outcomes": work_outcomes}
    url = client._project_path(f"tasks/{task_id}")
    try:
        return client._request("PATCH", url, body)
    except APIError as err:
        err_body = err.body if isinstance(err.body, dict) else {}
        code = ""
        if isinstance(err_body.get("error"), dict):
            code = err_body["error"].get("code", "")
        if code != "lease_conflict":
            raise
    client._request("POST", client._project_path(f"tasks/{task_id}/claim"), None)
    try:
        return client._request("PATCH", url, body)
    finally:
        client._request("POST", client._project_path(f"tasks/{task_id}/release"), None)


def ensure_problem_refinement_task(discovery_output: Dict[str, object]) -> str:
    task = _ensure_problem_refinement_task_exists()
    work_outcomes = task.get("work_outcomes") or {}
    work_outcomes["discovery"] = discovery_output
    _update_task_work_outcomes(task["id"], work_outcomes)
    return task["id"]


def _ensure_problem_refinement_task_exists() -> Dict[str, object]:
    task_id = "problem-refinement"
    task = _get_task(task_id)
    if task is None:
        task = _create_problem_refinement_task(task_id)
    return task


def get_problem_statement_from_workline() -> Optional[str]:
    task = _get_task("problem-refinement")
    if not task:
        return None
    work_outcomes = task.get("work_outcomes") or {}
    statement = work_outcomes.get("problem_statement")
    if isinstance(statement, str) and statement.strip():
        return statement
    return None


def set_problem_statement_in_workline(problem_statement: str) -> None:
    task = _ensure_problem_refinement_task_exists()
    work_outcomes = task.get("work_outcomes") or {}
    work_outcomes["problem_statement"] = problem_statement
    _update_task_work_outcomes(task["id"], work_outcomes)


def log_conversation(question: str, answer: str) -> None:
    task = _ensure_problem_refinement_task_exists()
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
    }
    client.append_work_outcomes(task["id"], "conversation", entry)


def get_problem_refinement_discovery() -> Optional[Dict[str, object]]:
    task = _get_task("problem-refinement")
    if not task:
        return None
    work_outcomes = task.get("work_outcomes") or {}
    discovery = work_outcomes.get("discovery")
    if isinstance(discovery, dict):
        return discovery
    if isinstance(discovery, str) and discovery.strip():
        return {"initial": discovery}
    return None


def ensure_agent_log_task() -> str:
    task_id = "agent-log"
    task = _get_task(task_id)
    if task is None:
        body = {
            "id": task_id,
            "title": "Agent actions log",
            "type": "docs",
            "description": "Chronological log of agent actions and decisions.",
        }
        task = client._request("POST", client._project_path("tasks"), body)
    return task["id"]


def append_agent_log(stage: str, summary: str, payload: Optional[Dict[str, object]] = None) -> None:
    task_id = ensure_agent_log_task()
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "summary": summary,
    }
    if payload:
        entry["payload"] = payload
    client.append_work_outcomes(task_id, "actions", entry)


def get_latest_log_payload(stage: str) -> Optional[Dict[str, object]]:
    task = _get_task("agent-log")
    if not task:
        return None
    work_outcomes = task.get("work_outcomes") or {}
    actions = work_outcomes.get("actions")
    if not isinstance(actions, list):
        return None
    for entry in reversed(actions):
        if entry.get("stage") == stage and isinstance(entry.get("payload"), dict):
            return entry["payload"]
    return None


def ask_human_question_local(question: str, options: Optional[List[str]] = None) -> str:
    if HUMAN_REVIEW_MODE == "interactive":
        if not sys.stdin.isatty():
            raise RuntimeError("stdin is not interactive; run without make or attach a TTY.")
        print("\n=== Question ===\n", flush=True)
        print(question, flush=True)
        if options:
            for idx, opt in enumerate(options, start=1):
                print(f"{idx}. {opt}", flush=True)
        while True:
            print("Your answer: ", end="", flush=True)
            answer = sys.stdin.readline()
            if answer == "":
                raise RuntimeError("stdin closed while waiting for input")
            answer = answer.strip()
            if answer:
                if options and answer.isdigit():
                    choice = int(answer)
                    if 1 <= choice <= len(options):
                        selected = options[choice - 1]
                        if selected.lower().startswith("other"):
                            detail = input("Please specify: ").strip()
                            if detail:
                                append_agent_log(
                                    "human.question",
                                    "Asked a human question",
                                    {"question": question, "answer": detail, "choice": selected},
                                )
                                log_conversation(question, detail)
                                return detail
                        append_agent_log(
                            "human.question",
                            "Asked a human question",
                            {"question": question, "answer": selected},
                        )
                        log_conversation(question, selected)
                        return selected
                append_agent_log("human.question", "Asked a human question", {"question": question, "answer": answer})
                log_conversation(question, answer)
                return answer
            print("Please enter a non-empty answer.", flush=True)
    raise RuntimeError("HUMAN_REVIEW_MODE must be interactive; simulation is disabled.")


@tool
def ask_human_question(question: str, options: Optional[List[str]] = None) -> str:
    """Ask a human for a decision or clarification."""
    return ask_human_question_local(question, options)


def ask_human_for_review(draft: str) -> str:
    if HUMAN_REVIEW_MODE == "interactive":
        if not sys.stdin.isatty():
            raise RuntimeError("stdin is not interactive; run without make or attach a TTY.")
        print("\n=== Draft Plan (for review) ===\n", flush=True)
        print(draft, flush=True)
        print("\n=== Provide edits or approvals ===\n", flush=True)
        print("1. approve", flush=True)
        print("2. request changes", flush=True)
        while True:
            print("Enter review feedback (or 'approve'): ", end="", flush=True)
            feedback = sys.stdin.readline()
            if feedback == "":
                raise RuntimeError("stdin closed while waiting for input")
            feedback = feedback.strip()
            if feedback:
                if feedback.isdigit():
                    if feedback == "1":
                        return "approve"
                    if feedback == "2":
                        return "request changes"
                return feedback
            print("Please enter a response (or type 'approve').", flush=True)
    raise RuntimeError("HUMAN_REVIEW_MODE must be interactive; simulation is disabled.")




def _run_agent(model: ChatOpenAI, system_prompt: str, user_input: str, tools: List) -> str:
    if _LC_AGENT_MODE == "graph" and lc_create_agent is not None:
        agent = lc_create_agent(
            model,
            tools=tools,
            system_prompt=system_prompt,
            debug=True,
            interrupt_after=["tools"],
        )
        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                return msg.content
            if isinstance(msg, dict) and msg.get("content"):
                return msg["content"]
        return ""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_input),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(model, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=1)
    return executor.invoke({})["output"]


def run_discovery(model: ChatOpenAI, problem_statement: str) -> str:
    system_prompt = (
        "You are a product planner starting a discovery phase. First, refine "
        "the provided problem statement into clear goals and scope. Only ask "
        "clarifying questions if critical details are missing. Use "
        "ask_human_question when needed, and always include 3-5 options plus "
        "'Other'. Ask at most one question at a time. "
        "'Other' in each question. Then provide assumptions and success metrics. "
        "Output sections: Refined Problem, Assumptions, Success Metrics, Actors."
    )
    tools = [ask_human_question]
    return _run_agent(model, system_prompt, problem_statement, tools)


def run_discovery_phase(model: ChatOpenAI, phase_name: str, context: str) -> str:
    system_prompt = (
        f"You are facilitating a discovery workshop phase: {phase_name}. "
        "Ask clarifying questions when needed using ask_human_question, and "
        "include 3-5 options plus 'Other' in each question. "
        "Ask at most one question at a time. "
        "Return a concise summary with decisions, risks, and open questions."
    )
    tools = [ask_human_question]
    return _run_agent(model, system_prompt, context, tools)


def continue_discovery(
    model: ChatOpenAI,
    problem_statement: str,
    existing: Optional[Dict[str, object]],
) -> Dict[str, object]:
    discovery: Dict[str, object] = existing or {}
    if "initial" not in discovery or not str(discovery.get("initial", "")).strip():
        discovery["initial"] = run_discovery(model, problem_statement)
    context = "\n\n".join(
        [
            f"Problem Statement:\n{problem_statement}",
            f"Initial Refinement:\n{discovery.get('initial','')}",
        ]
    )
    if "event_storming" not in discovery:
        discovery["event_storming"] = run_discovery_phase(model, "Event Storming", context)
    if "decision_workshop" not in discovery:
        discovery["decision_workshop"] = run_discovery_phase(model, "Decision Workshop", context)
    if "brainstorm" not in discovery:
        discovery["brainstorm"] = run_discovery_phase(model, "Brainstorm", context)
    return discovery


def run_planner(model: ChatOpenAI, discovery_output: str) -> str:
    system_prompt = (
        "You are a product owner running agile planning. Based on discovery, "
        "create a one-iteration plan with dependencies and owners. Workline "
        "iterations have no duration and we do not do capacity planning here. "
        "Assume the work is carried out by AI actors (e.g., PlannerAgent, "
        "OpsAgent, ReviewerAgent) and assign owners accordingly. Ask questions "
        "only when decisions are needed "
        "using ask_human_question, always providing 3-5 options plus 'Other'. "
        "Ask at most one question at a time. "
        "Output sections: Iteration ID, Sprint Goal, "
        "User Stories (with actors), Dependencies, Acceptance "
        "Criteria, Risks, Sprint Backlog (each item with owner and dependencies)."
    )
    tools = [ask_human_question]
    return _run_agent(model, system_prompt, discovery_output, tools)


def run_workline(model: ChatOpenAI, final_plan: str) -> str:
    system_prompt = (
        "You are a delivery lead. You will receive a finalized agile plan that "
        "includes an Iteration ID and Sprint Backlog. Do the following:\n"
        "1) Check if the iteration already exists using list_workline_iterations.\n"
        "2) If missing, create the iteration (status will be pending).\n"
        "3) Move iteration to running if not already.\n"
        "4) Check existing tasks for this iteration using list_workline_tasks; "
        "only create missing backlog items with create_workline_task_full.\n"
        "5) Ask the human if demo/review is approved. If approved, add an "
        "iteration.approved attestation on the iteration.\n"
        "6) Move iteration to delivered, then validated.\n"
        "7) Add ci.passed and review.approved attestations for each task.\n"
        "8) Call latest_workline_events.\n"
        "Use ask_human_question for any decision points and provide options. "
        "Ask at most one question at a time. Output a short "
        "'Workline Actions' section listing created task IDs and iteration status."
    )
    tools = [
        create_workline_iteration,
        set_workline_iteration_status,
        create_workline_task_full,
        add_workline_attestation,
        latest_workline_events,
        list_workline_iterations,
        list_workline_tasks,
        ask_human_question,
    ]
    return _run_agent(model, system_prompt, final_plan, tools)


def main() -> None:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    problem_statement = get_problem_statement_from_workline()
    if not problem_statement:
        problem_statement = ask_human_question_local(
            "What is the problem statement for this project?",
            options=[
                "Inventory management across plates, regions, and AZs",
                "Incident response control plan and change tracking",
                "Auditability and ownership for server lifecycle",
                "Other (type your own)",
            ],
        )
        set_problem_statement_in_workline(problem_statement)
    discovery = get_problem_refinement_discovery()
    if discovery:
        append_agent_log("discovery.resume", "Loaded discovery from Workline", {"output": discovery})
    else:
        append_agent_log("discovery.start", "Starting discovery phase", {"problem_statement": problem_statement})

    discovery = continue_discovery(model, problem_statement, discovery)
    append_agent_log("discovery.complete", "Completed discovery phases", {"output": discovery})

    refinement_task_id = ensure_problem_refinement_task(discovery)

    final_plan_payload = get_latest_log_payload("plan.approved")
    if final_plan_payload and isinstance(final_plan_payload.get("output"), str):
        final_plan = final_plan_payload["output"]
        append_agent_log("planning.resume", "Loaded approved plan from Workline", {"output": final_plan})
    else:
        append_agent_log("planning.start", "Starting iteration planning", {"discovery_summary": discovery})
        draft_plan = run_planner(model, json.dumps(discovery, indent=2))
        append_agent_log("planning.complete", "Drafted iteration plan", {"output": draft_plan})

        feedback = ask_human_for_review(draft_plan)
        if feedback.lower().startswith("approve"):
            final_plan = draft_plan
            append_agent_log("plan.approved", "Plan approved", {"output": final_plan})
        else:
            final_plan = (
                f"{draft_plan}\n\n---\nHuman Review Feedback:\n{feedback}\n"
                "Update the plan to address this feedback."
            )
            append_agent_log("plan.feedback", "Plan feedback provided", {"feedback": feedback})

    append_agent_log("execution.start", "Starting Workline execution", {"plan": final_plan})
    result = run_workline(model, final_plan)
    append_agent_log("execution.complete", "Completed Workline execution", {"result": result})

    print(
        json.dumps(
            {
                "discovery": discovery,
                "problem_refinement_task_id": refinement_task_id,
                "plan": final_plan,
                "workline": result,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
