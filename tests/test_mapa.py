"""Testes da montagem dos dados do mapa (geocode mockado, sem rede)."""

from unittest.mock import Mock

from racionador.coordenacao import ResumoGrupo
from racionador.mapa import montar_dados_mapa


def _resumo(
    nome: str,
    status: str = "OK",
    localizacao: str | None = None,
) -> ResumoGrupo:
    return ResumoGrupo(
        nome_grupo=nome,
        status=status,
        pedido_ajuda=False,
        localizacao=localizacao,
        regiao="",
        total_pessoas=1,
        suprimentos_criticos=[],
    )


def test_monta_pontos_com_lat_lon_e_cor_por_status():
    resumos = [
        _resumo("Critico", status="CRITICO", localizacao="Kyiv"),
        _resumo("Tranquilo", status="OK", localizacao="Lviv"),
    ]
    coords = {"Kyiv": (50.45, 30.52), "Lviv": (49.84, 24.03)}

    pontos = montar_dados_mapa(resumos, coords.get)

    assert pontos == [
        {"nome": "Critico", "lat": 50.45, "lon": 30.52, "cor": "#d62728"},
        {"nome": "Tranquilo", "lat": 49.84, "lon": 24.03, "cor": "#2ca02c"},
    ]


def test_resumo_sem_localizacao_e_pulado_sem_chamar_geocode():
    geocode = Mock(return_value=(50.45, 30.52))
    resumos = [
        _resumo("Sem cidade", localizacao=None),
        _resumo("Com cidade", localizacao="Kyiv"),
    ]

    pontos = montar_dados_mapa(resumos, geocode)

    assert [p["nome"] for p in pontos] == ["Com cidade"]
    geocode.assert_called_once_with("Kyiv")


def test_geocode_que_falha_pula_o_grupo_e_tudo_falhando_da_lista_vazia():
    resumos = [
        _resumo("A", localizacao="Cidade Inexistente"),
        _resumo("B", localizacao="Outra Inexistente"),
    ]

    # Geocode sempre falha (sem chave de API / offline / cidade desconhecida).
    assert montar_dados_mapa(resumos, lambda _cidade: None) == []


def test_cidades_repetidas_geocodificam_uma_vez_so():
    geocode = Mock(return_value=(50.45, 30.52))
    resumos = [
        _resumo("Grupo 1", localizacao="Kyiv"),
        _resumo("Grupo 2", localizacao="Kyiv"),
        _resumo("Grupo 3", localizacao="Kyiv"),
    ]

    pontos = montar_dados_mapa(resumos, geocode)

    assert len(pontos) == 3
    geocode.assert_called_once_with("Kyiv")


def test_lista_vazia_retorna_lista_vazia():
    geocode = Mock()

    assert montar_dados_mapa([], geocode) == []
    geocode.assert_not_called()
