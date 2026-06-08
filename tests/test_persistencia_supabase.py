"""Testes da persistencia Supabase com client mockado (sem banco real)."""

import datetime
from unittest.mock import MagicMock

import pytest

from racionador.modelos import Grupo, Pessoa, Suprimento
from racionador.persistencia_supabase import (
    carregar_grupo,
    carregar_todos_grupos,
    criar_cliente,
    listar_grupos,
    salvar_grupo,
)


def _grupo_completo() -> Grupo:
    return Grupo(
        nome_grupo="Equipe Alfa",
        localizacao="Kyiv",
        regiao="Norte",
        pedido_ajuda=True,
        pessoas=[Pessoa(nome="Carlos", idade=40)],
        suprimentos=[
            Suprimento(
                nome="Agua",
                quantidade_atual=20.0,
                consumo_diario_padrao=2.0,
                unidade_medida="L",
                categoria="agua",
                validade=datetime.date(2026, 12, 31),
            )
        ],
    )


@pytest.fixture
def cliente_salvar():
    """Client mockado cujo upsert de grupos devolve o id do grupo."""
    cliente = MagicMock()
    cliente.table.return_value.upsert.return_value.execute.return_value.data = [{"id": 7}]
    return cliente


@pytest.fixture
def cliente_carregar():
    """Client mockado que devolve dados distintos por tabela."""
    tabela_grupos = MagicMock()
    tabela_grupos.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": 7,
            "nome": "Equipe Alfa",
            "localizacao": "Kyiv",
            "regiao": "Norte",
            "pedido_ajuda": True,
            "criado_em": "2026-06-01",
        }
    ]

    tabela_pessoas = MagicMock()
    tabela_pessoas.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": 1, "grupo_id": 7, "nome": "Carlos", "idade": 40}
    ]

    tabela_suprimentos = MagicMock()
    tabela_suprimentos.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": 2,
            "grupo_id": 7,
            "nome": "Agua",
            "quantidade_atual": 20.0,
            "consumo_diario_padrao": 2.0,
            "unidade_medida": "L",
            "categoria": "agua",
            "validade": "2026-12-31",
        }
    ]

    tabelas = {
        "grupos": tabela_grupos,
        "pessoas": tabela_pessoas,
        "suprimentos": tabela_suprimentos,
    }
    cliente = MagicMock()
    cliente.table.side_effect = tabelas.__getitem__
    return cliente


# --- criar_cliente ---


def test_criar_cliente_sem_env_retorna_none(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    assert criar_cliente() is None


# --- salvar_grupo ---


def test_salvar_grupo_happy_path(cliente_salvar):
    grupo = _grupo_completo()

    assert salvar_grupo(grupo, cliente_salvar) is True

    tabelas_chamadas = [chamada.args[0] for chamada in cliente_salvar.table.call_args_list]
    assert tabelas_chamadas == ["grupos", "pessoas", "suprimentos", "pessoas", "suprimentos"]

    chain = cliente_salvar.table.return_value
    chain.upsert.assert_called_once_with(
        {
            "nome": "Equipe Alfa",
            "localizacao": "Kyiv",
            "regiao": "Norte",
            "pedido_ajuda": True,
        },
        on_conflict="nome",
    )
    chain.delete.return_value.eq.assert_any_call("grupo_id", 7)

    inserts = [chamada.args[0] for chamada in chain.insert.call_args_list]
    assert inserts[0] == [{"grupo_id": 7, "nome": "Carlos", "idade": 40}]
    assert inserts[1] == [
        {
            "grupo_id": 7,
            "nome": "Agua",
            "quantidade_atual": 20.0,
            "consumo_diario_padrao": 2.0,
            "unidade_medida": "L",
            "categoria": "agua",
            "validade": "2026-12-31",
        }
    ]


def test_salvar_grupo_vazio_nao_insere(cliente_salvar):
    grupo = Grupo(nome_grupo="Vazio")

    assert salvar_grupo(grupo, cliente_salvar) is True
    cliente_salvar.table.return_value.insert.assert_not_called()


def test_salvar_grupo_erro_conexao_retorna_false():
    cliente = MagicMock()
    cliente.table.side_effect = Exception("connection refused")
    assert salvar_grupo(_grupo_completo(), cliente) is False


# --- carregar_grupo ---


def test_carregar_grupo_happy_path(cliente_carregar):
    grupo = carregar_grupo("Equipe Alfa", cliente_carregar)

    assert grupo is not None
    assert grupo.nome_grupo == "Equipe Alfa"
    assert grupo.localizacao == "Kyiv"
    assert grupo.regiao == "Norte"
    assert grupo.pedido_ajuda is True

    assert len(grupo.pessoas) == 1
    assert grupo.pessoas[0].nome == "Carlos"
    assert grupo.pessoas[0].idade == 40
    assert grupo.pessoas[0].fator_consumo == 1.0

    assert len(grupo.suprimentos) == 1
    sup = grupo.suprimentos[0]
    assert sup.nome == "Agua"
    assert sup.quantidade_atual == 20.0
    assert sup.consumo_diario_padrao == 2.0
    assert sup.unidade_medida == "L"
    assert sup.categoria == "agua"
    assert sup.validade == datetime.date(2026, 12, 31)


def test_carregar_grupo_colunas_nulas_usam_defaults():
    """Linha antiga (antes da migração) com regiao/pedido_ajuda nulos → defaults."""
    tabela_grupos = MagicMock()
    tabela_grupos.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": 7, "nome": "Legado", "localizacao": None, "regiao": None, "pedido_ajuda": None}
    ]

    tabela_vazia = MagicMock()
    tabela_vazia.select.return_value.eq.return_value.execute.return_value.data = []

    tabelas = {"grupos": tabela_grupos, "pessoas": tabela_vazia, "suprimentos": tabela_vazia}
    cliente = MagicMock()
    cliente.table.side_effect = tabelas.__getitem__

    grupo = carregar_grupo("Legado", cliente)

    assert grupo is not None
    assert grupo.regiao == ""
    assert grupo.pedido_ajuda is False


