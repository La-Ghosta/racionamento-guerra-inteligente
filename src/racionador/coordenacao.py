"""Lógica pura de coordenação entre grupos (visão do coordenador).

Agrega o status de vários grupos reusando ``relatorio_completo`` de
``racionamento.py`` — os limiares CRITICO/ALERTA/OK ficam num lugar só.
Sem banco, sem Streamlit: recebe a lista de Grupos pronta e devolve
dataclasses que a UI consome.
"""

from dataclasses import dataclass

from racionador.modelos import Grupo
from racionador.racionamento import relatorio_completo

# Ordem de severidade usada para agregar e ordenar (menor = mais urgente).
_PRIORIDADE_STATUS = {"CRITICO": 0, "ALERTA": 1, "SEM_DADOS": 2, "OK": 3}


@dataclass
class ResumoGrupo:
    """Resumo de um grupo para o painel do coordenador."""

    nome_grupo: str
    status: str  # CRITICO | ALERTA | OK | SEM_DADOS
    pedido_ajuda: bool
    localizacao: str | None
    regiao: str  # valor cru; "" = sem região (rótulo fica pra UI)
    total_pessoas: int
    suprimentos_criticos: list[str]  # nomes dos suprimentos com status CRITICO


@dataclass
class VisaoCoordenador:
    """Resultado agregado: lista ordenada por urgência + agrupamento por região."""

    resumos: list[ResumoGrupo]
    por_regiao: dict[str, list[ResumoGrupo]]


def _resumir_grupo(grupo: Grupo) -> ResumoGrupo:
    """Computa o resumo de um grupo: status geral = pior status entre suprimentos.

    Grupo sem pessoas ou sem suprimentos (relatorio_completo lança ValueError)
    recebe status SEM_DADOS — o coordenador ainda precisa vê-lo, ex.: se pediu ajuda.
    """
    try:
        relatorio = relatorio_completo(grupo)
        status = min(
            (info["status"] for info in relatorio.values()),
            key=_PRIORIDADE_STATUS.__getitem__,
        )
        suprimentos_criticos = [
            nome for nome, info in relatorio.items() if info["status"] == "CRITICO"
        ]
    except ValueError:
        status = "SEM_DADOS"
        suprimentos_criticos = []

    return ResumoGrupo(
        nome_grupo=grupo.nome_grupo,
        status=status,
        pedido_ajuda=grupo.pedido_ajuda,
        localizacao=grupo.localizacao,
        regiao=grupo.regiao,
        total_pessoas=len(grupo.pessoas),
        suprimentos_criticos=suprimentos_criticos,
    )


def visao_coordenador(grupos: list[Grupo]) -> VisaoCoordenador:
    """Monta a visão agregada dos grupos para o coordenador.

    Resumos ordenados por urgência: críticos primeiro, pedido de ajuda
    desempata, nome do grupo garante ordem determinística. ``por_regiao``
    agrupa pelo valor cru de ``regiao`` ("" forma o próprio bucket) com
    chaves em ordem alfabética e listas na mesma ordem de urgência.
    """
    resumos = sorted(
        (_resumir_grupo(g) for g in grupos),
        key=lambda r: (_PRIORIDADE_STATUS[r.status], not r.pedido_ajuda, r.nome_grupo),
    )

    por_regiao: dict[str, list[ResumoGrupo]] = {}
    for regiao in sorted({r.regiao for r in resumos}):
        por_regiao[regiao] = [r for r in resumos if r.regiao == regiao]

    return VisaoCoordenador(resumos=resumos, por_regiao=por_regiao)
