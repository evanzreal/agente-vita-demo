"""
LangGraph multi-agent graph para o agente Vita — VitaPet Clínica Veterinária.

Arquitetura (grafo único, estado compartilhado):
- orchestrator_node  : lê histórico completo e decide rota via structured output
- consulta_node      : agente especializado em consultas, vacinas, emergências
- consulta_tools     : executa tools do agente de consultas
- banho_tosa_node    : agente especializado em banho e tosa
- banho_tosa_tools   : executa tools do agente de banho/tosa

Todos os nós compartilham a mesma lista `messages` — memória automática.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated, Literal, Optional

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from typing_extensions import TypedDict

from agents.prompts import (
    CONSULTA_PROMPT_TEMPLATE,
    BANHO_TOSA_PROMPT_TEMPLATE,
    ORCHESTRATOR_PROMPT,
)
from agents.tools import (
    verificar_disponibilidade,
    agendar_consulta,
    agendar_banho_tosa,
    send_images_clinica,
    send_images_banho_tosa,
    buscar_orientacao_pos_consulta,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _date_context() -> dict[str, str]:
    now = datetime.now()
    weekdays_pt = {
        "Monday": "segunda-feira",
        "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira",
        "Friday": "sexta-feira",
        "Saturday": "sábado",
        "Sunday": "domingo",
    }
    return {
        "current_date": now.strftime("%d/%m/%Y"),
        "current_year": str(now.year),
        "current_weekday": weekdays_pt.get(now.strftime("%A"), now.strftime("%A")),
    }


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    current_agent: str   # "orchestrator" | "consulta" | "banho_tosa"
    tutor_phone: str
    tutor_name: str


# ---------------------------------------------------------------------------
# Orchestrator routing schema
# ---------------------------------------------------------------------------


class OrchestratorDecision(BaseModel):
    route: Literal["consulta", "banho_tosa", "respond"]
    response: Optional[str] = None  # usado apenas quando route == "respond"


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

_llms: dict = {}


def _make_llm(temperature: float = 0) -> ChatOpenAI:
    key = temperature
    if key not in _llms:
        _llms[key] = ChatOpenAI(
            model="openai/gpt-4o-mini",
            temperature=temperature,
            openai_api_key=os.environ["OPENROUTER_API_KEY"],
            openai_api_base="https://openrouter.ai/api/v1",
        )
    return _llms[key]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def orchestrator_node(state: AgentState) -> dict:
    """
    Lê a conversa completa e decide qual agente ativar.
    Usa structured output — nunca texto livre.
    """
    llm = _make_llm(temperature=0).with_structured_output(OrchestratorDecision)

    current_agent = state.get("current_agent", "")
    if current_agent and current_agent != "orchestrator":
        agent_context = (
            f"\n\nAGENTE ATUALMENTE ATIVO: {current_agent}\n"
            f"MANTENHA este agente. NUNCA retorne route='respond'."
        )
    else:
        agent_context = ""

    decision: OrchestratorDecision = llm.invoke([
        SystemMessage(content=ORCHESTRATOR_PROMPT + agent_context),
        *state["messages"],
    ])

    print(f"[DEBUG orchestrator] decision.route='{decision.route}'")

    if decision.route == "respond":
        return {
            "current_agent": "orchestrator",
            "messages": [AIMessage(content=decision.response or "")],
        }

    return {"current_agent": decision.route}


def consulta_node(state: AgentState) -> dict:
    print(f"[DEBUG consulta_node] chamado, {len(state['messages'])} msgs no histórico")
    llm = _make_llm(temperature=0.3).bind_tools([
        verificar_disponibilidade,
        agendar_consulta,
        send_images_clinica,
        buscar_orientacao_pos_consulta,
    ])
    system_prompt = CONSULTA_PROMPT_TEMPLATE.format(**_date_context())

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ])

    return {"messages": [response], "current_agent": "consulta"}


def banho_tosa_node(state: AgentState) -> dict:
    print(f"[DEBUG banho_tosa_node] chamado, {len(state['messages'])} msgs no histórico")
    llm = _make_llm(temperature=0.3).bind_tools([
        verificar_disponibilidade,
        agendar_banho_tosa,
        send_images_banho_tosa,
    ])
    system_prompt = BANHO_TOSA_PROMPT_TEMPLATE.format(**_date_context())

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ])

    return {"messages": [response], "current_agent": "banho_tosa"}


# ---------------------------------------------------------------------------
# Tool nodes (isolados por agente)
# ---------------------------------------------------------------------------

consulta_tool_node = ToolNode([
    verificar_disponibilidade,
    agendar_consulta,
    send_images_clinica,
    buscar_orientacao_pos_consulta,
])

banho_tosa_tool_node = ToolNode([
    verificar_disponibilidade,
    agendar_banho_tosa,
    send_images_banho_tosa,
])

# ---------------------------------------------------------------------------
# Conditional edges
# ---------------------------------------------------------------------------


def route_after_orchestrator(state: AgentState) -> str:
    agent = state.get("current_agent", "orchestrator")
    if agent == "consulta":
        return "consulta"
    if agent == "banho_tosa":
        return "banho_tosa"
    return END


def should_call_consulta_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "consulta_tools"
    return END


def should_call_banho_tosa_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "banho_tosa_tools"
    return END


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

builder = StateGraph(AgentState)

builder.add_node("orchestrator", orchestrator_node)
builder.add_node("consulta", consulta_node)
builder.add_node("consulta_tools", consulta_tool_node)
builder.add_node("banho_tosa", banho_tosa_node)
builder.add_node("banho_tosa_tools", banho_tosa_tool_node)


def route_entry(state: AgentState) -> str:
    agent = state.get("current_agent", "")
    print(f"\n[DEBUG route_entry] current_agent='{agent}'")
    return "orchestrator"


builder.add_conditional_edges(
    START,
    route_entry,
    {"orchestrator": "orchestrator", "consulta": "consulta", "banho_tosa": "banho_tosa"},
)

builder.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {"consulta": "consulta", "banho_tosa": "banho_tosa", END: END},
)

builder.add_conditional_edges(
    "consulta",
    should_call_consulta_tools,
    {"consulta_tools": "consulta_tools", END: END},
)
builder.add_edge("consulta_tools", "consulta")

builder.add_conditional_edges(
    "banho_tosa",
    should_call_banho_tosa_tools,
    {"banho_tosa_tools": "banho_tosa_tools", END: END},
)
builder.add_edge("banho_tosa_tools", "banho_tosa")

# ---------------------------------------------------------------------------
# Checkpointer (PostgreSQL)
# ---------------------------------------------------------------------------

from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

_pg_url = os.environ.get("POSTGRES_URL", "")
_pool = ConnectionPool(conninfo=_pg_url, max_size=10, kwargs={"autocommit": True})
_checkpointer = PostgresSaver(_pool)
_checkpointer.setup()

graph = builder.compile(checkpointer=_checkpointer)
