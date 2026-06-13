# Racionamento em Guerra Inteligente

[![CI](https://github.com/La-Ghosta/racionamento-guerra-inteligente/actions/workflows/ci.yml/badge.svg)](https://github.com/La-Ghosta/racionamento-guerra-inteligente/actions/workflows/ci.yml) ![Versao](https://img.shields.io/badge/versao-2.0.0-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Licenca](https://img.shields.io/badge/licenca-MIT-green)

Ferramenta para **famílias e grupos isolados em zonas de conflito humanitário** controlarem seus suprimentos essenciais — água, comida e remédios —, preverem por quantos dias cada item ainda dura e receberem sugestões de corte no consumo. Feita para continuar útil mesmo com pouca ou nenhuma conexão.

## Por que este projeto

Escolhemos um tema de **impacto real**: em situações de guerra e crises humanitárias, grupos isolados precisam fazer recursos escassos durarem o máximo possível, muitas vezes sem energia estável e sem internet confiável. A proposta é uma ferramenta simples que ajude essas pessoas a enxergarem quanto tempo cada suprimento ainda dura, a anteciparem a escassez e a coordenarem ajuda entre grupos vizinhos.

O projeto **ainda não está completo**. A lacuna mais importante hoje é de **segurança**: faltam **autenticação e autorização**, para que cada grupo acesse e altere apenas os próprios dados, com diferentes níveis de permissão. Essa é a evolução natural prevista para uma próxima etapa.

## App ao vivo

Roda direto no navegador, sem instalar nada.

**Copie e cole a URL na barra de endereços do navegador:**

```
https://racionamento-guerra-inteligente.streamlit.app/
```

## O que dá para fazer

- **Controlar o estoque** de cada grupo: pessoas, suprimentos e consumo.
- **Prever a autonomia** de cada item (quantos dias dura no ritmo atual), do status `OK` ao `CRÍTICO`.
- **Receber sugestões de racionamento** para esticar os recursos.
- **Alertas de validade**: itens vencidos ou perto de vencer aparecem em destaque na aba Status.
- **Deletar um grupo** direto pela interface, com a remoção refletida no banco (e nos dados ligados a ele).
- **Histórico de aquisições**: cada mudança de quantidade é registrada, e uma aba mostra a evolução em gráfico e em log.
- **Visão de coordenador** sobre vários grupos ao mesmo tempo, agrupados por região: quem está crítico, quem pediu ajuda (`SOS`) e um mapa ao vivo.
- **Clicar num grupo** na visão do coordenador e cair direto no status detalhado dele.

A interface é um **terminal CRT** — estética de log de operações, monocromática e de leitura rápida, pensada para registro em campo.

---

## 🕹 Guia rápido do app (passo a passo)

Abriu o app? É só seguir as abas, da esquerda para a direita. Não precisa instalar nem configurar nada para testar.

**1. Início — crie um grupo.** Dê um nome, informe a **cidade** e escolha a **região** (Norte, Sul, Leste, Oeste...). Esta aba também é o painel do grupo: mostra um resumo dos dados dele. Aqui fica o botão de **SOS** — ele é pensado para um grupo em estado **crítico** sinalizar que precisa de ajuda (a ideia é que, no futuro, um grupo sem suprimentos acione esse pedido para os demais). Marque o SOS apenas quando o grupo estiver crítico.

**2. Pessoas — quem faz parte do grupo.** Adicione as pessoas (nome e idade). A idade importa: crianças e idosos consomem proporcionalmente mais, então isso afeta o cálculo de quanto tempo os suprimentos duram.

**3. Suprimentos — o estoque.** Cadastre cada item com a **quantidade atual**, o **consumo por dia**, a **unidade** (L, kg, comp...) e, opcionalmente, a **data de validade**.

**4. Status — a saúde do grupo.** Mostra, item por item, o **estoque atual** e por **quantos dias** ele ainda dura no ritmo de consumo, além dos **alertas de validade**. As cores indicam a gravidade:
- 🟢 **OK** — autonomia confortável.
- 🟡 **ALERTA** — o item está acabando (poucos dias de folga) ou perto de vencer.
- 🔴 **CRÍTICO** — vai faltar muito em breve; itens vencidos também aparecem em destaque.

**5. Sugestões — como esticar os recursos.** Com base no estoque e no consumo, o app sugere **cortes de ração** para fazer os suprimentos durarem mais.

**6. Coordenação — a visão geral de todos os grupos.** Lista os grupos com uma **cor correspondente ao estado** (🔴 crítico, 🟡 alerta, 🟢 normal) e destaca quem pediu **SOS**, com um **mapa** das cidades. Clicar num grupo leva direto ao Status detalhado dele. É a tela que transforma vários controles individuais em uma operação coordenada.

**7. Histórico — a evolução no tempo.** Cada vez que um suprimento é adicionado ou tem a quantidade alterada, fica registrado. Esta aba mostra um **gráfico** da quantidade ao longo do tempo, por suprimento, e um **log** das movimentações.

> ** Este ambiente já vem com **6 grupos de exemplo** (em cidades da Ucrânia) cobrindo os três estados — 2 críticos com SOS, 3 em alerta e 1 normal — para visualizar rapidamente a aba de Coordenação. Sinta-se à vontade para criar os seus próprios grupos e testar o fluxo completo.

---

## Como o trabalho em equipe foi conduzido 

### Briefing

A equipe partiu de uma decisão inicial: em vez de começar um projeto do zero, **adotar um projeto de racionamento já existente do integrante La-Ghosta**, desenvolvido nas etapas anteriores do Bootcamp, e usá-lo como base para aperfeiçoar e ampliar, indo além do mínimo exigido pela etapa. O briefing alinhou o objetivo (uma ferramenta de racionamento útil em cenários reais de guerra).

### Ideação

Levantamos várias ideias de funcionalidades. As mais discutidas foram:

- Autenticação e autorização
- Interface melhorada
- Deletar grupo pela aba Início
- Histórico de suprimentos
- Alertas de validade na aba Status
- Coordenação entre grupos
- Notificações de status crítico (alerta por SMS/rádio para grupos sem internet)
- Exportação de relatório de estoque (CSV/PDF para registro em campo)
- Modo multilíngue (para uso por equipes humanitárias internacionais)

### O que priorizamos e por quê

Diante do prazo da entrega e do risco de cada mudança, optamos pelo conjunto que entregava **mais valor visível com menor risco de quebrar a base**:

- **Interface melhorada** — uma boa experiência de uso é o que torna a ferramenta de fato utilizável em campo; a estética de terminal CRT dá leitura rápida e foco no essencial.
- **Coordenação entre grupos** — eleva o app de "controle individual" para "operação coletiva": ver quem está crítico e quem pediu ajuda, com mapa, é o que mais aproxima a ferramenta de um cenário humanitário real.
- **Histórico de suprimentos** — dá rastreabilidade temporal (como o estoque evoluiu), essencial para entender consumo e planejar reposição; foi também a funcionalidade que mais exercitou a escrita no banco de dados.
- **Alertas de validade** — evita o desperdício de recursos escassos por vencimento, reaproveitando a informação de validade que o sistema já guardava.
- **Deletar grupo** — fecha o ciclo básico de gerenciamento (criar, ler, atualizar e **apagar**), operação que faltava na interface.

**Autenticação** foi reconhecida como importante, mas **adiada de propósito**: é a funcionalidade mais complexa e sensível, e tentá-la na reta final colocaria em risco a estabilidade do que já funcionava. Ficou registrada como o próximo passo do projeto em um futuro. 

### Banco de dados na nuvem

A adição de um **banco de dados PostgreSQL na nuvem (Supabase)** foi um ganho central da etapa: aumentou muito a **confiabilidade dos dados**, que deixaram de viver apenas na memória/arquivos locais e passaram a ser persistidos de forma consistente, permitindo a visão de coordenação entre grupos e o histórico de aquisições. Mesmo assim, o núcleo continua **offline-first** e degrada de forma graciosa quando a nuvem não está disponível.

Como parte da qualidade, também reescrevemos o carregamento de todos os grupos para usar **3 queries fixas no lugar de 1 + 3N** (uma consulta por grupo, que crescia com a quantidade de grupos). A decisão foi tomada para **eliminar o problema de N+1 e manter a tela de coordenação rápida** à medida que o número de grupos aumenta, sem alterar o comportamento — apenas a eficiência.

### Resumo das contribuições (Pull Requests)

| Integrante                   | Pull Request                                          | Contribuição                                                 |
| ---------------------------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| Luan (luluzin2025)           | feat: deletar grupo pela aba Início                   | Exclusão de grupo pela interface, refletida no banco.        |
| Carlos (CarlosEduardoBorges) | feat: alertas de validade na aba Status               | Classificação de validade e exibição dos itens vencidos/vencendo. |
| Murilo (YukiSukiyama)        | feat: histórico de aquisições de suprimentos          | Tabela `historico`, persistência e aba com gráfico e log.    |
| Guilherme (La-Ghosta)        | Integração Supabase, coordenação, performance, schema | Base do projeto e infraestrutura das etapas anteriores e da Etapa 3. |

---

## Stack

Python · Typer + Rich (CLI) · Streamlit (web) · Supabase / PostgreSQL · OpenWeather (clima e geocoding) · pytest + ruff · GitHub Actions (CI em 3.10 / 3.11 / 3.12) · Streamlit Community Cloud (deploy).

## Como funciona por dentro

- **Offline-first**: o núcleo funciona sem internet, com dados locais. A visão de coordenador e o mapa usam a nuvem e degradam de forma graciosa quando ela não está disponível.
- **Nuvem** via Supabase (PostgreSQL) para a persistência e a visão multi-grupo; **mapa** com geolocalização das cidades dos grupos.
- **Lógica separada da interface**: as regras (autonomia, alertas, validade, coordenação, histórico) ficam em módulos puros e testáveis em `src/racionador/`, separados do Streamlit.

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

O app abre no navegador. Sem configuração extra ele roda em **modo offline** (o núcleo funciona sem nuvem). Para habilitar a persistência na nuvem, a visão de coordenador e o mapa, configure as chaves abaixo.

### Banco de dados (Supabase) e chaves de API

A persistência na nuvem, a visão de coordenador e o mapa usam um banco PostgreSQL no Supabase (opcional — sem ele o app funciona offline):

1. Crie um projeto gratuito no [Supabase](https://supabase.com/).
2. No **SQL Editor**, rode os arquivos de `db/migrations/` em ordem:
   - `0000_init.sql` — cria as tabelas `grupos`, `pessoas` e `suprimentos`.
   - `0001_grupos_regiao_pedido_ajuda.sql` — adiciona `regiao` e `pedido_ajuda` à tabela `grupos`.
   - `0002_historico.sql` — cria a tabela `historico` (snapshots de quantidade por suprimento).
3. Em **Settings → API**, copie a `URL` e a `service_role key`.
4. A chave do clima/geolocalização vem do [OpenWeather](https://openweathermap.org/api): crie uma conta e gere uma `API key` gratuita.

**Onde guardar as 3 chaves:** crie o arquivo `.streamlit/secrets.toml` (já está no `.gitignore`, então **nunca** é enviado ao GitHub) com:

```toml
SUPABASE_URL = "https://...supabase.co"
SUPABASE_SERVICE_KEY = "sua-service-role-key"
OPENWEATHER_API_KEY = "sua-api-key-do-openweather"
```

No deploy (Streamlit Community Cloud), as mesmas três chaves são configuradas em **Settings → Secrets** do app, no mesmo formato acima.

### Estrutura do banco de dados (Supabase)

O schema é normalizado em três tabelas relacionadas, mais a tabela de histórico. As tabelas `pessoas`, `suprimentos` e `historico` referenciam `grupos` com **`ON DELETE CASCADE`** — ao apagar um grupo, tudo que está ligado a ele é removido junto.

**`grupos`**

| Coluna         | Tipo        | Observação                   |
| -------------- | ----------- | ---------------------------- |
| `id`           | bigint      | chave primária (identity)    |
| `nome`         | text        | obrigatório, único           |
| `localizacao`  | text        | opcional                     |
| `criado_em`    | timestamptz | default `now()`              |
| `regiao`       | text        | obrigatório, default `''`    |
| `pedido_ajuda` | boolean     | obrigatório, default `false` |

**`pessoas`**

| Coluna     | Tipo    | Observação                            |
| ---------- | ------- | ------------------------------------- |
| `id`       | bigint  | chave primária (identity)             |
| `grupo_id` | bigint  | FK → `grupos.id`, `on delete cascade` |
| `nome`     | text    | obrigatório                           |
| `idade`    | integer | obrigatório                           |

**`suprimentos`**

| Coluna                  | Tipo    | Observação                            |
| ----------------------- | ------- | ------------------------------------- |
| `id`                    | bigint  | chave primária (identity)             |
| `grupo_id`              | bigint  | FK → `grupos.id`, `on delete cascade` |
| `nome`                  | text    | obrigatório                           |
| `quantidade_atual`      | numeric | obrigatório                           |
| `consumo_diario_padrao` | numeric | obrigatório                           |
| `unidade_medida`        | text    | obrigatório                           |
| `categoria`             | text    | obrigatório, default `'outro'`        |
| `validade`              | date    | opcional                              |

**`historico`**

| Coluna       | Tipo        | Observação                                                   |
| ------------ | ----------- | ------------------------------------------------------------ |
| `id`         | bigint      | chave primária (identity)                                    |
| `grupo_id`   | bigint      | FK → `grupos.id`, `on delete cascade`                        |
| `suprimento` | text        | obrigatório                                                  |
| `quantidade` | numeric     | obrigatório (snapshot da quantidade)                         |
| `tipo`       | text        | obrigatório, default `'atualizacao'` (`'adicao'` ou `'atualizacao'`) |
| `criado_em`  | timestamptz | default `now()`                                              |

Índice em `historico (grupo_id, criado_em)` para leitura rápida e ordenada por grupo.

## Testes e qualidade

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
```

A suíte cobre a lógica de racionamento, validade, coordenação, mapa, clima e a persistência (com mocks, sem banco real). O GitHub Actions roda essa esteira em Python 3.10, 3.11 e 3.12 a cada push e Pull Request, exigindo aprovação antes do merge.