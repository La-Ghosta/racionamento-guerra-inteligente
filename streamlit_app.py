"""Camada web do Racionador-Supri em Streamlit."""

import datetime
import json
import os
from dataclasses import asdict
from urllib.parse import quote

import pandas as pd
import streamlit as st

from crt_ui import classe_status, info, linha, load_theme, secao
from racionador.clima import geocodificar, obter_clima
from racionador.coordenacao import visao_coordenador
from racionador.mapa import montar_dados_mapa
from racionador.modelos import Grupo, Pessoa, Suprimento
from racionador.persistencia_supabase import (
    carregar_grupo,
    carregar_todos_grupos,
    criar_cliente,
    deletar_grupo,
    listar_grupos,
    salvar_grupo,
)
from racionador.racionamento import relatorio_completo, sugerir_corte

# --- BLOCO 1: Page config (deve ser a primeira chamada Streamlit) ---
st.set_page_config(
    page_title="Racionador-Supri",
    page_icon="📦",
    layout="wide",
)
load_theme()

# --- BLOCO 2: Inject secrets a partir de st.secrets (se houver) ---
# st.secrets levanta StreamlitSecretNotFoundError quando nao existe
# .streamlit/secrets.toml local — capturamos para que o app rode
# tanto no Streamlit Cloud (com secrets configurados no painel) quanto
# localmente (lendo as env vars setadas manualmente no terminal).
try:
    for _secret in ("OPENWEATHER_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"):
        if _secret in st.secrets:
            os.environ[_secret] = st.secrets[_secret]
except FileNotFoundError:
    pass

# --- BLOCO 3: Session state e persistência Supabase ---
if "grupo" not in st.session_state:
    st.session_state.grupo = None


@st.cache_resource
def _obter_cliente_supabase():
    """Cria (uma única vez por processo) o client do Supabase.

    Retorna None quando as credenciais estão ausentes ou inválidas —
    nesse caso o app opera em modo offline, apenas com session_state.
    """
    return criar_cliente()


def _persistir(grupo: Grupo) -> None:
    """Salva o grupo no Supabase, se houver client; avisa em caso de falha."""
    client = _obter_cliente_supabase()
    if client is None:
        return
    if not salvar_grupo(grupo, client):
        st.warning("⚠️ Não foi possível salvar no banco — alterações mantidas apenas na sessão.")


# --- BLOCO 4: Funções auxiliares puras ---


def _grupo_para_json(grupo: Grupo) -> str:
    return json.dumps(asdict(grupo), ensure_ascii=False, indent=2, default=str)


def _json_para_grupo(data: dict) -> Grupo:
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
        pedido_ajuda=bool(data.get("pedido_ajuda", False)),
    )


def _grupo_exemplo() -> Grupo:
    grupo = Grupo(nome_grupo="Família Kyiv", localizacao="Kyiv")
    grupo.pessoas = [
        Pessoa(nome="Olena", idade=34),
        Pessoa(nome="Mykola", idade=8),
        Pessoa(nome="Maria", idade=67),
    ]
    grupo.suprimentos = [
        Suprimento(
            nome="Água",
            quantidade_atual=20,
            consumo_diario_padrao=2.0,
            unidade_medida="L",
            categoria="agua",
        ),
        Suprimento(
            nome="Arroz",
            quantidade_atual=5,
            consumo_diario_padrao=0.3,
            unidade_medida="kg",
            categoria="comida",
        ),
        Suprimento(
            nome="Medicamento",
            quantidade_atual=10,
            consumo_diario_padrao=1.0,
            unidade_medida="un",
            categoria="remedio",
        ),
    ]
    return grupo


# --- BLOCO 5: Sidebar ---


