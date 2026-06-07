import html
from pathlib import Path

# status cru (do relatorio / ResumoGrupo) -> classe CSS
_STATUS_CLASSE = {
    "OK": "ok",
    "ALERTA": "alerta",
    "CRITICO": "crit",  # chave SEM acento (só o label tem acento)
    "SEM_DADOS": "sem-dados",
    # Fase 4 (ainda não emitidos pelo código):
    "ESGOTADO": "esgotado",
    "VENCE_HOJE": "vence",
}


def classe_status(status: str) -> str:
    """Mapeia o status cru para a classe CSS; default gracioso pra status desconhecido."""
    return _STATUS_CLASSE.get(status, "ok")


def load_theme(nome: str = "theme.css") -> None:
    import streamlit as st

    css = (Path(__file__).parent / nome).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def linha(
    num: int,
    nome: str,
    tag: str,
    estado: str = "ok",
    sos: bool = False,
    href: str | None = None,
) -> str:
    # estado: "ok" | "alerta" | "crit" | "esgotado" | "vence" | "sem-dados"
    cls = "log-line" + ("" if estado == "ok" else f" {estado}")
    selo = '<span class="badge sos">SOS</span>' if sos else ""
    inner = (
        f'<div class="{cls}">'
        f'<span class="num">{num:02d}</span>'
        f'<span class="label">{html.escape(str(nome))}</span>'
        f'<span class="dots"></span>'
        f'<span class="tag">[{html.escape(str(tag))}]</span>{selo}</div>'
    )
    if href:
        return f'<a class="log-link" target="_self" href="{html.escape(href)}">{inner}</a>'
    return inner


def secao(titulo: str, linhas: list[str]) -> str:
    return (
        f'<div class="section"><div class="section-title">{html.escape(titulo)}</div>'
        + "".join(linhas)
        + "</div>"
    )


def info(label, valor, estado="ok"):
    cls = "log-line" + ("" if estado == "ok" else f" {estado}")
    return (
        f'<div class="{cls}">'
        f'<span class="label">{html.escape(str(label))}</span>'
        f'<span class="dots"></span>'
        f'<span class="tag">[{html.escape(str(valor))}]</span></div>'
    )
