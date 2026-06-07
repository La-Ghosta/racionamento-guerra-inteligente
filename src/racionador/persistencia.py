"""Funções para persistência do estado do grupo em JSON."""

import datetime
import json
from dataclasses import asdict
from pathlib import Path

from racionador.modelos import Grupo, Pessoa, Suprimento


def salvar_grupo(grupo: Grupo, caminho: str | Path) -> None:
    """Serializa um Grupo em JSON no caminho indicado."""
    Path(caminho).write_text(
        json.dumps(asdict(grupo), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def carregar_grupo(caminho: str | Path) -> Grupo | None:
    """Desserializa um Grupo de JSON. Retorna None se o arquivo não existir."""
    p = Path(caminho)
    if not p.exists():
        return None

    data = json.loads(p.read_text(encoding="utf-8"))
    pessoas = [Pessoa(**d) for d in data["pessoas"]]
    for d in data["suprimentos"]:
        if d.get("validade"):
            d["validade"] = datetime.date.fromisoformat(d["validade"])
    suprimentos = [Suprimento(**d) for d in data["suprimentos"]]
    return Grupo(
        nome_grupo=data["nome_grupo"],
        pessoas=pessoas,
        suprimentos=suprimentos,
        localizacao=data.get("localizacao"),
        regiao=data.get("regiao", ""),
        pedido_ajuda=data.get("pedido_ajuda", False),
    )
