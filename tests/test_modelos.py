"""Testes das dataclasses Pessoa, Suprimento e Grupo."""

import pytest

from racionador.modelos import Grupo, Pessoa, Suprimento


def test_pessoa_adulta_tem_fator_um():
    p = Pessoa(nome="Ana", idade=30)
    assert p.fator_consumo == 1.0


def test_pessoa_crianca_tem_fator_zero_seis():
    p = Pessoa(nome="Beto", idade=8)
    assert p.fator_consumo == 0.6


def test_pessoa_idosa_tem_fator_zero_oito():
    p = Pessoa(nome="Clara", idade=70)
    assert p.fator_consumo == 0.8


def test_pessoa_limite_doze_anos_tem_fator_um():
    p = Pessoa(nome="Davi", idade=12)
    assert p.fator_consumo == 1.0


def test_pessoa_limite_sessenta_e_cinco_anos_tem_fator_um():
    p = Pessoa(nome="Eva", idade=65)
    assert p.fator_consumo == 1.0


def test_suprimento_quantidade_negativa_lanca_value_error():
    with pytest.raises(ValueError):
        Suprimento(
            nome="Agua", quantidade_atual=-1.0, consumo_diario_padrao=2.0, unidade_medida="L"
        )


def test_suprimento_consumo_negativo_lanca_value_error():
    with pytest.raises(ValueError):
        Suprimento(
            nome="Agua", quantidade_atual=10.0, consumo_diario_padrao=-1.0, unidade_medida="L"
        )


def test_grupo_tem_defaults_de_coordenacao():
    g = Grupo(nome_grupo="Alpha")
    assert g.regiao == ""
    assert g.pedido_ajuda is False


def test_grupo_aceita_regiao_e_pedido_ajuda():
    g = Grupo(nome_grupo="Bravo", regiao="Centro-Oeste", pedido_ajuda=True)
    assert g.regiao == "Centro-Oeste"
    assert g.pedido_ajuda is True
