"""Montagem dos dados do mapa do coordenador (lógica pura).

Converte os resumos de ``visao_coordenador`` em pontos lat/lon prontos
para ``st.map``, com a função de geocoding injetada como parâmetro —
mesmo padrão de injeção de dependência do ``http_client`` em ``clima.py``.
Sem Streamlit, sem rede direta: tudo testável com mock.
"""

from collections.abc import Callable

from racionador.coordenacao import ResumoGrupo

# Cores hex por status para o mapa (mesma semântica dos emojis da UI).
_COR_STATUS = {
    "CRITICO": "#d62728",
    "ALERTA": "#ff7f0e",
    "OK": "#2ca02c",
    "SEM_DADOS": "#7f7f7f",
}


def montar_dados_mapa(
    resumos: list[ResumoGrupo],
    geocode_fn: Callable[[str], tuple[float, float] | None],
) -> list[dict]:
    """Monta os pontos do mapa: um dict {nome, lat, lon, cor} por grupo localizável.

    Resumos sem ``localizacao`` são ignorados; cada cidade é geocodificada
    uma única vez (memoização local, além de qualquer cache externo); cidade
    que ``geocode_fn`` não resolve (None) é pulada. Lista vazia sinaliza à
    UI que não há mapa a renderizar (sem chave de API, offline etc.).
    """
    coords_por_cidade: dict[str, tuple[float, float] | None] = {}
    pontos: list[dict] = []

    for resumo in resumos:
        if not resumo.localizacao:
            continue
        if resumo.localizacao not in coords_por_cidade:
            coords_por_cidade[resumo.localizacao] = geocode_fn(resumo.localizacao)
        coords = coords_por_cidade[resumo.localizacao]
        if coords is None:
            continue
        pontos.append(
            {
                "nome": resumo.nome_grupo,
                "lat": coords[0],
                "lon": coords[1],
                "cor": _COR_STATUS[resumo.status],
            }
        )

    return pontos
