"""
CLI interativo para testar o agente Vita localmente.

Uso:
  python test_chat.py
  python test_chat.py --phone 5511987654321 --name "Ana Lima"

Comandos durante o chat:
  sair    — encerra a sessão
  reset   — nova conversa (novo thread_id)
  debug   — alterna exibição de qual agente respondeu
"""

import argparse
import time
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from agents.graph import graph


def run_chat(phone: str, name: str):
    thread_id = f"vitapet.{phone}"
    debug_mode = False

    print(f"\n{'='*50}")
    print(f"  VitaPet — Vita (agente de demonstração)")
    print(f"  Tutor: {name} | Tel: {phone}")
    print(f"  Thread: {thread_id}")
    print(f"  Comandos: 'sair', 'reset', 'debug'")
    print(f"{'='*50}\n")

    while True:
        try:
            user_input = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando...")
            break

        if not user_input:
            continue

        if user_input.lower() == "sair":
            print("Até logo!")
            break

        if user_input.lower() == "reset":
            thread_id = f"vitapet.{phone}.{int(time.time())}"
            print(f"[Nova conversa iniciada: {thread_id}]\n")
            continue

        if user_input.lower() == "debug":
            debug_mode = not debug_mode
            print(f"[Debug {'ativado' if debug_mode else 'desativado'}]\n")
            continue

        config = {"configurable": {"thread_id": thread_id}}

        result = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        last_ai = next(
            (m for m in reversed(result["messages"]) if hasattr(m, "content") and m.type == "ai"),
            None,
        )
        reply = last_ai.content if last_ai else "(sem resposta)"

        if debug_mode:
            current_agent = result.get("current_agent", "desconhecido")
            print(f"[agente: {current_agent}]")

        print(f"\nVita: {reply}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testa o agente Vita interativamente")
    parser.add_argument("--phone", default="5511999999999", help="Telefone do tutor (thread ID)")
    parser.add_argument("--name", default="Tutor Teste", help="Nome do tutor")
    args = parser.parse_args()

    run_chat(phone=args.phone, name=args.name)
