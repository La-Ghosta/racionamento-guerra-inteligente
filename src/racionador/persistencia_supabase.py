"""Persistência do estado do grupo no Supabase (PostgreSQL em nuvem).

Espelha a interface de ``persistencia.py`` (JSON), trocando o caminho de
arquivo por um client do supabase-py injetado como parâmetro — mesmo padrão
de injeção de dependência do ``http_client`` em ``clima.py``. Todas as
funções degradam graciosamente em erro de conexão/API: nunca derrubam o app.
"""

import datetime
import os
from dataclasses import asdict
from typing import Any

from racionador.modelos import Grupo, Pessoa, Suprimento


def criar_cliente() -> Any | None:
    """Cria um client supabase a partir de SUPABASE_URL/SUPABASE_SERVICE_KEY.

    Retorna None se as variáveis de ambiente estiverem ausentes ou se a
    criação do client falhar (pacote indisponível, URL inválida etc.).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None

    try:
        # Import tardio: a CLI (offline-first) não exige o pacote supabase.
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def salvar_grupo(grupo: Grupo, client: Any) -> bool:
    """Salva um Grupo no banco: upsert do grupo + substituição de pessoas/suprimentos.

    Retorna True em sucesso e False em qualquer falha de conexão/API.
    """
    try:
        resultado = (
            client.table("grupos")
            .upsert(
                {
                    "nome": grupo.nome_grupo,
                    "localizacao": grupo.localizacao,
                    "regiao": grupo.regiao,
                    "pedido_ajuda": grupo.pedido_ajuda,
                },
                on_conflict="nome",
            )
            .execute()
        )
        grupo_id = resultado.data[0]["id"]

        client.table("pessoas").delete().eq("grupo_id", grupo_id).execute()
        client.table("suprimentos").delete().eq("grupo_id", grupo_id).execute()

        if grupo.pessoas:
            linhas_pessoas = [
                {"grupo_id": grupo_id, "nome": p.nome, "idade": p.idade} for p in grupo.pessoas
            ]
            client.table("pessoas").insert(linhas_pessoas).execute()

        if grupo.suprimentos:
            linhas_suprimentos = []
            for s in grupo.suprimentos:
                linha = {"grupo_id": grupo_id, **asdict(s)}
                linha["validade"] = s.validade.isoformat() if s.validade else None
                linhas_suprimentos.append(linha)
            client.table("suprimentos").insert(linhas_suprimentos).execute()

        return True
    except Exception:
        return False


def carregar_grupo(nome: str, client: Any) -> Grupo | None:
    """Busca um Grupo pelo nome e reconstrói o dataclass com pessoas/suprimentos.

    Retorna None se o grupo não existir ou em qualquer falha de conexão/API.
    """
    try:
        resultado = client.table("grupos").select("*").eq("nome", nome).execute()
        if not resultado.data:
            return None
        linha_grupo = resultado.data[0]
        grupo_id = linha_grupo["id"]

        linhas_pessoas = client.table("pessoas").select("*").eq("grupo_id", grupo_id).execute().data
        linhas_suprimentos = (
            client.table("suprimentos").select("*").eq("grupo_id", grupo_id).execute().data
        )

        pessoas = [Pessoa(nome=p["nome"], idade=p["idade"]) for p in linhas_pessoas]
        suprimentos = []
        for s in linhas_suprimentos:
            campos = {k: v for k, v in s.items() if k not in ("id", "grupo_id")}
            if campos.get("validade"):
                campos["validade"] = datetime.date.fromisoformat(campos["validade"])
            suprimentos.append(Suprimento(**campos))

        return Grupo(
            nome_grupo=linha_grupo["nome"],
            pessoas=pessoas,
            suprimentos=suprimentos,
            localizacao=linha_grupo.get("localizacao"),
            # Defaults seguros: coluna nula ou ausente vira "" / False.
            regiao=linha_grupo.get("regiao") or "",
            pedido_ajuda=bool(linha_grupo.get("pedido_ajuda")),
        )
    except Exception:
        return None


def deletar_grupo(nome: str, client: Any) -> bool:
    """Apaga um grupo pelo nome; FK ON DELETE CASCADE remove pessoas/suprimentos.

    Retorna True em sucesso e False em qualquer falha de conexão.
    """
    try:
        # Corrigido o ponto antes do delete()
        client.table("grupos").delete().eq("nome", nome).execute()
        return True
    except Exception:  # Corrigido o 'execept'
        return False


def listar_grupos(client: Any) -> list[str]:
    """Lista os nomes dos grupos cadastrados, em ordem alfabética.

    Retorna a lista de nomes em sucesso e uma lista vazia em qualquer falha da conexão/API.
    """
    try:
        # Busca apenas a coluna 'nome' e ordena de forma ascendente (alfabética)
        resposta = client.table("grupos").select("nome").order("nome").execute()
        # Extrai os nomes do resultado da API
        nomes = [registro["nome"] for registro in resposta.data]
        return nomes
    except Exception:
        return []


def carregar_todos_grupos(client: Any) -> list[Grupo]:
    """Carrega todos os grupos em 3 queries (grupos, pessoas, suprimentos).

    Junta os filhos em memória por grupo_id, evitando o N+1 de chamar
    carregar_grupo uma vez por grupo (que fazia 1 + 3*N idas ao banco).
    Mantém a ordem alfabética por nome. Retorna lista vazia em qualquer
    falha de conexão/API.
    """
    try:
        linhas_grupos = client.table("grupos").select("*").order("nome").execute().data
        if not linhas_grupos:
            return []

        linhas_pessoas = client.table("pessoas").select("*").execute().data
        linhas_suprimentos = client.table("suprimentos").select("*").execute().data

        # Indexa os filhos por grupo_id para montar cada grupo sem novas queries.
        pessoas_por_grupo: dict[Any, list[dict]] = {}
        for p in linhas_pessoas:
            pessoas_por_grupo.setdefault(p["grupo_id"], []).append(p)

        suprimentos_por_grupo: dict[Any, list[dict]] = {}
        for s in linhas_suprimentos:
            suprimentos_por_grupo.setdefault(s["grupo_id"], []).append(s)

        grupos = []
        for linha_grupo in linhas_grupos:
            grupo_id = linha_grupo["id"]

            pessoas = [
                Pessoa(nome=p["nome"], idade=p["idade"])
                for p in pessoas_por_grupo.get(grupo_id, [])
            ]

            suprimentos = []
            for s in suprimentos_por_grupo.get(grupo_id, []):
                campos = {k: v for k, v in s.items() if k not in ("id", "grupo_id")}
                if campos.get("validade"):
                    campos["validade"] = datetime.date.fromisoformat(campos["validade"])
                suprimentos.append(Suprimento(**campos))

            grupos.append(
                Grupo(
                    nome_grupo=linha_grupo["nome"],
                    pessoas=pessoas,
                    suprimentos=suprimentos,
                    localizacao=linha_grupo.get("localizacao"),
                    # Defaults seguros: coluna nula ou ausente vira "" / False.
                    regiao=linha_grupo.get("regiao") or "",
                    pedido_ajuda=bool(linha_grupo.get("pedido_ajuda")),
                )
            )
        return grupos
    except Exception:
        return []
