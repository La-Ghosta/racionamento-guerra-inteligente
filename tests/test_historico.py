"""Testes da lógica pura de preparo do histórico (sem banco)."""

import datetime

from racionador.historico import preparar_historico


def _linha(criado_em, suprimento="Agua", quantidade=10.0, tipo="atualizacao"):
    return {
        "criado_em": criado_em,
        "suprimento": suprimento,
        "quantidade": quantidade,
        "tipo": tipo,
    }


def test_preparar_historico_ordena_por_data():
    linhas = [
        _linha("2026-06-03T10:00:00+00:00", quantidade=15.0),
        _linha("2026-06-01T10:00:00+00:00", quantidade=20.0),
        _linha("2026-06-02T10:00:00+00:00", quantidade=18.0),
    ]
    registros = preparar_historico(linhas)
    assert [r["quantidade"] for r in registros] == [20.0, 18.0, 15.0]
    assert registros[0]["quando"] == datetime.datetime(
        2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc
    )


def test_preparar_historico_aceita_sufixo_z():
    registros = preparar_historico([_linha("2026-06-01T10:00:00Z")])
    assert len(registros) == 1
    assert registros[0]["quando"] == datetime.datetime(
        2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc
    )


def test_linha_com_criado_em_invalido_e_pulada():
    linhas = [_linha("isso-nao-e-data"), _linha(None), _linha("2026-06-01T10:00:00+00:00")]
    registros = preparar_historico(linhas)
    assert len(registros) == 1


def test_linha_com_quantidade_invalida_e_pulada():
    linhas = [
        _linha("2026-06-01T10:00:00+00:00", quantidade="vinte"),
        _linha("2026-06-02T10:00:00+00:00", quantidade=5.0),
    ]
    registros = preparar_historico(linhas)
    assert len(registros) == 1
    assert registros[0]["quantidade"] == 5.0


def test_lista_vazia_retorna_lista_vazia():
    assert preparar_historico([]) == []
