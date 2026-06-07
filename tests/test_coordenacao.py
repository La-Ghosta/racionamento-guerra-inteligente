"""Testes da logica pura de coordenacao entre grupos (sem mocks)."""

from racionador.coordenacao import visao_coordenador
from racionador.modelos import Grupo, Pessoa, Suprimento


def _suprimento(nome: str, quantidade: float) -> Suprimento:
    """Suprimento com consumo 1.0/dia: com 1 adulto, dias_restantes = quantidade."""
    return Suprimento(
        nome=nome, quantidade_atual=quantidade, consumo_diario_padrao=1.0, unidade_medida="un"
    )


def _grupo(
    nome: str,
    quantidades: list[float],
    regiao: str = "",
    pedido_ajuda: bool = False,
    localizacao: str | None = None,
) -> Grupo:
    """Grupo com 1 adulto (fator 1.0) e um suprimento por quantidade informada."""
    return Grupo(
        nome_grupo=nome,
        pessoas=[Pessoa(nome="Ana", idade=30)],
        suprimentos=[_suprimento(f"Item {i}", q) for i, q in enumerate(quantidades)],
        regiao=regiao,
        pedido_ajuda=pedido_ajuda,
        localizacao=localizacao,
    )


def test_status_geral_e_o_pior_entre_suprimentos():
    # 10.0 → OK; 0.5 → CRITICO; o pior (CRITICO) define o status do grupo.
    grupo = _grupo("Misto", quantidades=[10.0, 0.5])

    visao = visao_coordenador([grupo])

    resumo = visao.resumos[0]
    assert resumo.status == "CRITICO"
    assert resumo.suprimentos_criticos == ["Item 1"]


def test_resumo_captura_pedido_ajuda_localizacao_e_regiao():
    grupo = _grupo(
        "Equipe Alfa", quantidades=[10.0], regiao="Norte", pedido_ajuda=True, localizacao="Kyiv"
    )

    resumo = visao_coordenador([grupo]).resumos[0]

    assert resumo.nome_grupo == "Equipe Alfa"
    assert resumo.status == "OK"
    assert resumo.pedido_ajuda is True
    assert resumo.localizacao == "Kyiv"
    assert resumo.regiao == "Norte"
    assert resumo.total_pessoas == 1
    assert resumo.suprimentos_criticos == []


def test_grupo_sem_suprimentos_vira_sem_dados():
    sem_suprimentos = Grupo(
        nome_grupo="Recem-criado", pessoas=[Pessoa(nome="Ana", idade=30)], pedido_ajuda=True
    )
    sem_pessoas = Grupo(nome_grupo="Vazio", suprimentos=[_suprimento("Agua", 10.0)])

    visao = visao_coordenador([sem_suprimentos, sem_pessoas])

    assert all(r.status == "SEM_DADOS" for r in visao.resumos)
    assert all(r.suprimentos_criticos == [] for r in visao.resumos)
    # Pedido de ajuda continua visivel mesmo sem dados de suprimentos.
    assert visao.resumos[0].pedido_ajuda is True


def test_agrupamento_por_regiao_usa_valor_cru():
    grupos = [
        _grupo("Norte A", quantidades=[10.0], regiao="Norte"),
        _grupo("Norte B", quantidades=[0.5], regiao="Norte"),
        _grupo("Sul A", quantidades=[3.0], regiao="Sul"),
        _grupo("Sem regiao", quantidades=[10.0], regiao=""),
    ]

    visao = visao_coordenador(grupos)

    # Regiao crua como chave: "" forma o proprio bucket, sem rotulo inventado.
    assert list(visao.por_regiao.keys()) == ["", "Norte", "Sul"]
    assert [r.nome_grupo for r in visao.por_regiao[""]] == ["Sem regiao"]
    assert [r.nome_grupo for r in visao.por_regiao["Norte"]] == ["Norte B", "Norte A"]
    assert [r.nome_grupo for r in visao.por_regiao["Sul"]] == ["Sul A"]


def test_ordenacao_prioriza_criticos_e_pedidos_de_ajuda():
    grupos = [
        _grupo("Ok tranquilo", quantidades=[10.0]),
        _grupo("Alerta", quantidades=[3.0]),
        _grupo("Critico sem ajuda", quantidades=[0.5]),
        _grupo("Critico com ajuda", quantidades=[0.5], pedido_ajuda=True),
        _grupo("Ok pedindo ajuda", quantidades=[10.0], pedido_ajuda=True),
    ]

    visao = visao_coordenador(grupos)

    assert [r.nome_grupo for r in visao.resumos] == [
        "Critico com ajuda",
        "Critico sem ajuda",
        "Alerta",
        "Ok pedindo ajuda",
        "Ok tranquilo",
    ]


def test_lista_vazia_retorna_visao_vazia():
    visao = visao_coordenador([])

    assert visao.resumos == []
    assert visao.por_regiao == {}
