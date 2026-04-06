"""
Mock tools para o agente Vita — VitaPet Clínica Veterinária.

Em produção, estas tools chamarão APIs reais de agendamento e CRM.
Para demonstração, imprimem no console e retornam strings de confirmação.
"""

from langchain_core.tools import tool
from typing import Literal

BASE_URL = "https://raw.githubusercontent.com/vitapet-demo/fotos/main"

# ---------------------------------------------------------------------------
# Imagens por categoria
# ---------------------------------------------------------------------------

IMAGES_CONSULTA: dict[str, list[str]] = {
    "estrutura": [
        f"{BASE_URL}/estrutura/estrutura_{i:02d}.jpg" for i in range(1, 8)
    ],
    "equipe": [
        f"{BASE_URL}/equipe/equipe_{i:02d}.jpg" for i in range(1, 6)
    ],
    "animais": [
        f"{BASE_URL}/animais/animais_{i:02d}.jpg" for i in range(1, 9)
    ],
    "internacao": [
        f"{BASE_URL}/internacao/internacao_{i:02d}.jpg" for i in range(1, 5)
    ],
}

IMAGES_BANHO_TOSA: dict[str, list[str]] = {
    "antes_depois": [
        f"{BASE_URL}/banho_tosa/antes_depois_{i:02d}.jpg" for i in range(1, 7)
    ],
    "espaco": [
        f"{BASE_URL}/banho_tosa/espaco_{i:02d}.jpg" for i in range(1, 5)
    ],
}

# ---------------------------------------------------------------------------
# Tipos de categoria
# ---------------------------------------------------------------------------

CategoriaConsulta = Literal["estrutura", "equipe", "animais", "internacao"]
CategoriaBanhoTosa = Literal["antes_depois", "espaco"]

EspecialidadeConsulta = Literal[
    "clinica_geral",
    "vacinas",
    "dermatologia",
    "cardiologia",
    "ortopedia",
    "oftalmologia",
    "odontologia",
    "emergencia",
]

TipoServicoBanhoTosa = Literal[
    "banho_simples",
    "banho_tosa_higienica",
    "tosa_completa",
    "tosa_na_tesoura",
    "spa_completo",
]

# ---------------------------------------------------------------------------
# Tools de agendamento
# ---------------------------------------------------------------------------


@tool
def verificar_disponibilidade(
    especialidade: EspecialidadeConsulta,
    data_preferida: str,
    periodo: Literal["manha", "tarde", "qualquer"],
) -> str:
    """Verifica disponibilidade de horários para consulta ou serviço na clínica.

    Args:
        especialidade: tipo de consulta desejada
        data_preferida: data no formato DD/MM/AAAA ou descrição como "esta semana", "semana que vem"
        periodo: preferência de horário (manha, tarde ou qualquer)
    """
    print(f"[TOOL] verificar_disponibilidade esp={especialidade} data={data_preferida} periodo={periodo}")

    # Mock: retorna horários fictícios mas realistas
    horarios_mock = {
        "manha": ["08:00", "09:30", "10:00", "11:30"],
        "tarde": ["14:00", "15:30", "16:00", "17:30"],
        "qualquer": ["08:00", "09:30", "14:00", "15:30", "17:30"],
    }
    horarios = horarios_mock.get(periodo, horarios_mock["qualquer"])

    return (
        f"Horários disponíveis para {especialidade.replace('_', ' ')} em {data_preferida}:\n"
        + "\n".join(f"• {h}" for h in horarios[:3])
        + "\n\nQual desses funciona melhor para você?"
    )


@tool
def agendar_consulta(
    tutor_nome: str,
    tutor_telefone: str,
    pet_nome: str,
    pet_especie: Literal["cao", "gato", "outros"],
    pet_raca: str,
    pet_idade: str,
    especialidade: EspecialidadeConsulta,
    data_horario: str,
    observacoes: str = "",
) -> str:
    """Confirma o agendamento de uma consulta ou serviço na VitaPet.

    Args:
        tutor_nome: nome completo do tutor
        tutor_telefone: telefone do tutor com DDD
        pet_nome: nome do pet
        pet_especie: espécie do animal (cao, gato, outros)
        pet_raca: raça do pet
        pet_idade: idade do pet
        especialidade: tipo de consulta agendada
        data_horario: data e horário confirmados
        observacoes: informações adicionais relevantes
    """
    print(
        f"[TOOL] agendar_consulta: tutor={tutor_nome} tel={tutor_telefone} "
        f"pet={pet_nome} esp={pet_especie} esp={especialidade} "
        f"data={data_horario} obs={observacoes}"
    )
    return "Agendamento confirmado com sucesso."


@tool
def agendar_banho_tosa(
    tutor_nome: str,
    tutor_telefone: str,
    pet_nome: str,
    pet_especie: Literal["cao", "gato"],
    pet_raca: str,
    pet_porte: Literal["pequeno", "medio", "grande", "gigante"],
    servico: TipoServicoBanhoTosa,
    data_horario: str,
    observacoes: str = "",
) -> str:
    """Confirma o agendamento de banho e/ou tosa na VitaPet.

    Args:
        tutor_nome: nome completo do tutor
        tutor_telefone: telefone do tutor com DDD
        pet_nome: nome do pet
        pet_especie: espécie (cao ou gato)
        pet_raca: raça do pet
        pet_porte: porte do animal
        servico: tipo de serviço de banho/tosa desejado
        data_horario: data e horário confirmados
        observacoes: informações adicionais
    """
    print(
        f"[TOOL] agendar_banho_tosa: tutor={tutor_nome} tel={tutor_telefone} "
        f"pet={pet_nome} porte={pet_porte} servico={servico} data={data_horario}"
    )
    return "Agendamento de banho/tosa confirmado com sucesso."


