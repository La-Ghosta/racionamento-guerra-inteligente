> 🚀 **Aplicação publicada (Etapa 2):** https://racionador-supri.streamlit.app/
>
> **Issue da Etapa 2:** [#1](https://github.com/La-Ghosta/racionador-supri/issues/1)

# Racionador-Supri

[![CI](https://github.com/La-Ghosta/racionador-supri/actions/workflows/ci.yml/badge.svg)](https://github.com/La-Ghosta/racionador-supri/actions/workflows/ci.yml)
![Versao](https://img.shields.io/badge/versao-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Licenca](https://img.shields.io/badge/licenca-MIT-green)

Aplicação de linha de comando (CLI) feita em Python para ajudar famílias e grupos isolados em **zonas de conflito humanitário** a controlar seus suprimentos básicos (água, alimentos, medicamentos), calcular quantos dias eles ainda vão durar e receber sugestões inteligentes de corte no consumo quando algo está acabando.

---

## Sobre o projeto

Este projeto foi desenvolvido como atividade da disciplina e simula um pequeno ciclo profissional de desenvolvimento de software, incluindo versionamento semântico, declaração de dependências, testes automatizados, linting e integração contínua.

- **Autor:** Guilherme Holanda
- **Versão atual:** `1.1.0`
- **Repositório público:** https://github.com/La-Ghosta/racionador-supri
- **Licença:** MIT

---

## O problema real

Em situações de conflito armado e crises humanitárias - como a guerra em curso na Ucrânia - milhares de famílias ficam isoladas em regiões onde a chegada de ajuda é incerta, intermitente ou completamente bloqueada. Nesse contexto, **administrar os suprimentos disponíveis deixa de ser uma escolha e passa a ser uma questão de sobrevivência**.

Sem ferramentas adequadas, é fácil:

- subestimar o consumo diário do grupo;
- não perceber que um item essencial vai acabar antes da próxima oportunidade de reabastecimento;
- racionar de forma desigual entre adultos, crianças e idosos;
- perder a noção de quanto ainda existe de cada coisa.

## A proposta de solução

O **Racionador-Supri** é uma CLI simples que permite:

- cadastrar as pessoas do grupo (com fator de consumo automático por faixa etária);
- cadastrar os suprimentos disponíveis (água, alimentos, remédios, baterias, etc.);
- ver, a qualquer momento, **quantos dias cada item vai durar**;
- receber **alertas visuais coloridos** (verde / amarelo / vermelho) conforme o nível de criticidade;
- pedir uma **sugestão de corte percentual** no consumo para esticar um suprimento até uma data-alvo;
- atualizar quantidades quando chegar ajuda humanitária;
- remover pessoas ou suprimentos do grupo.

Tudo é salvo localmente em um arquivo `dados.json`, sem precisar de internet ou banco de dados. Ou seja, o Racionador-Supri foi pensado exatamente para esse cenário: uma ferramenta que funciona **sem internet, sem custo extra e sem depender de infraestrutura** que pode ser destruída.

---

## Público-alvo

- Famílias ou pequenos grupos isolados em zonas de crise humanitária.
- Cuidadores e voluntários que ajudam a organizar a logística de suprimentos para essas famílias.
- ONGs e iniciativas locais que precisam de uma ferramenta simples para acompanhar consumo em campo, sem depender de internet.

---

## Funcionalidades principais

- Cadastro de pessoas com cálculo automático do fator de consumo por idade (criança = 0.6, adulto = 1.0, idoso = 0.8).
- Cadastro de suprimentos com nome, quantidade, consumo diário por adulto e unidade de medida.
- Cálculo de quantos dias cada suprimento vai durar para o grupo.
- Relatório colorido com classificação OK / ALERTA / CRÍTICO.
- Sugestão automática de corte percentual no consumo.
- Atualização e remoção de itens.
- Persistência local em JSON, sem necessidade de internet.
- Mensagens de erro amigáveis (ex: nomes duplicados, valores negativos, grupo vazio).
- Definição opcional de localização do grupo (`set-localizacao`).
- Consulta de clima local via API pública OpenWeather, com enriquecimento automático do comando `status` quando há localização cadastrada.

---

## Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| Typer | Construção da interface CLI |
| Rich | Tabelas e cores no terminal |
| pytest | Testes automatizados |
| ruff | Linting e formatação de código |
| GitHub Actions | Pipeline de Integração Contínua (CI) |
| Streamlit | Interface web |
| Requests | Consumo de APIs HTTP |

---

## Instalação

### Pré-requisitos

- **Python 3.10 ou superior** instalado ([download oficial](https://www.python.org/downloads/))
- **Git** instalado

### Passo 1 - Clonar o repositório

```bash
git clone https://github.com/La-Ghosta/racionador-supri.git
cd racionador-supri
```

### Passo 2 - Criar e ativar um ambiente virtual

No Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Após ativar, você verá `(.venv)` no início da linha do terminal.

### Passo 3 - Instalar o projeto

```bash
pip install -e .
```

Isso instala o `racionador-supri` em modo editável, junto com suas dependências (`typer` e `rich`).

Se você também quiser rodar os testes e o linter, instale com:

```bash
pip install -e ".[dev]"
```

---

## Como usar

Depois de instalar, o comando `racionador` fica disponível no seu ambiente virtual. Aqui vai um exemplo completo de uso:

```bash
# 1. Criar um grupo
racionador init "Familia Kyiv"

# 2. Adicionar pessoas (idade define o fator de consumo automaticamente)
racionador add-pessoa "Olena" 34
racionador add-pessoa "Mykola" 8
racionador add-pessoa "Maria" 67

# 3. Adicionar suprimentos
#    formato: nome quantidade consumo_diario_por_adulto unidade
racionador add-suprimento "Agua" 20 2.0 L
racionador add-suprimento "Arroz" 5 0.3 kg
racionador add-suprimento "Medicamento" 10 1.0 un

# 4. Ver o status (tabela colorida)
racionador status

# 4.1. (Opcional) Definir a localização do grupo
racionador set-localizacao "Kyiv"

# 4.2. (Opcional) Consultar o clima de uma cidade
racionador clima "Kyiv"

# 5. Pedir uma sugestão de corte para a agua durar 10 dias
racionador sugerir Agua 10

# 6. Listar tudo
racionador listar

# 7. Atualizar um suprimento (ex: chegou mais arroz da ajuda humanitária)
racionador atualizar-suprimento "Arroz" 12

# 8. Remover algo
racionador remover-suprimento "Medicamento"
racionador remover-pessoa "Mykola"
```

Os dados são salvos em um arquivo `dados.json` na pasta atual. Se quiser começar do zero, basta apagar esse arquivo.

### Lista completa de comandos

| Comando | Descrição |
|---|---|
| `racionador init <nome>` | Cria um grupo novo |
| `racionador add-pessoa <nome> <idade>` | Adiciona uma pessoa ao grupo |
| `racionador add-suprimento <nome> <qtd> <consumo> <unidade>` | Adiciona um suprimento |
| `racionador atualizar-suprimento <nome> <nova_qtd>` | Atualiza a quantidade |
| `racionador remover-pessoa <nome>` | Remove uma pessoa |
| `racionador remover-suprimento <nome>` | Remove um suprimento |
| `racionador listar` | Lista pessoas e suprimentos |
| `racionador status` | Mostra o relatório colorido |
| `racionador sugerir <suprimento> <dias>` | Sugere corte de consumo |
| `racionador set-localizacao <cidade>` | Define a localização do grupo (usada pelo clima) |
| `racionador clima <cidade>` | Consulta o clima atual de uma cidade |

Para ver a ajuda de qualquer comando:

```bash
racionador --help
racionador status --help
```

---

## Versão web

Além da CLI, existe uma versão em interface web feita com Streamlit, que reusa a mesma lógica de domínio. Ela está publicada em:

🚀 **https://racionador-supri.streamlit.app/**

Para rodar a versão web localmente:

    streamlit run streamlit_app.py

A versão web mantém os dados na sessão do navegador e oferece download e upload do estado em JSON, sem dependência de banco de dados.

---

## Integração com clima (OpenWeather)

A versão 1.1.0 adiciona consulta opcional ao clima atual via API pública da OpenWeather. **A aplicação continua funcionando 100% offline** — esse é o caráter central do projeto, pensado para zonas de crise humanitária onde a conectividade é intermitente. Quando há internet, os comandos `clima` e `status` (com localização cadastrada) exibem dados climáticos da cidade. Quando não há, eles seguem respondendo normalmente sem o enriquecimento.

A integração é via variável de ambiente `OPENWEATHER_API_KEY` na CLI e via secret no painel do Streamlit Cloud na versão web.

---

## Como rodar os testes

Com as dependências de desenvolvimento instaladas (`pip install -e ".[dev]"`):

```bash
pytest
```

A suite tem **29 testes** cobrindo:

- caminho feliz dos cálculos de racionamento;
- entradas inválidas (quantidades negativas, grupo vazio, dias-alvo zero);
- casos limite (idade exatamente 12 e 65 anos, consumo zero);
- serialização e desserialização do JSON.

Para ver o resultado em modo detalhado:

```bash
pytest -v
```

---

## Como rodar o linter

Para verificar o estilo e a qualidade do código:

```bash
ruff check .
```

Para verificar a formatação:

```bash
ruff format --check .
```

Para corrigir automaticamente o que for possível:

```bash
ruff check . --fix
ruff format .
```

---

## Integração contínua (CI)

O projeto possui um workflow do GitHub Actions (`.github/workflows/ci.yml`) que roda automaticamente em todo `push` e `pull request` para a branch `main`. Ele executa:

1. Instalação do projeto e das dependências de desenvolvimento;
2. `ruff check .` (linter);
3. `ruff format --check .` (verificação de formatação);
4. `pytest` (suite de testes).

Os testes rodam em **três versões do Python**: 3.10, 3.11 e 3.12.

O status atual do build pode ser visto no badge no topo deste README.

---

## Estrutura do projeto

```
racionador-supri/
├── .github/
│   └── workflows/
│       └── ci.yml              # Pipeline de integração contínua
├── src/
│   └── racionador/
│       ├── __init__.py
│       ├── __main__.py         # Ponto de entrada (python -m racionador)
│       ├── modelos.py          # Dataclasses (Pessoa, Suprimento, Grupo)
│       ├── racionamento.py     # Lógica pura de cálculo
│       ├── persistencia.py     # Salvar e carregar JSON
│       ├── clima.py            # Integração com OpenWeather
│       └── cli.py              # Interface CLI com Typer + Rich
├── tests/
│   ├── __init__.py
│   ├── test_modelos.py
│   ├── test_racionamento.py
│   ├── test_persistencia.py
│   └── test_clima.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml              # Manifesto + versão + dependências
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## Versão e licença

- **Versão atual:** `1.1.0` (declarada no `pyproject.toml`)
- **Licença:** MIT - veja o arquivo [LICENSE](LICENSE)

---

## Autor

**Guilherme Holanda**

- GitHub: [@La-Ghosta](https://github.com/La-Ghosta)

---

## Observações finais

Este é um projeto **acadêmico**, desenvolvido como parte de uma atividade da faculdade. Seu objetivo é demonstrar o ciclo básico de desenvolvimento de software (estrutura, testes, lint, CI, versionamento) aplicado a um problema real e socialmente relevante.