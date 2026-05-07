"""Camada web do Racionador-Supri em Streamlit."""

import json
import os
from dataclasses import asdict

import pandas as pd
import streamlit as st

from racionador.clima import obter_clima
from racionador.modelos import Grupo, Pessoa, Suprimento
from racionador.racionamento import relatorio_completo, sugerir_corte

# --- BLOCO 1: Page config (deve ser a primeira chamada Streamlit) ---
st.set_page_config(
    page_title="Racionador-Supri",
    page_icon="📦",
    layout="wide",
)

# --- BLOCO 2: Inject API key a partir de st.secrets (se houver) ---
# st.secrets levanta StreamlitSecretNotFoundError quando nao existe
# .streamlit/secrets.toml local — capturamos para que o app rode
# tanto no Streamlit Cloud (com secret configurado no painel) quanto
# localmente (lendo a env var setada manualmente no terminal).
try:
    if "OPENWEATHER_API_KEY" in st.secrets:
        os.environ["OPENWEATHER_API_KEY"] = st.secrets["OPENWEATHER_API_KEY"]
except FileNotFoundError:
    pass

# --- BLOCO 3: Session state ---
if "grupo" not in st.session_state:
    st.session_state.grupo = None


# --- BLOCO 4: Funções auxiliares puras ---


def _grupo_para_json(grupo: Grupo) -> str:
    return json.dumps(asdict(grupo), ensure_ascii=False, indent=2)


def _json_para_grupo(data: dict) -> Grupo:
    pessoas = [Pessoa(**d) for d in data["pessoas"]]
    suprimentos = [Suprimento(**d) for d in data["suprimentos"]]
    return Grupo(
        nome_grupo=data["nome_grupo"],
        pessoas=pessoas,
        suprimentos=suprimentos,
        localizacao=data.get("localizacao"),
    )


def _grupo_exemplo() -> Grupo:
    grupo = Grupo(nome_grupo="Família Kyiv", localizacao="Kyiv")
    grupo.pessoas = [
        Pessoa(nome="Olena", idade=34),
        Pessoa(nome="Mykola", idade=8),
        Pessoa(nome="Maria", idade=67),
    ]
    grupo.suprimentos = [
        Suprimento(nome="Água", quantidade_atual=20, consumo_diario_padrao=2.0, unidade_medida="L"),
        Suprimento(
            nome="Arroz", quantidade_atual=5, consumo_diario_padrao=0.3, unidade_medida="kg"
        ),
        Suprimento(
            nome="Medicamento", quantidade_atual=10, consumo_diario_padrao=1.0, unidade_medida="un"
        ),
    ]
    return grupo


# --- BLOCO 5: Sidebar ---


def _renderizar_sidebar() -> None:
    with st.sidebar:
        st.header("⚙️ Configurações")

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
                st.success("Grupo carregado com sucesso!")
                st.rerun()
            except (ValueError, KeyError) as e:
                st.error(f"Arquivo inválido: {e}")

        st.divider()

        st.markdown("[📂 Repositório GitHub](https://github.com/La-Ghosta/racionador-supri)")
        st.markdown("[🐛 Issue #1](https://github.com/La-Ghosta/racionador-supri/issues/1)")


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
            st.rerun()
    else:
        grupo = st.session_state.grupo
        col1, col2, col3 = st.columns(3)
        col1.metric("Grupo", grupo.nome_grupo)
        col2.metric("Pessoas", len(grupo.pessoas))
        col3.metric("Suprimentos", len(grupo.suprimentos))
        if grupo.localizacao:
            st.caption(f"📍 Localização: {grupo.localizacao}")
        if st.button("🔄 Recarregar dados de exemplo"):
            st.session_state.grupo = _grupo_exemplo()
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
        submitted = st.form_submit_button("Adicionar")
        if submitted:
            if nome.strip() and unidade.strip():
                try:
                    sup = Suprimento(
                        nome=nome.strip(),
                        quantidade_atual=quantidade,
                        consumo_diario_padrao=consumo,
                        unidade_medida=unidade.strip(),
                    )
                    grupo.suprimentos.append(sup)
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
                    st.success(
                        f"Quantidade de '{sup.nome}' atualizada para {nova_qtd} {sup.unidade_medida}."
                    )
                    st.rerun()
                if col2.button("Remover suprimento", key=f"remover_sup_{i}"):
                    grupo.suprimentos.pop(i)
                    st.rerun()


# --- BLOCO 9: Aba Status ---

_STATUS_EMOJI = {"OK": "🟢", "ALERTA": "🟡", "CRITICO": "🔴"}
_STATUS_LABEL = {"OK": "OK", "ALERTA": "ALERTA", "CRITICO": "CRÍTICO"}


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

    linhas = []
    for nome_sup, dados in relatorio.items():
        emoji = _STATUS_EMOJI[dados["status"]]
        label = _STATUS_LABEL[dados["status"]]
        dias = dados["dias_restantes"]
        dias_str = str(int(dias)) if dias != float("inf") else "∞"
        corte = dados["corte_sugerido_pct"]
        linhas.append(
            {
                "Suprimento": nome_sup,
                "Quantidade": f"{dados['quantidade_atual']} {dados['unidade_medida']}",
                "Dias restantes": dias_str,
                "Status": f"{emoji} {label}",
                "Corte sugerido": f"{corte:.1f}%" if corte > 0 else "—",
            }
        )

    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

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


# --- BLOCO 11: Main ---


def main() -> None:
    _renderizar_sidebar()

    aba1, aba2, aba3, aba4, aba5 = st.tabs(
        ["🏠 Início", "👥 Pessoas", "📦 Suprimentos", "📊 Status", "✂️ Sugestões"]
    )

    with aba1:
        _aba_inicio()
    with aba2:
        _aba_pessoas()
    with aba3:
        _aba_suprimentos()
    with aba4:
        _aba_status()
    with aba5:
        _aba_sugestoes()


if __name__ == "__main__":
    main()