def _renderizar_sidebar() -> None:
    client = _obter_cliente_supabase()

    with st.sidebar:
        st.header("⚙️ Configurações")

        if client is not None:
            nomes_grupos = listar_grupos(client)
            if nomes_grupos:
                nome_sel = st.selectbox("Grupos no banco", nomes_grupos, key="sidebar_sel_grupo")
                if st.button("Carregar grupo", key="btn_carregar_grupo"):
                    grupo = carregar_grupo(nome_sel, client)
                    if grupo is not None:
                        st.session_state.grupo = grupo
                        st.rerun()
                    else:
                        st.error(f"Não foi possível carregar o grupo '{nome_sel}' do banco.")
            else:
                st.caption("Nenhum grupo no banco ainda.")

            novo_nome = st.text_input("Novo grupo", key="sidebar_nome_grupo")
            if st.button("Criar grupo", key="btn_criar_grupo") and novo_nome.strip():
                grupo = Grupo(nome_grupo=novo_nome.strip())
                _persistir(grupo)
                st.session_state.grupo = grupo
                st.rerun()
        else:
            st.warning("🔌 Banco indisponível — modo offline (dados só nesta sessão).")

            nome_atual = st.session_state.grupo.nome_grupo if st.session_state.grupo else ""
            label_btn = "Renomear grupo" if st.session_state.grupo else "Criar grupo"
            novo_nome = st.text_input("Nome do grupo", value=nome_atual, key="sidebar_nome_grupo")
            if st.button(label_btn, key="btn_criar_renomear") and novo_nome.strip():
                if st.session_state.grupo is None:
                    st.session_state.grupo = Grupo(nome_grupo=novo_nome.strip())
                else:
                    st.session_state.grupo.nome_grupo = novo_nome.strip()
                st.rerun()

        st.divider()

        loc_atual = (
            st.session_state.grupo.localizacao
            if st.session_state.grupo and st.session_state.grupo.localizacao
            else ""
        )
        nova_loc = st.text_input("Cidade (localização)", value=loc_atual, key="sidebar_localizacao")
        if (
            st.button("Definir localização", key="btn_definir_loc")
            and st.session_state.grupo
            and nova_loc.strip()
        ):
            st.session_state.grupo.localizacao = nova_loc.strip()
            _persistir(st.session_state.grupo)
            st.rerun()

        regiao_atual = st.session_state.grupo.regiao if st.session_state.grupo else ""
        nova_regiao = st.text_input(
            "Região (coordenação)", value=regiao_atual, key="sidebar_regiao"
        )
        if st.button("Definir região", key="btn_definir_regiao") and st.session_state.grupo:
            st.session_state.grupo.regiao = nova_regiao.strip()
            _persistir(st.session_state.grupo)
            st.rerun()

        if st.session_state.grupo:
            # Toggle dinâmico: a flag muda conforme a situação do grupo evolui,
            # então persiste imediatamente, sem botão de confirmação.
            pedido = st.toggle(
                "🆘 Pedido de ajuda",
                value=st.session_state.grupo.pedido_ajuda,
                key="sidebar_pedido_ajuda",
            )
            if pedido != st.session_state.grupo.pedido_ajuda:
                st.session_state.grupo.pedido_ajuda = pedido
                _persistir(st.session_state.grupo)
                st.rerun()

        st.divider()

        if st.session_state.grupo:
            json_str = _grupo_para_json(st.session_state.grupo)
            st.download_button(
                "⬇️ Baixar dados (JSON)",
                data=json_str,
                file_name="grupo.json",
                mime="application/json",
            )

        arquivo = st.file_uploader("⬆️ Carregar JSON", type=["json"], key="uploader_json")
        if arquivo is not None:
            try:
                data = json.loads(arquivo.read().decode("utf-8"))
                st.session_state.grupo = _json_para_grupo(data)
                _persistir(st.session_state.grupo)
                st.success("Grupo carregado com sucesso!")
                st.rerun()
            except (ValueError, KeyError) as e:
                st.error(f"Arquivo inválido: {e}")

        st.divider()

        st.markdown(
            "[📂 Repositório GitHub](https://github.com/La-Ghosta/racionamento-guerra-inteligente)"
        )
        st.markdown(
            "[🐛 Issues](https://github.com/La-Ghosta/racionamento-guerra-inteligente/issues)"
        )


# --- BLOCO 6: Aba Início ---