# ---------------------------------------------------------------------------
# Tools de imagens
# ---------------------------------------------------------------------------


@tool
def send_images_clinica(categoria: CategoriaConsulta) -> str:
    """Envia fotos da estrutura e equipe da VitaPet por categoria.

    Categorias disponíveis:
    - estrutura: fotos das salas, recepção, equipamentos e instalações
    - equipe: fotos dos veterinários e equipe clínica
    - animais: fotos de pets atendidos (com autorização dos tutores)
    - internacao: fotos do setor de internação e UTI pet

    Args:
        categoria: qual categoria de fotos enviar
    """
    print(f"[TOOL] send_images_clinica categoria={categoria}")
    links = IMAGES_CONSULTA.get(categoria, [])
    return "\n\n".join(links)


@tool
def send_images_banho_tosa(categoria: CategoriaBanhoTosa) -> str:
    """Envia fotos do serviço de banho e tosa da VitaPet.

    Categorias disponíveis:
    - antes_depois: transformações de pets antes e depois da tosa
    - espaco: fotos do espaço de banho e tosa

    Args:
        categoria: qual categoria de fotos enviar
    """
    print(f"[TOOL] send_images_banho_tosa categoria={categoria}")
    links = IMAGES_BANHO_TOSA.get(categoria, [])
    return "\n\n".join(links)


# ---------------------------------------------------------------------------
# Tool de orientações pós-consulta
# ---------------------------------------------------------------------------


@tool
def buscar_orientacao_pos_consulta(
    procedimento: Literal[
        "castracao",
        "cirurgia_geral",
        "vacinacao",
        "internacao",
        "tosa",
        "exames",
        "emergencia",
    ]
) -> str:
    """Retorna orientações pós-consulta ou pós-procedimento para o tutor.

    Args:
        procedimento: tipo de procedimento realizado ou dúvida do tutor
    """
    print(f"[TOOL] buscar_orientacao_pos_consulta procedimento={procedimento}")

    orientacoes = {
        "castracao": (
            "Cuidados após a castração:\n"
            "• Mantenha o pet em repouso por 7–10 dias, evite pulos e corridas\n"
            "• Impeça que ele lamber a sutura — use colar elizabetano se necessário\n"
            "• Ofereça água fresca à vontade; ração somente 6h após retornar em casa\n"
            "• Higienize a sutura com soro fisiológico 1x/dia\n"
            "• Retorno para retirada de pontos em 10 dias\n"
            "• Em caso de inchaço, vermelhidão ou secreção, contate a clínica imediatamente"
        ),
        "cirurgia_geral": (
            "Cuidados pós-cirurgia:\n"
            "• Repouso absoluto nas primeiras 48h\n"
            "• Administre os medicamentos nos horários indicados pelo veterinário\n"
            "• Mantenha a sutura limpa e seca\n"
            "• Evite banho até liberação médica\n"
            "• Observe sinais de alerta: vômito, letargia, febre, sangramento"
        ),
        "vacinacao": (
            "Após a vacinação:\n"
            "• É normal leve sonolência e redução de apetite nas primeiras 24h\n"
            "• Evite banho nas 48h seguintes à aplicação\n"
            "• Monitore reações alérgicas: inchaço no focinho, urticária, dificuldade respiratória\n"
            "• Se notar qualquer reação adversa, retorne à clínica imediatamente\n"
            "• Próxima dose conforme carteirinha de vacinação"
        ),
        "internacao": (
            "Orientações para pets em internação:\n"
            "• Visitas conforme horário informado pela equipe\n"
            "• Pode trazer objeto com cheiro familiar (cobertinha, brinquedo)\n"
            "• Informações sobre o estado do pet a cada 12h pelo nosso WhatsApp\n"
            "• Em caso de piora, a equipe entrará em contato imediatamente"
        ),
        "tosa": (
            "Após a tosa:\n"
            "• Evite exposição ao sol por 24h (pele mais sensível após tosa)\n"
            "• Em dias frios, proteja pets de porte menor com roupinha\n"
            "• Use hidratante específico se indicado pelo tosador\n"
            "• Próxima tosa recomendada: 45–60 dias (varia por raça)"
        ),
        "exames": (
            "Sobre seus exames:\n"
            "• Resultados ficam prontos em 24–48h (laboratoriais) ou na hora (imagem)\n"
            "• Você receberá uma notificação por WhatsApp quando os resultados chegarem\n"
            "• Agende retorno para interpretação dos resultados com o veterinário\n"
            "• Guarde sempre uma cópia física ou digital do histórico do seu pet"
        ),
        "emergencia": (
            "Sinais de emergência que requerem atendimento IMEDIATO:\n"
            "• Dificuldade respiratória ou engasgo\n"
            "• Convulsões ou tremores\n"
            "• Sangramento intenso\n"
            "• Abdômen distendido e dor intensa\n"
            "• Inconsciência ou não responsividade\n"
            "• Suspeita de ingestão de veneno\n\n"
            "📞 Nosso plantão 24h: (11) 9999-0000\n"
            "🏥 Endereço de emergência: Rua das Palmeiras, 142 — atendemos 24 horas"
        ),
    }
    return orientacoes.get(procedimento, "Orientação não encontrada. Por favor, contate a clínica.")
