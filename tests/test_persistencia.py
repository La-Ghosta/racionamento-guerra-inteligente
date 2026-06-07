"""Testes de persistencia: salvar e carregar Grupo em JSON."""

import datetime
import json

from racionador.modelos import Grupo, Pessoa, Suprimento
from racionador.persistencia import carregar_grupo, salvar_grupo


def test_salvar_e_carregar_grupo_simples(tmp_path):
    caminho = tmp_path / "grupo.json"
    grupo = Grupo(nome_grupo="Familia Teste")

    salvar_grupo(grupo, caminho)
    carregado = carregar_grupo(caminho)

    assert carregado is not None
    assert carregado.nome_grupo == "Familia Teste"
    assert carregado.pessoas == []
    assert carregado.suprimentos == []


def test_carregar_arquivo_inexistente_retorna_none(tmp_path):
    caminho = tmp_path / "nao_existe.json"
    resultado = carregar_grupo(caminho)
    assert resultado is None


def test_serializa_pessoas_e_suprimentos_corretamente(tmp_path):
    caminho = tmp_path / "grupo_completo.json"
    pessoa = Pessoa(nome="Carlos", idade=40)
    suprimento = Suprimento(
        nome="Agua", quantidade_atual=20.0, consumo_diario_padrao=2.0, unidade_medida="L"
    )
    grupo = Grupo(nome_grupo="Equipe", pessoas=[pessoa], suprimentos=[suprimento])

    salvar_grupo(grupo, caminho)
    carregado = carregar_grupo(caminho)

    assert carregado is not None
    assert len(carregado.pessoas) == 1
    assert carregado.pessoas[0].nome == "Carlos"
    assert carregado.pessoas[0].idade == 40
    assert carregado.pessoas[0].fator_consumo == 1.0

    assert len(carregado.suprimentos) == 1
    assert carregado.suprimentos[0].nome == "Agua"
    assert carregado.suprimentos[0].quantidade_atual == 20.0
    assert carregado.suprimentos[0].consumo_diario_padrao == 2.0
    assert carregado.suprimentos[0].unidade_medida == "L"
    assert carregado.suprimentos[0].categoria == "outro"
    assert carregado.suprimentos[0].validade is None


def test_roundtrip_com_categoria_e_validade(tmp_path):
    caminho = tmp_path / "grupo_validade.json"
    suprimento = Suprimento(
        nome="Soro",
        quantidade_atual=10.0,
        consumo_diario_padrao=1.0,
        unidade_medida="un",
        categoria="remedio",
        validade=datetime.date(2026, 12, 31),
    )
    grupo = Grupo(nome_grupo="Equipe", suprimentos=[suprimento])

    salvar_grupo(grupo, caminho)
    carregado = carregar_grupo(caminho)

    assert carregado is not None
    assert carregado.suprimentos[0].categoria == "remedio"
    assert carregado.suprimentos[0].validade == datetime.date(2026, 12, 31)


def test_roundtrip_com_regiao_e_pedido_ajuda(tmp_path):
    caminho = tmp_path / "grupo_regiao.json"
    grupo = Grupo(nome_grupo="Equipe", regiao="Norte", pedido_ajuda=True)

    salvar_grupo(grupo, caminho)
    carregado = carregar_grupo(caminho)

    assert carregado is not None
    assert carregado.regiao == "Norte"
    assert carregado.pedido_ajuda is True


def test_carrega_json_antigo_sem_campos_novos(tmp_path):
    caminho = tmp_path / "grupo_antigo.json"
    dados_antigos = {
        "nome_grupo": "Legado",
        "pessoas": [],
        "suprimentos": [
            {
                "nome": "Agua",
                "quantidade_atual": 20.0,
                "consumo_diario_padrao": 2.0,
                "unidade_medida": "L",
            }
        ],
        "localizacao": None,
    }
    caminho.write_text(json.dumps(dados_antigos), encoding="utf-8")

    carregado = carregar_grupo(caminho)

    assert carregado is not None
    assert carregado.suprimentos[0].categoria == "outro"
    assert carregado.suprimentos[0].validade is None
    assert carregado.regiao == ""
    assert carregado.pedido_ajuda is False
