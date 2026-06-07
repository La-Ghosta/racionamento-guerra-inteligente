"""Modelos de domínio do racionador de suprimentos."""

import datetime
from dataclasses import dataclass, field


@dataclass
class Suprimento:
    """Representa um item de suprimento com quantidade e consumo diário."""

    nome: str
    quantidade_atual: float
    consumo_diario_padrao: float
    unidade_medida: str
    categoria: str = "outro"
    validade: datetime.date | None = None

    def __post_init__(self) -> None:
        if self.quantidade_atual < 0:
            raise ValueError(f"Suprimento '{self.nome}': quantidade_atual não pode ser negativa.")
        if self.consumo_diario_padrao < 0:
            raise ValueError(
                f"Suprimento '{self.nome}': consumo_diario_padrao não pode ser negativo."
            )


@dataclass
class Pessoa:
    """Representa um membro do grupo com fator de consumo baseado na idade."""

    nome: str
    idade: int
    fator_consumo: float = field(default=0.0)

    def __post_init__(self) -> None:
        if self.fator_consumo == 0.0:
            if self.idade < 12:
                self.fator_consumo = 0.6
            elif self.idade > 65:
                self.fator_consumo = 0.8
            else:
                self.fator_consumo = 1.0
        elif not (0.0 < self.fator_consumo <= 5.0):
            raise ValueError(f"Pessoa '{self.nome}': fator_consumo deve estar entre 0 e 5.")


@dataclass
class Grupo:
    """Representa um grupo de pessoas com seus suprimentos."""

    nome_grupo: str
    pessoas: list[Pessoa] = field(default_factory=list)
    suprimentos: list[Suprimento] = field(default_factory=list)
    localizacao: str | None = None
    regiao: str = ""  # [F4] região para agrupar no painel do coordenador
    pedido_ajuda: bool = False  # [F4] grupo sinalizou que precisa de ajuda