def _aba_inicio() -> None:
    st.header("📦 Racionador-Supri")
    st.markdown(
        "Ferramenta para grupos em **zonas de conflito humanitário** controlarem suprimentos "
        "básicos, prever quantos dias cada item vai durar e receber sugestões de corte no consumo."
    )

    if st.session_state.grupo is None:
        if st.button("📂 Carregar dados de exemplo"):
            st.session_state.grupo = _grupo_exemplo()
            _persistir(st.session_state.grupo)
            st.rerun()
    else:
        grupo = st.session_state.grupo
        col1, col2, col3 = st.columns(3)
        col1.metric("Grupo", grupo.nome_grupo)
        col2.metric("Pessoas", len(grupo.pessoas))
        col3.metric("Suprimentos", len(grupo.suprimentos))
        linhas_info = []
        if grupo.localizacao:
            linhas_info.append(info("LOCALIZAÇÃO", grupo.localizacao))
        linhas_info.append(info("REGIÃO", grupo.regiao or "NÃO DEFINIDA"))
        if grupo.pedido_ajuda:
            linhas_info.append(
                '<div class="log-line">'
                '<span class="label" style="color:var(--crit);text-shadow:0 0 6px var(--crit)">PEDIDO DE AJUDA</span>'
                '<span class="dots"></span>'
                '<span class="badge sos">SOS</span></div>'
            )
        else:
            linhas_info.append(info("PEDIDO DE AJUDA", "NÃO", estado="sem-dados"))
        st.markdown('<div class="crt">' + "".join(linhas_info) + "</div>", unsafe_allow_html=True)
        if st.button("🔄 Recarregar dados de exemplo"):
            st.session_state.grupo = _grupo_exemplo()
            _persistir(st.session_state.grupo)
            st.rerun()
        if st.button("Deletar grupo", key="btn_deletar_grupo"):
            client = _obter_cliente_supabase()
            if client is not None:
                deletar_grupo(grupo.nome_grupo, client)
            st.session_state.grupo = None
            st.rerun()


# --- BLOCO 7: Aba Pessoas ---


def _aba_pessoas() -> None:
    if st.session_state.grupo is None:
        st.info("Crie um grupo na barra lateral para começar.")
        return

    grupo = st.session_state.grupo

    st.subheader("Adicionar pessoa")
    with st.form("form_add_pessoa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome")
        idade = col2.number_input("Idade", min_value=0, max_value=120, step=1, value=30)
        submitted = st.form_submit_button("Adicionar")
        if submitted:
            if nome.strip():
                try:
                    pessoa = Pessoa(nome=nome.strip(), idade=int(idade))
                    grupo.pessoas.append(pessoa)
                    _persistir(grupo)
                    st.success(
                        f"'{pessoa.nome}' adicionada (fator de consumo: {pessoa.fator_consumo:.1f})"
                    )
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            else:
                st.error("Informe um nome para a pessoa.")

    st.subheader("Pessoas no grupo")
    if not grupo.pessoas:
        st.caption("Nenhuma pessoa cadastrada.")
    else:
        for i, pessoa in enumerate(grupo.pessoas):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(pessoa.nome)
            col2.write(f"{pessoa.idade} anos")
            col3.write(f"fator {pessoa.fator_consumo:.1f}")
            if col4.button("Remover", key=f"remover_pessoa_{i}"):
                grupo.pessoas.pop(i)
                _persistir(grupo)
                st.rerun()


# --- BLOCO 8: Aba Suprimentos ---