def test_carregar_grupo_inexistente_retorna_none():
    cliente = MagicMock()
    cliente.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    assert carregar_grupo("Fantasma", cliente) is None


def test_carregar_grupo_erro_conexao_retorna_none():
    cliente = MagicMock()
    cliente.table.side_effect = Exception("connection refused")
    assert carregar_grupo("Equipe Alfa", cliente) is None


# --- listar_grupos ---


def test_listar_grupos():
    cliente = MagicMock()
    chain = cliente.table.return_value.select.return_value.order.return_value
    chain.execute.return_value.data = [{"nome": "Alfa"}, {"nome": "Bravo"}]

    assert listar_grupos(cliente) == ["Alfa", "Bravo"]
    cliente.table.assert_called_once_with("grupos")
    cliente.table.return_value.select.assert_called_once_with("nome")


def test_listar_grupos_erro_conexao_retorna_lista_vazia():
    cliente = MagicMock()
    cliente.table.side_effect = Exception("connection refused")
    assert listar_grupos(cliente) == []


# --- carregar_todos_grupos ---


def _cliente_todos(linhas_grupos, linhas_pessoas, linhas_suprimentos):
    """Client mockado para a carga em massa: um mock por tabela, com dados próprios."""
    tab_grupos = MagicMock()
    tab_grupos.select.return_value.order.return_value.execute.return_value.data = linhas_grupos
    tab_pessoas = MagicMock()
    tab_pessoas.select.return_value.execute.return_value.data = linhas_pessoas
    tab_suprimentos = MagicMock()
    tab_suprimentos.select.return_value.execute.return_value.data = linhas_suprimentos

    tabelas = {"grupos": tab_grupos, "pessoas": tab_pessoas, "suprimentos": tab_suprimentos}
    cliente = MagicMock()
    cliente.table.side_effect = tabelas.__getitem__
    return cliente


def test_carregar_todos_grupos_happy_path():
    cliente = _cliente_todos(
        linhas_grupos=[
            {
                "id": 1,
                "nome": "Alfa",
                "localizacao": "Kyiv",
                "regiao": "Norte",
                "pedido_ajuda": True,
            },
            {"id": 2, "nome": "Bravo", "localizacao": None, "regiao": "", "pedido_ajuda": False},
        ],
        linhas_pessoas=[
            {"id": 10, "grupo_id": 1, "nome": "Carlos", "idade": 40},
            {"id": 11, "grupo_id": 2, "nome": "Ana", "idade": 8},
        ],
        linhas_suprimentos=[
            {
                "id": 20,
                "grupo_id": 1,
                "nome": "Agua",
                "quantidade_atual": 20.0,
                "consumo_diario_padrao": 2.0,
                "unidade_medida": "L",
                "categoria": "agua",
                "validade": "2026-12-31",
            }
        ],
    )

    grupos = carregar_todos_grupos(cliente)

    assert [g.nome_grupo for g in grupos] == ["Alfa", "Bravo"]

    alfa, bravo = grupos
    assert alfa.localizacao == "Kyiv"
    assert alfa.regiao == "Norte"
    assert alfa.pedido_ajuda is True
    assert [p.nome for p in alfa.pessoas] == ["Carlos"]
    assert len(alfa.suprimentos) == 1
    assert alfa.suprimentos[0].nome == "Agua"
    assert alfa.suprimentos[0].validade == datetime.date(2026, 12, 31)

    # Filhos agrupados pelo grupo_id certo: Bravo fica com a Ana e sem suprimentos.
    assert [p.nome for p in bravo.pessoas] == ["Ana"]
    assert bravo.suprimentos == []


def test_carregar_todos_grupos_faz_3_queries():
    """A otimização: 3 queries no total (grupos/pessoas/suprimentos), não 1 + 3*N."""
    cliente = _cliente_todos(
        linhas_grupos=[
            {"id": 1, "nome": "Alfa", "localizacao": None, "regiao": "", "pedido_ajuda": False},
            {"id": 2, "nome": "Bravo", "localizacao": None, "regiao": "", "pedido_ajuda": False},
            {"id": 3, "nome": "Charlie", "localizacao": None, "regiao": "", "pedido_ajuda": False},
        ],
        linhas_pessoas=[],
        linhas_suprimentos=[],
    )

    carregar_todos_grupos(cliente)

    assert cliente.table.call_count == 3
    tabelas = [chamada.args[0] for chamada in cliente.table.call_args_list]
    assert tabelas == ["grupos", "pessoas", "suprimentos"]


def test_carregar_todos_grupos_grupo_sem_filhos_vem_com_listas_vazias():
    cliente = _cliente_todos(
        linhas_grupos=[
            {"id": 9, "nome": "Solo", "localizacao": None, "regiao": "", "pedido_ajuda": False}
        ],
        linhas_pessoas=[],
        linhas_suprimentos=[],
    )

    grupos = carregar_todos_grupos(cliente)

    assert len(grupos) == 1
    assert grupos[0].nome_grupo == "Solo"
    assert grupos[0].pessoas == []
    assert grupos[0].suprimentos == []


def test_carregar_todos_grupos_erro_conexao_retorna_lista_vazia():
    cliente = MagicMock()
    cliente.table.side_effect = Exception("connection refused")
    assert carregar_todos_grupos(cliente) == []
