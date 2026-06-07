"""Interface de linha de comando do racionador de suprimentos."""

import datetime
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from racionador.clima import obter_clima
from racionador.modelos import Grupo, Pessoa, Suprimento
from racionador.persistencia import carregar_grupo, salvar_grupo
from racionador.racionamento import relatorio_completo, sugerir_corte

app = typer.Typer(
    name="racionador",
    help="Racionamento de suprimentos em zonas de conflito humanitário.",
    no_args_is_help=True,
)
console = Console()

_ARQUIVO_DADOS = Path(os.environ.get("RACIONADOR_DADOS", "dados.json"))

_COR_STATUS = {
    "OK": "green",
    "ALERTA": "yellow",
    "CRITICO": "red",
}


def _carregar_ou_abortar() -> Grupo:
    """Carrega o grupo do arquivo de dados ou encerra com mensagem de erro."""
    grupo = carregar_grupo(_ARQUIVO_DADOS)
    if grupo is None:
        typer.echo(
            "Erro: nenhum grupo encontrado. Execute 'racionador init <nome>' primeiro.",
            err=True,
        )
        raise typer.Exit(1) from None
    return grupo


def _construir_tabela_clima(dados: dict) -> Table:
    """Constrói a tabela Rich de exibição do clima."""
    tabela = Table(title=f"Clima em {dados['cidade']}", show_lines=True)
    tabela.add_column("Cidade", style="bold")
    tabela.add_column("Temperatura", justify="right")
    tabela.add_column("Descrição")
    tabela.add_column("Umidade", justify="right")
    tabela.add_row(
        str(dados["cidade"]),
        f"{dados['temperatura_c']}°C",
        str(dados["descricao"]),
        f"{dados['umidade']}%",
    )
    return tabela


@app.command()
def init(
    nome_grupo: str = typer.Argument(..., help="Nome do grupo a ser criado."),
) -> None:
    """Cria um novo grupo e salva em dados.json."""
    if _ARQUIVO_DADOS.exists():
        confirmar = typer.confirm(f"Arquivo '{_ARQUIVO_DADOS}' já existe. Deseja sobrescrever?")
        if not confirmar:
            typer.echo("Operação cancelada.")
            raise typer.Exit(0)

    grupo = Grupo(nome_grupo=nome_grupo)
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    typer.echo(f"Grupo '{nome_grupo}' criado em '{_ARQUIVO_DADOS}'.")


@app.command(name="add-pessoa")
def add_pessoa(
    nome: str = typer.Argument(..., help="Nome da pessoa."),
    idade: int = typer.Argument(..., help="Idade da pessoa em anos."),
) -> None:
    """Adiciona uma pessoa ao grupo."""
    grupo = _carregar_ou_abortar()

    if any(p.nome.strip().lower() == nome.strip().lower() for p in grupo.pessoas):
        typer.echo(
            f"Erro: ja existe uma pessoa chamada '{nome}' no grupo. "
            f"Use 'remover-pessoa' antes de adicionar novamente.",
            err=True,
        )
        raise typer.Exit(1) from None

    try:
        pessoa = Pessoa(nome=nome, idade=idade)
    except ValueError as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1) from None

    grupo.pessoas.append(pessoa)
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    typer.echo(
        f"Pessoa '{nome}' (idade {idade}, fator {pessoa.fator_consumo:.1f}) "
        f"adicionada ao grupo '{grupo.nome_grupo}'."
    )


@app.command(name="add-suprimento")
def add_suprimento(
    nome: str = typer.Argument(..., help="Nome do suprimento."),
    quantidade: float = typer.Argument(..., help="Quantidade atual disponível."),
    consumo_diario: float = typer.Argument(..., help="Consumo diário padrão por adulto."),
    unidade: str = typer.Argument(..., help="Unidade de medida (ex: kg, L, un)."),
    categoria: str = typer.Option(
        "outro", "--categoria", help="Categoria do suprimento (ex: agua, comida, remedio)."
    ),
    validade: str | None = typer.Option(
        None, "--validade", help="Data de validade no formato AAAA-MM-DD."
    ),
) -> None:
    """Adiciona um suprimento ao grupo."""
    grupo = _carregar_ou_abortar()

    if any(s.nome.strip().lower() == nome.strip().lower() for s in grupo.suprimentos):
        typer.echo(
            f"Erro: ja existe um suprimento chamado '{nome}'. "
            f"Use 'atualizar-suprimento' para modificar a quantidade "
            f"ou 'remover-suprimento' para excluir.",
            err=True,
        )
        raise typer.Exit(1) from None

    data_validade: datetime.date | None = None
    if validade is not None:
        try:
            data_validade = datetime.date.fromisoformat(validade)
        except ValueError:
            typer.echo(
                f"Erro: validade '{validade}' inválida. Use o formato AAAA-MM-DD.",
                err=True,
            )
            raise typer.Exit(1) from None

    try:
        suprimento = Suprimento(
            nome=nome,
            quantidade_atual=quantidade,
            consumo_diario_padrao=consumo_diario,
            unidade_medida=unidade,
            categoria=categoria,
            validade=data_validade,
        )
    except ValueError as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1) from None

    grupo.suprimentos.append(suprimento)
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    typer.echo(
        f"Suprimento '{nome}' ({quantidade} {unidade}, consumo {consumo_diario} {unidade}/dia) "
        f"adicionado ao grupo '{grupo.nome_grupo}'."
    )


