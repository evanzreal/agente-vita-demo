"""
FastAPI server para o agente Vita — VitaPet Clínica Veterinária.

Endpoints:
  POST /chat       — conversa normal (inbound)
  POST /chat       — formulário pré-preenchido (FORM_LEAD_CONSULTA / FORM_LEAD_BANHO_TOSA)
  GET  /health     — health check
"""

import os
import time

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from typing import Optional

from agents.graph import graph

app = FastAPI(title="VitaPet — Vita API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class FormDataConsulta(BaseModel):
    """Campos do formulário de agendamento de consulta."""
    nomeTutor: str
    telefone: Optional[str] = ""
    email: Optional[str] = ""
    nomePet: str
    especiePet: Optional[str] = ""
    racaPet: Optional[str] = ""
    idadePet: Optional[str] = ""
    motivoConsulta: str
    especialidade: Optional[str] = ""
    dataPreferida: Optional[str] = ""
    periodoPreferido: Optional[str] = ""


class FormDataBanhoTosa(BaseModel):
    """Campos do formulário de agendamento de banho e tosa."""
    nomeTutor: str
    telefone: Optional[str] = ""
    email: Optional[str] = ""
    nomePet: str
    especiePet: Optional[str] = ""
    racaPet: Optional[str] = ""
    portePet: Optional[str] = ""
    servicoDesejado: Optional[str] = ""
    dataPreferida: Optional[str] = ""
    periodoPreferido: Optional[str] = ""
    observacoes: Optional[str] = ""


class ChatRequest(BaseModel):
    message: str
    sessionId: str
    timestamp: str = ""
    formDataConsulta: Optional[FormDataConsulta] = None
    formDataBanhoTosa: Optional[FormDataBanhoTosa] = None


class ChatResponse(BaseModel):
    output: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FORM_CODE_CONSULTA = "FORM_LEAD_CONSULTA"
FORM_CODE_BANHO_TOSA = "FORM_LEAD_BANHO_TOSA"


def _build_consulta_context(f: FormDataConsulta) -> str:
    especialidade_str = f.especialidade if f.especialidade else "não informada"
    data_str = f.dataPreferida if f.dataPreferida else "não informada"
    periodo_str = f.periodoPreferido if f.periodoPreferido else "não informado"
    raca_str = f.racaPet if f.racaPet else "não informada"
    idade_str = f.idadePet if f.idadePet else "não informada"
    especie_str = f.especiePet if f.especiePet else "não informada"
    return (
        f"CONTEXTO DO FORMULÁRIO — LEAD QUALIFICADO:\n"
        f"Tutor: {f.nomeTutor}\n"
        f"Telefone: {f.telefone}\n"
        f"E-mail: {f.email}\n"
        f"Nome do pet: {f.nomePet}\n"
        f"Espécie: {especie_str}\n"
        f"Raça: {raca_str}\n"
        f"Idade: {idade_str}\n"
        f"Motivo da consulta: {f.motivoConsulta}\n"
        f"Especialidade desejada: {especialidade_str}\n"
        f"Data preferida: {data_str}\n"
        f"Período preferido: {periodo_str}\n"
    )


def _build_banho_tosa_context(f: FormDataBanhoTosa) -> str:
    servico_str = f.servicoDesejado if f.servicoDesejado else "não informado"
    data_str = f.dataPreferida if f.dataPreferida else "não informada"
    periodo_str = f.periodoPreferido if f.periodoPreferido else "não informado"
    porte_str = f.portePet if f.portePet else "não informado"
    obs_str = f.observacoes if f.observacoes else "nenhuma"
    raca_str = f.racaPet if f.racaPet else "não informada"
    especie_str = f.especiePet if f.especiePet else "não informada"
    return (
        f"CONTEXTO DO FORMULÁRIO — LEAD QUALIFICADO:\n"
        f"Tutor: {f.nomeTutor}\n"
        f"Telefone: {f.telefone}\n"
        f"E-mail: {f.email}\n"
        f"Nome do pet: {f.nomePet}\n"
        f"Espécie: {especie_str}\n"
        f"Raça: {raca_str}\n"
        f"Porte: {porte_str}\n"
        f"Serviço desejado: {servico_str}\n"
        f"Data preferida: {data_str}\n"
        f"Período preferido: {periodo_str}\n"
        f"Observações: {obs_str}\n"
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    is_form = req.message in (FORM_CODE_CONSULTA, FORM_CODE_BANHO_TOSA)
    if is_form:
        thread_id = f"vitapet.{req.sessionId}.{int(time.time())}"
    else:
        thread_id = f"vitapet.{req.sessionId}"
    config = {"configurable": {"thread_id": thread_id}}

    # --- Fluxo FORM_LEAD_CONSULTA ---
    if req.message == FORM_CODE_CONSULTA and req.formDataConsulta:
        context = _build_consulta_context(req.formDataConsulta)
        internal_message = (
            f"FORM_LEAD_CONSULTA\n\n"
            f"{context}\n"
            f"Instrução: Você é Vita da VitaPet. O tutor preencheu o formulário de interesse "
            f"em consulta veterinária. Faça a primeira abordagem ativa usando o nome do tutor e "
            f"os dados do pet. Seja calorosa, humana e tranquilizadora — como alguém que realmente "
            f"se preocupa com a saúde e bem-estar do animal.\n\n"
            f"MODO OUTBOUND — INSTRUÇÕES ESPECIAIS:\n"
            f"- Você já tem as informações do formulário. Use-as para personalizar cada mensagem.\n"
            f"- Demonstre que leu os dados: chame o pet pelo nome, mencione o motivo da consulta.\n"
            f"- Antecipe preocupações comuns do tutor (se é sério, se precisa de exames, se tem jejum) "
            f"e responda antes mesmo de serem perguntadas, no momento certo.\n"
            f"- Use as fotos da clínica (tool send_images_clinica) estrategicamente: quando o tutor "
            f"demonstrar dúvida sobre a estrutura ou equipe, mande as fotos para gerar confiança.\n"
            f"- Conduza naturalmente para a confirmação do agendamento.\n"
            f"- Não se apresente como IA ou bot."
        )
        result = graph.invoke(
            {
                "messages": [HumanMessage(content=internal_message)],
                "current_agent": "consulta",
            },
            config=config,
        )

    # --- Fluxo FORM_LEAD_BANHO_TOSA ---
    elif req.message == FORM_CODE_BANHO_TOSA and req.formDataBanhoTosa:
        context = _build_banho_tosa_context(req.formDataBanhoTosa)
        internal_message = (
            f"FORM_LEAD_BANHO_TOSA\n\n"
            f"{context}\n"
            f"Instrução: Você é Vita da VitaPet. O tutor preencheu o formulário de interesse "
            f"em banho e tosa. Faça a primeira abordagem ativa usando o nome do tutor e os dados "
            f"do pet. Seja animada, carinhosa e consultiva — como alguém que ama deixar cada pet lindo.\n\n"
            f"MODO OUTBOUND — INSTRUÇÕES ESPECIAIS:\n"
            f"- Use os dados do formulário para personalizar: mencione a raça e porte do pet.\n"
            f"- Sugira o serviço mais adequado com base no que foi informado.\n"
            f"- Ofereça fotos de antes e depois (tool send_images_banho_tosa) proativamente "
            f"para criar desejo e confiança.\n"
            f"- Conduza naturalmente para a confirmação do agendamento.\n"
            f"- Não se apresente como IA ou bot."
        )
        result = graph.invoke(
            {
                "messages": [HumanMessage(content=internal_message)],
                "current_agent": "banho_tosa",
            },
            config=config,
        )

    # --- Fluxo normal: conversa inbound ---
    else:
        result = graph.invoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )

    last_ai = next(
        (m for m in reversed(result["messages"]) if hasattr(m, "content") and m.type == "ai"),
        None,
    )
    reply = last_ai.content if last_ai else ""

    user_msg = req.message if not is_form else f"[FORM] {req.message}"
    print(f"\n[{thread_id}]")
    print(f"👤 {user_msg}")
    print(f"🐾 {reply}\n")

    return ChatResponse(output=reply)


@app.get("/health")
def health():
    return {"status": "ok"}
