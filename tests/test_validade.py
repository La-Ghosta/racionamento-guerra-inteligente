"""Testes da lógica pura de validade (datas fixas, sem mock de relógio)."""

import datetime

from racionador.modelos import Suprimento
from racionador.validade import alertas_validade, status_validade

HOJE = datetime.date(2026, 6, 10)


def _suprimento(nome: str = "Item", validade: datetime.date | None = None) -> Suprimento:
    return Suprimento(
        nome=nome,
        quantidade_atual=1.0,
        consumo_diario_padrao=1.0,
        unidade_medida="un",
        validade=validade,
    )


def test_sem_validade_retorna_vazio():
    assert status_validade(None, HOJE) == ""


def test_validade_distante_retorna_vazio():
    assert status_validade(HOJE + datetime.timedelta(days=30), HOJE) == ""


def test_validade_hoje_retorna_vence_hoje():
    assert status_validade(HOJE, HOJE) == "VENCE_HOJE"


def test_limite_da_janela_de_aviso():
    assert status_validade(HOJE + datetime.timedelta(days=3), HOJE) == "VENCE_HOJE"
    assert status_validade(HOJE + datetime.timedelta(days=4), HOJE) == ""


def test_validade_passada_retorna_esgotado():
    assert status_validade(HOJE - datetime.timedelta(days=1), HOJE) == "ESGOTADO"


def test_alertas_filtra_e_ordena_mais_urgente_primeiro():
    suprimentos = [
        _suprimento("Sem validade"),
        _suprimento("Distante", HOJE + datetime.timedelta(days=30)),
        _suprimento("Vencendo", HOJE + datetime.timedelta(days=2)),
        _suprimento("Vencido", HOJE - datetime.timedelta(days=1)),
    ]
    assert alertas_validade(suprimentos, HOJE) == [
        ("Vencido", "ESGOTADO", HOJE - datetime.timedelta(days=1)),
        ("Vencendo", "VENCE_HOJE", HOJE + datetime.timedelta(days=2)),
    ]
