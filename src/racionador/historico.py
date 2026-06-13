"""Preparo das séries do histórico de suprimentos (lógica pura).

Converte as linhas cruas da tabela ``historico`` (vindas de
``persistencia_supabase.carregar_historico``) em registros prontos para
gráfico/tabela na UI. Sem Streamlit, sem rede: tudo testável sem mock.

Robusto a dados sujos: linha sem ``criado_em`` válido ou com ``quantidade``
não numérica é simplesmente pulada, nunca levanta.
"""

import datetime


def preparar_historico(linhas: list[dict]) -> list[dict]:
    """Converte linhas cruas do banco em registros prontos para gráfico/tabela.

    Cada registro: {"quando": datetime, "suprimento": str, "quantidade": float,
    "tipo": str}, ordenado por "quando". O ``criado_em`` chega como string ISO
    8601 com timezone; o fromisoformat do Python 3.10 não aceita o sufixo "Z",
    então normalizamos para "+00:00" antes de converter.
    """
    registros = []
    for linha_crua in linhas:
        criado_em = linha_crua.get("criado_em")
        if not criado_em:
            continue
        try:
            quando = datetime.datetime.fromisoformat(str(criado_em).replace("Z", "+00:00"))
            quantidade = float(linha_crua["quantidade"])
        except (ValueError, TypeError, KeyError):
            continue
        registros.append(
            {
                "quando": quando,
                "suprimento": linha_crua.get("suprimento", ""),
                "quantidade": quantidade,
                "tipo": linha_crua.get("tipo", ""),
            }
        )
    return sorted(registros, key=lambda r: r["quando"])