def _aba_suprimentos() -> None:
    if st.session_state.grupo is None:
        st.info("Crie um grupo na barra lateral para começar.")
        return

    grupo = st.session_state.grupo

    st.subheader("Adicionar suprimento")
    with st.form("form_add_suprimento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome")
        unidade = col2.text_input("Unidade (ex: L, kg, un)")
        col3, col4 = st.columns(2)
        quantidade = col3.number_input("Quantidade atual", min_value=0.0, step=0.1, value=0.0)
        consumo = col4.number_input("Consumo diário por adulto", min_value=0.0, step=0.1, value=0.0)
        col5, col6 = st.columns(2)
        categoria = col5.text_input("Categoria (opcional)", value="outro")
        validade = col6.date_input("Validade (opcional)", value=None)
        submitted = st.form_submit_button("Adicionar")
        if submitted:
            if nome.strip() and unidade.strip():
                try:
                    sup = Suprimento(
                        nome=nome.strip(),
                        quantidade_atual=quantidade,
                        consumo_diario_padrao=consumo,
                        unidade_medida=unidade.strip(),
                        categoria=categoria.strip() or "outro",
                        validade=validade,
                    )
                    grupo.suprimentos.append(sup)
                    _persistir(grupo)
                    st.success(f"'{sup.nome}' adicionado.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            else:
                st.error("Informe nome e unidade do suprimento.")

    st.subheader("Suprimentos no grupo")
    if not grupo.suprimentos:
        st.caption("Nenhum suprimento cadastrado.")
    else:
        for i, sup in enumerate(grupo.suprimentos):
            with st.expander(f"{sup.nome} — {sup.quantidade_atual} {sup.unidade_medida}"):
                detalhes = f"Categoria: {sup.categoria}"
                if sup.validade:
                    detalhes += f" · Validade: {sup.validade.isoformat()}"
                st.caption(detalhes)
                nova_qtd = st.number_input(
                    f"Nova quantidade ({sup.unidade_medida})",
                    value=float(sup.quantidade_atual),
                    min_value=0.0,
                    step=0.1,
                    key=f"qtd_{i}",
                )
                col1, col2 = st.columns(2)
                if col1.button("Atualizar quantidade", key=f"atualizar_{i}"):
                    sup.quantidade_atual = nova_qtd
                    _persistir(grupo)
                    st.success(
                        f"Quantidade de '{sup.nome}' atualizada para {nova_qtd} {sup.unidade_medida}."
                    )
                    st.rerun()
                if col2.button("Remover suprimento", key=f"remover_sup_{i}"):
                    grupo.suprimentos.pop(i)
                    _persistir(grupo)
                    st.rerun()


# --- BLOCO 9: Aba Status ---

_STATUS_LABEL = {"OK": "OK", "ALERTA": "ALERTA", "CRITICO": "CRÍTICO", "SEM_DADOS": "SEM DADOS"}


def _aba_status() -> None:
    if st.session_state.grupo is None:
        st.info("Crie um grupo na barra lateral para começar.")
        return

    grupo = st.session_state.grupo

    try:
        relatorio = relatorio_completo(grupo)
    except ValueError as e:
        st.error(str(e))
        return

    linhas_log = []
    for i, (nome_sup, dados) in enumerate(relatorio.items(), start=1):
        dias = dados["dias_restantes"]
        dias_str = str(int(dias)) if dias != float("inf") else "∞"
        if dias_str == "∞":
            tag = "∞"
        else:
            tag = f"{dias_str} DIA" if dias_str == "1" else f"{dias_str} DIAS"
        linhas_log.append(linha(i, nome_sup, tag, estado=classe_status(dados["status"])))

    if not linhas_log:
        linhas_log = [linha(1, "SEM SUPRIMENTOS", "—", estado="sem-dados")]

    html = '<div class="crt">' + secao("ESTOQUE", linhas_log) + "</div>"
    st.markdown(html, unsafe_allow_html=True)

    if grupo.localizacao:
        with st.spinner(f"Consultando clima em {grupo.localizacao}…"):
            dados_clima = obter_clima(grupo.localizacao)

        if dados_clima:
            st.subheader(f"🌡️ Clima em {dados_clima['cidade']}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Cidade", dados_clima["cidade"])
            col2.metric("Temperatura", f"{dados_clima['temperatura_c']}°C")
            col3.metric("Descrição", str(dados_clima["descricao"]).capitalize())
            col4.metric("Umidade", f"{dados_clima['umidade']}%")
        else:
            st.caption("🌐 Dados climáticos indisponíveis no momento.")


# --- BLOCO 10: Aba Sugestões ---


def _aba_sugestoes() -> None:
    if st.session_state.grupo is None:
        st.info("Crie um grupo na barra lateral para começar.")
        return

    grupo = st.session_state.grupo

    if not grupo.suprimentos:
        st.info("Adicione suprimentos para calcular sugestões de corte.")
        return

    nomes = [s.nome for s in grupo.suprimentos]
    nome_sel = st.selectbox("Suprimento", nomes)
    dias_alvo = st.number_input("Dias-alvo", min_value=1, step=1, value=10)

    if st.button("Calcular corte sugerido"):
        sup = next(s for s in grupo.suprimentos if s.nome == nome_sel)
        try:
            corte = sugerir_corte(sup, grupo, int(dias_alvo))
            if corte == 0.0:
                st.success(
                    f"✅ '{nome_sel}' já dura {dias_alvo} dias ou mais. Nenhum corte necessário."
                )
            else:
                st.warning(
                    f"✂️ Para **'{nome_sel}'** durar **{dias_alvo} dias**, "
                    f"reduza o consumo em **{corte:.1f}%**."
                )
        except ValueError as e:
            st.error(str(e))


# --- BLOCO 11: Aba Coordenação ---


@st.cache_data(ttl=86400, show_spinner=False)
def _geocodificar_ok(cidade: str) -> tuple[float, float]:
    """Geocodifica e cacheia SÓ o sucesso.

    Em falha levanta LookupError. O st.cache_data não cacheia exceções, então uma
    falha transitória (timeout, 429, rede no deploy) é re-tentada no próximo render,
    em vez de ficar presa como None por 1h num processo de nuvem de vida longa.
    Coordenada de cidade não muda — o sucesso pode ser cacheado por 24h, resolve a pica.
    """
    coords = geocodificar(cidade)
    if coords is None:
        raise LookupError(cidade)
    return coords


def _geocodificar_para_mapa(cidade: str) -> tuple[float, float] | None:
    """Adapta _geocodificar_ok ao contrato de montar_dados_mapa (None = pular)."""
    try:
        return _geocodificar_ok(cidade)
    except LookupError:
        return None


def _aba_coordenacao() -> None:
    client = _obter_cliente_supabase()
    if client is None:
        st.warning("🔌 Banco indisponível — a visão de coordenador precisa do Supabase.")
        return

    grupos = carregar_todos_grupos(client)
    if not grupos:
        st.info("Nenhum grupo no banco ainda.")
        return

    visao = visao_coordenador(grupos)

    st.header("🗺️ Visão do coordenador")
    st.caption(f"{len(grupos)} grupo(s) no banco, agrupados por região e ordenados por urgência.")

    blocos = []
    for regiao, resumos in visao.por_regiao.items():
        linhas_grp = [
            linha(
                i,
                r.nome_grupo,
                _STATUS_LABEL.get(r.status, r.status),
                estado=classe_status(r.status),
                sos=r.pedido_ajuda,
                href=f"?grupo={quote(r.nome_grupo)}",
            )
            for i, r in enumerate(resumos, start=1)
        ]
        blocos.append(secao((regiao or "SEM REGIÃO").upper(), linhas_grp))
    st.markdown('<div class="crt">' + "".join(blocos) + "</div>", unsafe_allow_html=True)

    st.divider()

    dados_mapa = montar_dados_mapa(visao.resumos, _geocodificar_para_mapa)
    if dados_mapa:
        df_mapa = pd.DataFrame(dados_mapa)
        st.markdown(
            '<div class="crt"><div class="section-title" '
            'style="position:static;display:inline-block;margin-bottom:.4rem">'
            "LIVE MAP [GPS]</div></div>",
            unsafe_allow_html=True,
        )
        st.map(df_mapa, latitude="lat", longitude="lon", color="cor")
    else:
        st.caption(
            "🌐 Mapa indisponível (sem chave de API, offline ou nenhuma cidade geocodificada)."
        )

    # Nunca deixar um grupo com cidade sumir do mapa em silêncio: um crítico em SOS
    # que some daqui é perigoso pro coordenador. Lista os que têm localização mas
    # não viraram ponto (cidade não resolvida nesta tentativa).
    nomes_no_mapa = {p["nome"] for p in dados_mapa}
    nao_localizados = [
        r for r in visao.resumos if r.localizacao and r.nome_grupo not in nomes_no_mapa
    ]
    if nao_localizados:
        st.caption(
            "⚠️ Sem ponto no mapa (cidade não geocodificada nesta tentativa): "
            + ", ".join(f"{r.nome_grupo} ({r.localizacao})" for r in nao_localizados)
        )


# --- BLOCO 12: Main ---


def main() -> None:
    client = _obter_cliente_supabase()

    grupo_q = st.query_params.get("grupo")
    if grupo_q:
        g = None
        if client is not None:
            try:
                g = carregar_grupo(grupo_q, client)
            except Exception:
                g = None
        if g is not None:
            st.session_state.grupo = g
            st.session_state["aba_ativa"] = "📊 Status"
        del st.query_params["grupo"]
        st.rerun()

    _renderizar_sidebar()

    aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
        ["🏠 Início", "👥 Pessoas", "📦 Suprimentos", "📊 Status", "✂️ Sugestões", "🗺️ Coordenação"],
        key="aba_ativa",
        on_change="rerun",
    )

    with aba1:
        _aba_inicio()
    with aba2:
        _aba_pessoas()
    with aba3:
        _aba_suprimentos()
    with aba4:
        if aba4.open:
            _aba_status()
    with aba5:
        _aba_sugestoes()
    with aba6:
        if aba6.open:
            _aba_coordenacao()


if __name__ == "__main__":
    main()
