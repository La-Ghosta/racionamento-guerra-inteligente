# Racionamento em Guerra Inteligente

[![CI](https://github.com/La-Ghosta/racionamento-guerra-inteligente/actions/workflows/ci.yml/badge.svg)](https://github.com/La-Ghosta/racionamento-guerra-inteligente/actions/workflows/ci.yml) ![Versao](https://img.shields.io/badge/versao-2.0.0-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Licenca](https://img.shields.io/badge/licenca-MIT-green)

Ferramenta para **famílias e grupos isolados em zonas de conflito humanitário** controlarem seus suprimentos essenciais — água, comida e remédios —, preverem por quantos dias cada item ainda dura e receberem sugestões de corte no consumo. Feita para continuar útil mesmo com pouca ou nenhuma conexão.

## App ao vivo

### → https://racionamento-guerra-inteligente.streamlit.app/

Roda direto no navegador, sem instalar nada.

## O que dá para fazer

- **Controlar o estoque** de cada grupo: pessoas, suprimentos e consumo.
- **Prever a autonomia** de cada item (quantos dias dura no ritmo atual), do status `OK` ao `CRÍTICO`.
- **Receber sugestões de racionamento** para esticar os recursos.
- **Visão de coordenador** sobre vários grupos ao mesmo tempo, agrupados por região: quem está crítico, quem pediu ajuda (`SOS`) e um mapa ao vivo.
- **Clicar num grupo** na visão do coordenador e cair direto no status detalhado dele.

A interface é um **terminal CRT** — estética de log de operações, monocromática e de leitura rápida, pensada para registro em campo.

## Como funciona por dentro

- **Offline-first**: o núcleo funciona sem internet, com dados locais. A visão de coordenador e o mapa usam a nuvem e degradam de forma graciosa quando ela não está disponível.
- **Nuvem** via Supabase (PostgreSQL) para a visão multi-grupo; **mapa** com geolocalização das cidades dos grupos.

## Stack

Python · Typer + Rich (CLI) · Streamlit (web) · Supabase / PostgreSQL · OpenWeather (clima e geocoding) · pytest + ruff · GitHub Actions (CI em 3.10 / 3.11 / 3.12) · Streamlit Community Cloud (deploy).

## Autores

| Integrante       |
|------------------|
| Guilherme Holanda |
| Murilo Yuki      |
| Carlos Eduardo   |
| Luan Ayres       |

Projeto da Etapa 3 — bootcamp II

## Repositório

https://github.com/La-Ghosta/racionamento-guerra-inteligente

## Como usar

A forma mais simples é pelo **app ao vivo** (link acima) — não precisa instalar nada.

### Rodar localmente

Requer **Python 3.10+** e Git.

```bash
# 1. Clonar o repositório
git clone https://github.com/La-Ghosta/racionamento-guerra-inteligente.git
cd racionamento-guerra-inteligente

# 2. Criar e ativar um ambiente virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Rodar o app
streamlit run streamlit_app.py
```

O app abre no navegador. Sem configuração extra ele roda em **modo offline** (o núcleo funciona sem nuvem). Para habilitar a visão de coordenador e o mapa, crie um arquivo `.streamlit/secrets.toml` com as suas chaves:

SUPABASE_URL = "https://..."
SUPABASE_SERVICE_KEY = "..."
OPENWEATHER_API_KEY = "..."