@app.command()
def status() -> None:
    """Exibe o relatório completo de suprimentos do grupo."""
    grupo = _carregar_ou_abortar()

    try:
        relatorio = relatorio_completo(grupo)
    except ValueError as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1) from None

    tabela = Table(
        title=f"Status do grupo: {grupo.nome_grupo}",
        show_lines=True,
    )
    tabela.add_column("Suprimento", style="bold")
    tabela.add_column("Quantidade", justify="right")
    tabela.add_column("Dias restantes", justify="right")
    tabela.add_column("Status", justify="center")
    tabela.add_column("Corte sugerido", justify="right")

    for nome_sup, dados in relatorio.items():
        cor = _COR_STATUS[dados["status"]]
        dias = dados["dias_restantes"]
        dias_str = str(dias) if dias != float("inf") else "∞"
        corte = dados["corte_sugerido_pct"]
        corte_str = f"{corte:.1f}%" if corte > 0 else "—"

        tabela.add_row(
            nome_sup,
            f"{dados['quantidade_atual']} {dados['unidade_medida']}",
            dias_str,
            f"[{cor}]{dados['status']}[/{cor}]",
            corte_str,
        )

    console.print(tabela)

    if grupo.localizacao:
        dados_clima = obter_clima(grupo.localizacao)
        if dados_clima is not None:
            console.print(_construir_tabela_clima(dados_clima))


@app.command()
def sugerir(
    nome_suprimento: str = typer.Argument(..., help="Nome do suprimento."),
    dias_alvo: int = typer.Argument(..., help="Número de dias desejados de duração."),
) -> None:
    """Mostra o percentual de corte necessário para o suprimento durar `dias_alvo` dias."""
    grupo = _carregar_ou_abortar()

    sup = next((s for s in grupo.suprimentos if s.nome == nome_suprimento), None)
    if sup is None:
        typer.echo(f"Erro: suprimento '{nome_suprimento}' não encontrado no grupo.", err=True)
        raise typer.Exit(1) from None

    try:
        corte = sugerir_corte(sup, grupo, dias_alvo)
    except ValueError as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1) from None

    if corte == 0.0:
        console.print(
            f"[green]O suprimento '{nome_suprimento}' já dura {dias_alvo} dias ou mais. "
            f"Nenhum corte necessário.[/green]"
        )
    else:
        console.print(
            f"Para '{nome_suprimento}' durar [bold]{dias_alvo} dias[/bold], "
            f"é necessário reduzir o consumo em [yellow bold]{corte:.1f}%[/yellow bold]."
        )


@app.command(name="atualizar-suprimento")
def atualizar_suprimento(
    nome: str = typer.Argument(..., help="Nome do suprimento a atualizar."),
    nova_quantidade: float = typer.Argument(..., help="Nova quantidade disponivel."),
) -> None:
    """Atualiza a quantidade atual de um suprimento existente."""
    grupo = _carregar_ou_abortar()

    if nova_quantidade < 0:
        typer.echo("Erro: a nova quantidade nao pode ser negativa.", err=True)
        raise typer.Exit(1) from None

    sup = next(
        (s for s in grupo.suprimentos if s.nome.strip().lower() == nome.strip().lower()),
        None,
    )
    if sup is None:
        typer.echo(f"Erro: suprimento '{nome}' nao encontrado no grupo.", err=True)
        raise typer.Exit(1) from None

    sup.quantidade_atual = nova_quantidade
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    typer.echo(
        f"Suprimento '{sup.nome}' atualizado: nova quantidade = {nova_quantidade} {sup.unidade_medida}"
    )


@app.command(name="remover-pessoa")
def remover_pessoa(
    nome: str = typer.Argument(..., help="Nome da pessoa a remover."),
) -> None:
    """Remove uma pessoa do grupo pelo nome."""
    grupo = _carregar_ou_abortar()

    pessoa = next(
        (p for p in grupo.pessoas if p.nome.strip().lower() == nome.strip().lower()),
        None,
    )
    if pessoa is None:
        typer.echo(f"Erro: pessoa '{nome}' nao encontrada no grupo.", err=True)
        raise typer.Exit(1) from None

    grupo.pessoas.remove(pessoa)
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    typer.echo(f"Pessoa '{pessoa.nome}' removida do grupo '{grupo.nome_grupo}'.")


@app.command(name="remover-suprimento")
def remover_suprimento(
    nome: str = typer.Argument(..., help="Nome do suprimento a remover."),
) -> None:
    """Remove um suprimento do grupo pelo nome."""
    grupo = _carregar_ou_abortar()

    sup = next(
        (s for s in grupo.suprimentos if s.nome.strip().lower() == nome.strip().lower()),
        None,
    )
    if sup is None:
        typer.echo(f"Erro: suprimento '{nome}' nao encontrado no grupo.", err=True)
        raise typer.Exit(1) from None

    grupo.suprimentos.remove(sup)
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    typer.echo(f"Suprimento '{sup.nome}' removido do grupo '{grupo.nome_grupo}'.")


@app.command(name="set-localizacao")
def set_localizacao(
    cidade: str = typer.Argument(..., help="Nome da cidade para associar ao grupo."),
) -> None:
    """Define a localização geográfica do grupo."""
    grupo = _carregar_ou_abortar()
    grupo.localizacao = cidade
    salvar_grupo(grupo, _ARQUIVO_DADOS)
    console.print(
        f"[green]Localização do grupo '{grupo.nome_grupo}' definida como '{cidade}'.[/green]"
    )


@app.command()
def clima(
    cidade: str = typer.Argument(..., help="Nome da cidade para consultar o clima."),
) -> None:
    """Consulta e exibe o clima atual de uma cidade."""
    dados = obter_clima(cidade)

    if dados is None:
        if not os.getenv("OPENWEATHER_API_KEY"):
            typer.echo(
                "Erro: API key não configurada. Defina OPENWEATHER_API_KEY para ativar o clima.",
                err=True,
            )
        else:
            typer.echo("Erro: Não foi possível obter o clima no momento.", err=True)
        raise typer.Exit(1) from None

    console.print(_construir_tabela_clima(dados))


@app.command()
def listar() -> None:
    """Lista as pessoas e suprimentos do grupo."""
    grupo = _carregar_ou_abortar()

    console.print(f"\n[bold]Grupo:[/bold] {grupo.nome_grupo}\n")

    tabela_pessoas = Table(title="Pessoas", show_lines=True)
    tabela_pessoas.add_column("Nome")
    tabela_pessoas.add_column("Idade", justify="right")
    tabela_pessoas.add_column("Fator de consumo", justify="right")

    for pessoa in grupo.pessoas:
        tabela_pessoas.add_row(
            pessoa.nome,
            str(pessoa.idade),
            f"{pessoa.fator_consumo:.2f}",
        )

    if grupo.pessoas:
        console.print(tabela_pessoas)
    else:
        console.print("[dim]Nenhuma pessoa cadastrada.[/dim]")

    tabela_sup = Table(title="Suprimentos", show_lines=True)
    tabela_sup.add_column("Nome")
    tabela_sup.add_column("Quantidade atual", justify="right")
    tabela_sup.add_column("Consumo/dia (adulto)", justify="right")
    tabela_sup.add_column("Unidade")
    tabela_sup.add_column("Categoria")
    tabela_sup.add_column("Validade", justify="right")

    for sup in grupo.suprimentos:
        tabela_sup.add_row(
            sup.nome,
            str(sup.quantidade_atual),
            str(sup.consumo_diario_padrao),
            sup.unidade_medida,
            sup.categoria,
            sup.validade.isoformat() if sup.validade else "—",
        )

    if grupo.suprimentos:
        console.print(tabela_sup)
    else:
        console.print("[dim]Nenhum suprimento cadastrado.[/dim]")
